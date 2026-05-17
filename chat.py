"""
Linko interactive chat — terminal REPL that talks to your configured bot.

Useful for iterating on bot.persona / ai.model / multi-turn behaviour
without needing a LINE Channel.

Built-in commands (typed as input):
    /quit, /q, /exit   — leave the chat
    /reset             — clear this session's conversation memory
    /info              — show current bot config
    /history           — print stored conversation history
    /help              — show this list

Usage:
    python chat.py
"""

from __future__ import annotations

import sys

# Importing ``main`` triggers config + LiteLLM setup. Thanks to the lifespan
# refactor in main.py, this works without LINE credentials.
from main import (
    BOT_NAME,
    ERROR_MESSAGE,
    MEMORY_ENABLED,
    MEMORY_TURNS,
    MODEL_ID,
    PERSONA,
    _generate_reply,
    _history,
)

USER_ID = "chat-cli-user"

COMMANDS = {
    "/quit", "/q", "/exit",
    "/reset",
    "/info",
    "/history",
    "/help",
}


def _print_info() -> None:
    print(f"  bot     = {BOT_NAME}")
    print(f"  model   = {MODEL_ID}")
    print(f"  memory  = {MEMORY_ENABLED} (最多 {MEMORY_TURNS} 輪)")
    persona_preview = PERSONA.strip().replace("\n", " ")
    if len(persona_preview) > 80:
        persona_preview = persona_preview[:80] + "…"
    print(f"  persona = {persona_preview}")


def _print_help() -> None:
    print("可用指令：")
    print("  /quit, /q, /exit  離開")
    print("  /reset            清除這次的對話記憶")
    print("  /info             顯示 bot 設定")
    print("  /history          顯示目前對話歷史")
    print("  /help             顯示這個說明")


def _print_history() -> None:
    history = list(_history[USER_ID])
    if not history:
        print("（目前沒有對話歷史）")
        return
    for msg in history:
        role = "你" if msg["role"] == "user" else BOT_NAME
        print(f"  {role}: {msg['content']}")


def main() -> int:
    bar = "─" * 50
    print(bar)
    print(f"💬 Linko Chat — 與 {BOT_NAME} 互動")
    print(f"   輸入 /help 查看指令、/quit 離開")
    print(bar)
    _print_info()
    print(bar)

    while True:
        try:
            user_text = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再見！")
            return 0

        if not user_text:
            continue

        if user_text in {"/quit", "/q", "/exit"}:
            print("再見！")
            return 0
        if user_text == "/reset":
            _history[USER_ID].clear()
            print("（記憶已清除）")
            continue
        if user_text == "/info":
            _print_info()
            continue
        if user_text == "/history":
            _print_history()
            continue
        if user_text == "/help":
            _print_help()
            continue
        if user_text.startswith("/") and user_text not in COMMANDS:
            print(f"未知指令：{user_text}（輸入 /help 看清單）")
            continue

        reply = _generate_reply(USER_ID, user_text)
        print(f"{BOT_NAME}：{reply}")

        if reply == ERROR_MESSAGE:
            print("⚠️  AI 呼叫失敗。請看上方 log，或使用 /info 確認設定。")


if __name__ == "__main__":
    sys.exit(main())
