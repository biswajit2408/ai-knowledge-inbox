# AI Knowledge Inbox

A small web app to save notes and links, and then ask questions about them.
Answers are generated only from the saved content (RAG), and every answer shows its sources.

## Features

- Save a plain-text note or a URL (the page text is fetched on the server)
- See the list of saved items
- Ask a question and get an answer with numbered citations like `[1]`
- See the source snippets used for the answer

## Tech stack

- **Backend:** Python, FastAPI, SQLite, NumPy
- **Frontend:** React (hooks), Vite, Tailwind CSS, shadcn/ui
- **AI:** Google Gemini (embeddings + answers)

## Setup

You need Python 3.12+, Node 20+ and a Gemini API key (https://aistudio.google.com/apikey).

**1. Backend**

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Open `server/.env`, set `GEMINI_API_KEY`, then run:

```powershell
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

**2. Frontend** (in a second terminal)

```powershell
cd client
npm install
npm run dev
```

Open http://localhost:5173. The dev server forwards `/api/*` requests to the backend, so no CORS
setup is needed.

**Optional settings** (`server/.env`)

| Variable | Default |
|---|---|
| `CHAT_MODEL` | `gemini-3.5-flash-lite` |
| `EMBEDDING_MODEL` | `gemini-embedding-001` |
| `EMBEDDING_DIMENSIONS` | `768` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `150` (characters) |
| `DATABASE_PATH` | `data/inbox.db` |
| `LOG_LEVEL` | `INFO` |

To start with an empty database, stop the server and delete the `server/data/` folder.

> **Windows note:** some antivirus tools (e.g. Kaspersky) and company proxies intercept HTTPS, and
> Python then fails with `CERTIFICATE_VERIFY_FAILED`. The server uses `truststore` to trust the
> Windows certificate store. For pip, use `pip install --use-feature=truststore -r requirements.txt`.

## API

### POST /ingest

Save a note:

```json
{ "source_type": "note", "content": "Leg day is Monday and Thursday.", "title": "Gym" }
```

Save a URL:

```json
{ "source_type": "url", "url": "https://en.wikipedia.org/wiki/Retrieval-augmented_generation" }
```

`title` is optional. If it's missing, a note uses its first line and a URL uses the page title.

Response `201 Created`:

```json
{
  "id": "0f55da3eab46462bad325da46ed9be7d",
  "source_type": "note",
  "title": "Gym",
  "url": null,
  "content_preview": "Leg day is Monday and Thursday.",
  "content_length": 31,
  "chunk_count": 1,
  "created_at": "2026-10-20T09:33:17.292196Z"
}
```

### GET /items

Response `200 OK`, newest first:

```json
{ "items": [ { "id": "...", "title": "Gym", "chunk_count": 1, "...": "..." } ], "count": 1 }
```

Only a short preview of the content is returned, because a web page can be very long.

### POST /query

```json
{ "question": "Which days are leg day?", "top_k": 5 }
```

`top_k` is optional (default 5, max 20).

Response `200 OK`:

```json
{
  "answer": "Leg day is Monday and Thursday [1].",
  "sources": [
    {
      "number": 1,
      "cited": true,
      "item_id": "...",
      "title": "Gym",
      "url": null,
      "source_type": "note",
      "chunk_index": 0,
      "snippet": "Leg day is Monday and Thursday.",
      "score": 0.6851
    }
  ]
}
```

- `number` matches the `[1]`, `[2]` markers in the answer.
- `cited` tells whether the answer actually used that source.
- If the saved content doesn't contain the answer, the answer says so instead of guessing.

### GET /health

Returns `{"status": "ok"}`.

### Errors

All errors look like `{"detail": "message"}`.

| Status | When |
|---|---|
| `400` | URL points to localhost or a private network address |
| `422` | Invalid input, unknown host, unsupported page type (image, PDF), page over 5 MB, or no text on the page |
| `502` | The website or the Gemini API returned an error |
| `503` | Gemini rate limit reached, try again later |
| `504` | The website or the Gemini API timed out |
| `500` | Unexpected error (includes a `request_id` to find it in the logs) |

## How it works

**Saving an item**

1. For a URL, the page is downloaded (10s timeout, max 5 MB) and the main text is extracted.
   Menus, scripts, footers etc. are removed.
2. The text is split into chunks.
3. Each chunk is turned into an embedding (a vector) with Gemini.
4. The item and its chunks are saved to SQLite together, in one transaction.

Embeddings are created before saving, so if Gemini fails nothing is stored.

**Asking a question**

1. The question is turned into an embedding.
2. It is compared with every saved chunk (cosine similarity), and the 5 best chunks are picked.
3. The chunks and the question are sent to the LLM, which is told to answer only from those
   chunks and to cite them as `[n]`.
4. The answer and the sources are returned.

## Tradeoffs

### Chunking approach

- Text is split by paragraphs first, and small paragraphs are joined until a chunk is about
  **1000 characters** (around 200-250 tokens).
- A paragraph that is too long is split by sentences, then by words, so no text is lost.
- Each chunk repeats the last **150 characters** of the previous one (overlap), so a sentence on the
  border between two chunks is not cut in half.

Why: 1000 characters is big enough to hold a full idea, and small enough that one chunk is about one
topic. Characters are used instead of tokens to keep it simple (no tokenizer needed).
Smarter options like semantic chunking need extra API calls per document and were not worth it here.

### Vector store choice

Embeddings are stored in the **same SQLite database** as the items, and search is done with
**NumPy** (one matrix multiplication over all chunks).

Why:
- For one user this is fast enough (under 0.1 ms for ~40 chunks).
- It is exact search, so results are accurate.
- Items and their vectors are always in sync, because they are saved in one transaction.
- No extra service to install or run.

A vector database (Chroma, Qdrant, pgvector) would only be needed at a much bigger size.

### What breaks at scale

- **Search speed and memory:** every question loads and scans all vectors. This is fine for thousands
  of chunks, but at ~100k chunks it means ~300 MB of data per question.
- **Slow saving:** fetching a page and creating embeddings happens inside the request, so big pages
  take a few seconds, and saving fails if Gemini is down.
- **SQLite:** only one write at a time.
- **API limits:** many requests at once will hit Gemini rate limits.
- **Changing the embedding model:** all items would need to be embedded again.
- **No users:** there is no login, everyone shares one inbox.
- **Search quality:** vector search can miss exact words (names, codes), and there is no re-ranking.

### What would change for production

1. Save items in the background: return `202` right away with a status (`pending`, `ready`,
   `failed`), and let a worker do the fetching and embedding with retries.
2. Use Postgres with pgvector (with an index) instead of SQLite + NumPy.
3. Combine keyword search with vector search, and add a re-ranking step.
4. Add login and keep each user's data separate.
5. Check every redirect for private addresses (right now only the first URL is checked), skip
   duplicate pages, and support PDFs.
6. Add automated tests and a small set of test questions to measure answer quality.
7. Stream answers, add caching, metrics and tracing.

## Other decisions

**Gemini instead of OpenAI.** The assignment allows OpenAI or a similar API. Gemini was used because
the Gemini account had API credits available, while the OpenAI account had no quota left. Gemini
also gives both embeddings and answers with one API key. All Gemini code is in
`services/gemini.py`, `services/embeddings.py` and `services/answering.py` (plus the settings in
`config.py`), so switching to OpenAI only means changing those files.

**Cheap model for answers.** The goal was the cheapest model that is still good enough. In RAG, the
search step already finds the right text, so the model mostly has to summarize a few short passages.
`gemini-3.5-flash-lite` gave answers as good as the bigger `gemini-3.8-flash` on the same test
questions, while being cheaper and faster (about 1-2s instead of 3-8s). The model can be changed with
`CHAT_MODEL`.

**Smaller embeddings.** Embeddings use 768 dimensions instead of the full 3072. They take 4x less
space and the quality difference is small.

**Max 3 chunks per item.** Without this, one long page can fill all 5 result slots and hide other
items. For example, a question about both a gym note and a Wikipedia page returned only Wikipedia
chunks. Limiting each item to 3 chunks fixed this.

**Safety.**
- Saved pages are treated as data. The model is told not to follow instructions written inside
  them. A note saying "Ignore all previous instructions..." was tested and the model did not follow it.
- URLs pointing to localhost or private networks are blocked.
- Footnote markers like `[5]` from Wikipedia are removed, because they look like the citation format.

## Debuggability

- **Structured logs:** every log line is JSON and includes a request ID. Saving, searching and
  answering log their timings, sizes and token usage. Example:

  ```json
  {"ts": "2026-10-20T09:37:45.309+00:00", "level": "INFO", "logger": "app.services.answering", "msg": "answer generated", "request_id": "6d43...", "model": "gemini-3.5-flash-lite", "sources": 5, "cited": [1], "prompt_tokens": 1336, "output_tokens": 25, "duration_ms": 1047.9}
  ```

- **Request ID:** every response has an `X-Request-ID` header. The UI shows it when something fails,
  so the matching log lines are easy to find.
- **Clear errors:** each error type maps to a proper status code (see the Errors table). Detailed
  errors from Gemini go to the logs, and the user gets a short, readable message.

## Project structure

```
server/app/
  main.py            app setup
  config.py          settings from .env
  logging_config.py  JSON logging
  middleware.py      request ID and request logs
  errors.py          error types and status codes
  timing.py          timing helper for logs
  api/               routes: ingest, items, query
  schemas/           request and response models
  services/          URL fetching, chunking, embeddings, search, answers
  db/                SQLite tables and queries

client/src/
  api/client.js      calls to the backend
  hooks/             useItems, useAsk
  components/        form, item list, ask panel, answer and sources
  components/ui/     shadcn/ui components
  lib/               small helpers
```

Each layer has one job: routes only handle HTTP, services hold the logic, and `db/` holds the SQL.

## Assignment checklist

- [x] Add text notes and URLs (fetched server-side), stored with timestamp and source type
- [x] Chunking, embeddings, vector storage
- [x] Retrieve top chunks, send them with the question to the LLM, return the answer with cited sources
- [x] `POST /ingest`, `GET /items`, `POST /query` with input validation and proper status codes
- [x] React UI: add note/URL, list items, ask questions, show answer and source snippets
- [x] Structured logging, clear error messages, sensible status codes
- [x] Tradeoffs: chunking, vector store, what breaks at scale, production changes
- [x] No auth, no extra infrastructure
