"""
Linko smoke test — verify the AI pipeline works WITHOUT going through LINE.

Calls ``_generate_reply()`` directly with a scripted three-turn conversation
so you can confirm:

  1. LiteLLM can reach the configured AI provider (e.g. LM Studio).
  2. The persona / system prompt is applied.
  3. Multi-turn memory works — the bot should remember the first message
     when asked about it in the third turn.

Run this BEFORE setting up a LINE Channel, so you can validate the
LLM connection independently from LINE infrastructure.

Usage:
    python smoke_test.py
"""

from __future__ import annotations

import sys

# Importing ``main`` triggers config + LiteLLM setup. Thanks to the lifespan
# refactor, this works even without LINE credentials.
from main import (
    BOT_NAME,
    ERROR_MESSAGE,
    MEMORY_ENABLED,
    MODEL_ID,
    _generate_reply,
    _history,
)


def main() -> int:
    bar = "=" * 50
    print(bar)
    print("Linko Smoke Test")
    print(bar)
    print(f"  bot    = {BOT_NAME}")
    print(f"  model  = {MODEL_ID}")
    print(f"  memory = {MEMORY_ENABLED}")
    print()

    user_id = "smoketest-user"
    prompts = [
        "你好，我叫 Bryan。",
        "請問你叫什麼名字？",
        "你還記得我剛剛說我叫什麼嗎？",
    ]

    for i, prompt in enumerate(prompts, 1):
        print(f"[{i}] 我：{prompt}")
        reply = _generate_reply(user_id, prompt)
        print(f"    Bot：{reply}")
        print()

        if reply == ERROR_MESSAGE:
            print("⚠️  AI 呼叫失敗。請檢查：")
            print("    1. LM Studio 的 Local Server 是否已啟動？")
            print("       可用以下指令確認：")
            print("       curl http://localhost:1234/v1/models")
            print("    2. .env 中 LM_STUDIO_API_BASE 與 LM_STUDIO_API_KEY 是否已填？")
            print("    3. config.yaml 的 ai.model 是否與 LM Studio 載入的模型名稱一致？")
            print()
            print("    程式的詳細錯誤已透過 logging 輸出在上方，可參考排查。")
            return 1

    history_size = len(_history[user_id])
    print(bar)
    print(f"✅ Smoke test passed — 共保留 {history_size} 條對話歷史")
    print(bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
