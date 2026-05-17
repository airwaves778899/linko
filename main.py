"""
Linko — Open-source LINE AI customer service bot (MVP entry point).

Receives LINE webhook events, calls the configured LLM via LiteLLM,
and replies back to the user.

Usage:
    cp .env.example .env                # fill in your keys
    cp config.yaml.example config.yaml  # tweak persona / model
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Deque, Dict

import litellm
import yaml
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("linko")


def _load_config() -> Dict[str, Any]:
    """Load config.yaml; fall back to config.yaml.example on first run."""
    primary = Path(os.getenv("LINKO_CONFIG", "config.yaml"))
    if primary.exists():
        path = primary
    else:
        example = Path("config.yaml.example")
        if example.exists():
            log.warning(
                "%s not found — falling back to %s. "
                "Copy the example file to customise your bot.",
                primary,
                example,
            )
            path = example
        else:
            raise SystemExit(
                "Neither config.yaml nor config.yaml.example found in CWD."
            )
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


CONFIG = _load_config()

BOT_NAME: str = CONFIG.get("bot", {}).get("name", "Linko")
PERSONA: str = CONFIG.get("bot", {}).get(
    "persona", f"你是 {BOT_NAME}，一個親切的客服助理。請用繁體中文回覆。"
)


def _load_knowledge_base() -> str:
    """Load knowledge base files into a single text blob.

    Reads every file under ``config.knowledge_base.path`` that matches one of
    the configured extensions and concatenates them. Returns an empty string
    when the knowledge base is disabled, the folder is missing, or no files
    are found.

    Enforces ``max_chars`` to avoid blowing up the LLM context window /
    per-message cost if a user drops in a huge file by accident.
    """
    kb_config = CONFIG.get("knowledge_base", {}) or {}
    if not kb_config.get("enabled", False):
        return ""

    path = Path(kb_config.get("path", "knowledge_base"))
    extensions = {ext.lower() for ext in kb_config.get("extensions", [".txt", ".md"])}
    max_chars = int(kb_config.get("max_chars", 10000))

    if not path.is_dir():
        log.warning("Knowledge base path '%s' does not exist — skipping.", path)
        return ""

    chunks: list[str] = []
    total = 0
    for file in sorted(path.iterdir()):
        if not file.is_file() or file.suffix.lower() not in extensions:
            continue
        try:
            content = file.read_text(encoding="utf-8").strip()
        except Exception as exc:
            log.warning("Failed to read knowledge base file %s: %s", file, exc)
            continue
        if not content:
            continue
        chunk = f"# {file.name}\n{content}"
        if total + len(chunk) > max_chars:
            log.warning(
                "Knowledge base exceeded %d chars; '%s' and later files skipped.",
                max_chars,
                file.name,
            )
            break
        chunks.append(chunk)
        total += len(chunk)

    if not chunks:
        log.info("Knowledge base enabled but no matching files found in '%s'.", path)
        return ""

    log.info("Knowledge base loaded: %d file(s), %d chars.", len(chunks), total)
    return "\n\n".join(chunks)


KNOWLEDGE_BASE: str = _load_knowledge_base()

if KNOWLEDGE_BASE:
    PERSONA = (
        f"{PERSONA}\n\n"
        "以下是你可以參考的知識庫內容。當客人問到相關問題時，請優先依據這些資訊回答；"
        "若知識庫中沒有相關資訊，請依你原本的指示處理（誠實告知不確定，不要編造）：\n\n"
        f"---\n{KNOWLEDGE_BASE}\n---"
    )


AI_PROVIDER: str = CONFIG.get("ai", {}).get("provider", "openai")
AI_MODEL: str = CONFIG.get("ai", {}).get("model", "gpt-4o-mini")
AI_TEMPERATURE: float = float(CONFIG.get("ai", {}).get("temperature", 0.7))
AI_MAX_TOKENS: int = int(CONFIG.get("ai", {}).get("max_tokens", 500))

MEMORY_ENABLED: bool = bool(CONFIG.get("memory", {}).get("enabled", True))
MEMORY_TURNS: int = int(CONFIG.get("memory", {}).get("max_turns", 10))

ERROR_MESSAGE: str = (
    CONFIG.get("fallback", {}).get("error_message")
    or "抱歉，我現在有點忙不過來，請稍後再試 🙏"
)

COOLDOWN_SEC: float = float(CONFIG.get("rate_limit", {}).get("cooldown_seconds", 0))


def _resolve_model_id(provider: str, model: str) -> str:
    """Map (provider, model) to LiteLLM's model identifier convention.

    OpenAI accepts the bare model name; all other providers need the
    ``"{provider}/{model}"`` prefix. See: https://docs.litellm.ai/docs/providers
    """
    if provider == "openai":
        return model
    return f"{provider}/{model}"


MODEL_ID = _resolve_model_id(AI_PROVIDER, AI_MODEL)

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

# Construct the LINE clients even when secrets are empty so that this module
# can be imported by tests (e.g. smoke_test.py) without LINE credentials.
# The actual credential check fires at server startup via the lifespan hook
# below, preserving fail-fast behaviour for `uvicorn main:app`.
parser = WebhookParser(LINE_CHANNEL_SECRET or "import-time-placeholder")
line_config = Configuration(
    access_token=LINE_CHANNEL_ACCESS_TOKEN or "import-time-placeholder"
)


# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------
# user_id -> deque of {"role": "user"|"assistant", "content": str}.
# One conversational "turn" = one user message + one assistant reply,
# so we cap each user's history at MEMORY_TURNS * 2 entries.
_history: Dict[str, Deque[Dict[str, str]]] = defaultdict(
    lambda: deque(maxlen=MEMORY_TURNS * 2 if MEMORY_ENABLED else 0)
)
# user_id -> last-seen monotonic timestamp (for cooldown)
_last_seen: Dict[str, float] = {}


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Validate runtime credentials at server startup.

    Putting the check here (instead of at module import) lets test scripts
    import this module without LINE credentials configured, while still
    failing fast when the actual server is started.
    """
    if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
        raise SystemExit(
            "LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN must be set in .env"
        )
    log.info("Linko starting — model=%s, memory=%s", MODEL_ID, MEMORY_ENABLED)
    yield


