import json
import logging
import sys
from datetime import datetime, timezone

from app.request_context import request_id_var

# Attributes present on every LogRecord; anything else came from `extra=` and
# is emitted as a structured field. `color_message` is uvicorn's ANSI-coloured
# duplicate of `msg`, which is just noise in JSON.
_STANDARD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "color_message",
}


class JsonFormatter(logging.Formatter):
    """Formats each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        request_id = request_id_var.get()
        if request_id:
            entry["request_id"] = request_id

        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                entry[key] = value

        if record.exc_info:
            entry["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str)


def configure_logging(level: str) -> None:
    """Route all logs (ours and uvicorn's) through one JSON handler on stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Uvicorn installs its own handlers; send its logs through ours instead.
    for name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True

    # Our request middleware logs every request, so uvicorn's access log is redundant.
    logging.getLogger("uvicorn.access").disabled = True
