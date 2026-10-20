import asyncio
import ipaddress
import logging
import re
import socket
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.errors import BadRequestError, UnprocessableContentError, UpstreamError, UpstreamTimeoutError

logger = logging.getLogger(__name__)

FETCH_TIMEOUT_SECONDS = 10.0
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
MAX_TEXT_LENGTH = 100_000
USER_AGENT = "AIKnowledgeInbox/0.1 (+https://github.com/biswajit2408/ai-knowledge-inbox)"

HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")
TEXT_CONTENT_TYPES = ("text/plain", "text/markdown")

# Page furniture that is never the main content.
NON_CONTENT_TAGS = ["script", "style", "noscript", "template", "svg", "iframe", "nav", "header", "footer", "aside", "form"]


@dataclass(frozen=True)
class FetchedPage:
    title: str | None
    text: str


async def fetch_page(url: str) -> FetchedPage:
    """Download a web page and return its readable text.

    Raises an AppError subclass with a client-safe message on any failure.
    """
    host = urlparse(url).hostname or ""
    await _ensure_public_host(host)

    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(
            timeout=FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
                if content_type not in HTML_CONTENT_TYPES + TEXT_CONTENT_TYPES:
                    raise UnprocessableContentError(
                        f"Unsupported content type '{content_type or 'unknown'}'; only HTML and plain-text pages can be saved."
                    )
                body = await _read_limited(response)
                encoding = response.encoding or "utf-8"
    except httpx.TimeoutException as exc:
        raise UpstreamTimeoutError(f"Timed out after {FETCH_TIMEOUT_SECONDS:.0f}s fetching {host}.") from exc
    except httpx.HTTPStatusError as exc:
        raise UpstreamError(f"{host} responded with HTTP {exc.response.status_code}.") from exc
    except httpx.RequestError as exc:
        raise UpstreamError(f"Could not connect to {host} ({type(exc).__name__}).") from exc

    if content_type in HTML_CONTENT_TYPES:
        title, text = _extract_from_html(body)
    else:
        title, text = None, _normalize_whitespace(body.decode(encoding, errors="replace"))

    if not text:
        raise UnprocessableContentError("No readable text was found at that URL.")

    logger.info(
        "page fetched",
        extra={
            "host": host,
            "content_type": content_type,
            "bytes": len(body),
            "text_length": len(text),
            "truncated": len(text) > MAX_TEXT_LENGTH,
            "duration_ms": round((time.perf_counter() - start) * 1000, 2),
        },
    )
    return FetchedPage(title=title, text=text[:MAX_TEXT_LENGTH])


async def _ensure_public_host(host: str) -> None:
    """Refuse URLs that resolve to private/loopback addresses (basic SSRF protection),
    so the server can't be used to probe its own network."""
    try:
        addresses = await asyncio.get_running_loop().getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise UnprocessableContentError(f"Could not resolve host '{host}'.") from exc

    for *_, sockaddr in addresses:
        ip = ipaddress.ip_address(str(sockaddr[0]).split("%")[0])
        if not ip.is_global:
            raise BadRequestError("URLs that point to private or local network addresses are not allowed.")


async def _read_limited(response: httpx.Response) -> bytes:
    """Read the body, but stop early if it exceeds MAX_RESPONSE_BYTES."""
    chunks: list[bytes] = []
    size = 0
    async for chunk in response.aiter_bytes():
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            raise UnprocessableContentError(f"Page is larger than {MAX_RESPONSE_BYTES // (1024 * 1024)} MB.")
        chunks.append(chunk)
    return b"".join(chunks)


def _extract_from_html(html: bytes) -> tuple[str | None, str]:
    """Return (title, main text). Prefers <main>/<article> over the whole <body>."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None

    for tag in soup(NON_CONTENT_TAGS):
        tag.decompose()

    root = soup.find("main") or soup.find("article") or soup.body or soup
    return title or None, _normalize_whitespace(root.get_text(separator="\n"))


def _normalize_whitespace(text: str) -> str:
    """Collapse runs of spaces inside lines and drop blank lines."""
    lines = (re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)