app = FastAPI(title=f"{BOT_NAME} (Linko)", lifespan=_lifespan)


@app.get("/")
async def root() -> Dict[str, str]:
    return {"name": BOT_NAME, "model": MODEL_ID, "status": "ok"}


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/callback")
async def callback(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature: str = Header(None),
) -> Dict[str, str]:
    """LINE Messaging API webhook entry point.

    We validate the signature, queue each text event for background
    processing, and return 200 immediately so we don't trip LINE's
    webhook timeout (1 s).
    """
    if x_line_signature is None:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature")

    body = (await request.body()).decode("utf-8")
    try:
        events = parser.parse(body, x_line_signature)
    except InvalidSignatureError:
        log.warning("Invalid LINE signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(
            event.message, TextMessageContent
        ):
            background_tasks.add_task(_handle_text_message, event)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Message handling
# ---------------------------------------------------------------------------
def _handle_text_message(event: MessageEvent) -> None:
    user_id = event.source.user_id if event.source else "anonymous"
    user_text = event.message.text.strip()
    reply_token = event.reply_token

    # Per-user cooldown to discourage spam / abuse.
    now = time.monotonic()
    if COOLDOWN_SEC > 0:
        last = _last_seen.get(user_id, 0.0)
        if now - last < COOLDOWN_SEC:
            log.info("Rate-limited user %s", user_id)
            return
    _last_seen[user_id] = now

    log.info("← [%s] %s", user_id, user_text)

    reply_text = _generate_reply(user_id, user_text)

    try:
        with ApiClient(line_config) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
    except Exception:  # pragma: no cover - external API failure
        log.exception("Failed to reply to LINE")
        return

    log.info("→ [%s] %s", user_id, reply_text[:80])


def _generate_reply(user_id: str, user_text: str) -> str:
    """Call the configured LLM via LiteLLM and return the reply text."""
    messages: list[Dict[str, str]] = [{"role": "system", "content": PERSONA}]
    if MEMORY_ENABLED:
        messages.extend(_history[user_id])
    messages.append({"role": "user", "content": user_text})

    try:
        response = litellm.completion(
            model=MODEL_ID,
            messages=messages,
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS,
        )
        reply = response["choices"][0]["message"]["content"].strip()
    except Exception:
        log.exception("LiteLLM call failed (model=%s)", MODEL_ID)
        return ERROR_MESSAGE

    if MEMORY_ENABLED:
        _history[user_id].append({"role": "user", "content": user_text})
        _history[user_id].append({"role": "assistant", "content": reply})

    return reply


# ---------------------------------------------------------------------------
# Entrypoint for `python main.py`
# ---------------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
