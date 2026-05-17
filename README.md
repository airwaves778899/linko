# Linko 🐙

> **Open-source AI customer service bot for LINE Official Account.**
> Self-hosted. Bring your own API key. Deploy in 5 minutes.
>
> 開源的 LINE 官方帳號 AI 客服機器人。自架部署、自帶 API Key、零月費。

[![CI](https://github.com/airwaves778899/linko/actions/workflows/ci.yml/badge.svg)](https://github.com/airwaves778899/linko/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](#)
[![Status](https://img.shields.io/badge/status-MVP-orange.svg)](#)

---

## 🌏 English summary

This README is primarily in Traditional Chinese (繁體中文). A short English overview:

- **What it is**: A self-hosted AI chatbot for LINE Official Accounts.
- **How it differs**: Bring your own LLM API key — OpenAI, Anthropic, Gemini, LM Studio, or Ollama (powered by [LiteLLM](https://docs.litellm.ai/)). All conversation data stays on your server. MIT licensed.
- **Status**: Early MVP. Working: LINE webhook, multi-model AI replies, multi-turn memory, simple knowledge base. Roadmap: Docker, RAG, admin dashboard, plugins.
- **Quick start**: See the Chinese docs below. English translation: contributions welcome 🙏 (see [`CONTRIBUTING.md`](CONTRIBUTING.md))

---

## ✨ 特色

- 🔌 **多模型支援**：OpenAI / Anthropic / Gemini / 本地 Ollama，改一行設定就能切換（背後使用 [LiteLLM](https://docs.litellm.ai/)）。
- 🔐 **資料完全掌控**：所有 API Key 在你自己的伺服器，專案不經手任何金鑰。
- 💬 **多輪對話記憶**：可設定保留最近 N 輪上下文。
- ⚙️ **設定即可上線**：人格、模型、記憶長度都在 `config.yaml`，不用改程式碼。
- 🚀 **5 分鐘部署**：FastAPI 一鍵啟動，VPS / Docker / 本地都能跑。

> ⚠️ 目前為 **MVP 階段**，僅提供 LINE Webhook + AI 對話。RAG 知識庫、Rich Menu、管理後台等規劃中。

---

## 🚀 快速開始

### 1. 準備 LINE Channel

到 [LINE Developers Console](https://developers.line.biz/) 建立 Messaging API Channel，取得：

- **Channel Secret**
- **Channel Access Token (long-lived)**

並到「Messaging API settings」把「Auto-reply messages」關掉、把「Webhook」打開。

### 2. Clone 與安裝

```bash
git clone https://github.com/airwaves778899/linko
cd linko
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 填入設定

```bash
cp .env.example .env
cp config.yaml.example config.yaml
```

編輯 `.env` 填入你的 LINE 金鑰，並擇一填入 AI provider 的 API Key（OpenAI / Anthropic / Gemini）。

### 4. 啟動

```bash
python main.py
# 或：uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. 對外暴露（開發階段用 ngrok）

```bash
ngrok http 8000
```

把 ngrok 給的 HTTPS URL 加上 `/callback`（例如 `https://abc123.ngrok.io/callback`），貼到 LINE Console 的 **Webhook URL** 欄位，按「Verify」確認連通。

打開 LINE 加你的官方帳號為好友，傳訊息試試 🎉

---

## 🔬 Smoke Test（先驗證 AI，不需 LINE 金鑰）

如果你還不想申請 LINE Channel，可以先用 `smoke_test.py` 直接驗證 AI 連線、人格設定、多輪記憶這幾條鏈路有沒有問題。

```bash
# 1. 在 LM Studio 啟動 Local Server，載入一個模型，記下模型 ID
#    可用 curl http://localhost:1234/v1/models 確認

# 2. 建立 .env（LINE 兩行可以留空，只填 LM Studio 即可）
cp .env.example .env
#   編輯後內容例如：
#     LM_STUDIO_API_BASE=http://localhost:1234/v1
#     LM_STUDIO_API_KEY=lm-studio

# 3. 建立 config.yaml 並把 provider 改成 lm_studio
cp config.yaml.example config.yaml
#   把 ai.provider 改成 "lm_studio"
#   把 ai.model 改成 LM Studio 載入的模型名稱

# 4. 跑 smoke test
python smoke_test.py
```

預期輸出會印出三輪對話，最後一行 `✅ Smoke test passed`。若看到 `AI 呼叫失敗`，腳本會列出檢查清單協助排查。

驗證通過之後，再進到下一節申請 LINE Channel 就行了。

---

## 💬 互動 chat（用 terminal 直接跟 bot 對話）

`chat.py` 提供一個簡單的 REPL，方便你在沒有 LINE 的情況下持續迭代 persona、試不同模型、模擬多輪對話：

```bash
python chat.py
```

內建指令（在對話中輸入）：

| 指令 | 作用 |
|---|---|
| `/quit`、`/q`、`/exit` | 離開 |
| `/reset` | 清除這次的對話記憶 |
| `/info` | 顯示目前 bot 設定（model / persona） |
| `/history` | 顯示目前對話歷史 |
| `/help` | 顯示指令清單 |

這個工具不會碰 LINE，所有對話都只在本機 process 內。重啟即清空。

---

## 📚 知識庫（簡單版）

把你的 FAQ / 商品資訊 / 營業時間之類的內容放在 `knowledge_base/` 資料夾底下，啟動時會自動讀進來、附加到 Bot 的 system prompt。Bot 之後就能依據這些資訊回答客人的問題。

```bash
# 1. 看一下範例
cat knowledge_base/example_faq.txt

# 2. 加入你自己的內容（可以放多個檔案）
notepad knowledge_base/my_faq.txt
notepad knowledge_base/products.md

# 3. 重啟程式（chat.py 或 main.py 都可以）
python chat.py
```

啟動時 log 會印出載入了幾個檔案、總共幾個字元，類似：

```
INFO linko: Knowledge base loaded: 2 file(s), 4321 chars.
```

設定（在 `config.yaml`）：

| 欄位 | 預設 | 說明 |
|---|---|---|
| `knowledge_base.enabled` | `true` | 是否啟用 |
| `knowledge_base.path` | `knowledge_base` | 資料夾位置 |
| `knowledge_base.extensions` | `[".txt", ".md"]` | 要讀的副檔名 |
| `knowledge_base.max_chars` | `10000` | 總字元上限（防止不小心撐爆 LLM context） |

⚠️ **限制**：這是 MVP 版本，把整個知識庫塞進 system prompt。當你的內容超過 10K 字元時，建議切成多個小檔案，並依需求調整 `max_chars`。等真的需要動態檢索（例如知識庫超過 50K 字元、或要支援 PDF）時，會升級為 RAG 架構。

---

## ⚙️ 設定說明

### `.env`

| 變數 | 說明 | 必填 |
|---|---|:---:|
| `LINE_CHANNEL_SECRET` | LINE Channel Secret | ✅ |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel Access Token | ✅ |
| `OPENAI_API_KEY` | OpenAI 金鑰 | ⚠️ 三選一 |
| `ANTHROPIC_API_KEY` | Anthropic 金鑰 | ⚠️ 三選一 |
| `GEMINI_API_KEY` | Google Gemini 金鑰 | ⚠️ 三選一 |
| `LM_STUDIO_API_BASE` | 本地 LM Studio URL（預設 `http://localhost:1234/v1`） | 選填 |
| `LM_STUDIO_API_KEY` | LM Studio 金鑰（隨便填一個非空字串即可） | 選填 |
| `OLLAMA_API_BASE` | 本地 Ollama URL | 選填 |
| `PORT` | 伺服器埠號（預設 8000） | 選填 |
| `HOST` | 監聽位址（預設 0.0.0.0） | 選填 |
| `LOG_LEVEL` | 日誌等級（預設 INFO） | 選填 |

### `config.yaml`

主要欄位：

- `bot.name` — Bot 名稱
- `bot.persona` — **AI 人格 / 行為指示（最重要）**，決定它怎麼說話
- `ai.provider` — `openai` / `anthropic` / `gemini` / `ollama`
- `ai.model` — 對應的模型名稱（見下方對照表）
- `memory.max_turns` — 對話記憶輪數
- `rate_limit.cooldown_seconds` — 同一人兩則訊息間最少間隔（防濫用）

### 模型對照範例

| Provider | `ai.provider` | `ai.model` 範例 |
|---|---|---|
| OpenAI | `openai` | `gpt-4o-mini` |
| Anthropic | `anthropic` | `claude-3-5-haiku-20241022` |
| Gemini | `gemini` | `gemini-1.5-flash` |
| LM Studio（本地） | `lm_studio` | LM Studio 內顯示的模型名稱，例如 `qwen2.5-7b-instruct` |
| Ollama（本地） | `ollama` | `llama3.2` |

完整模型清單見 [LiteLLM Providers 文件](https://docs.litellm.ai/docs/providers)。

---

## 🛠 專案結構（MVP）

```
linko/
├── .github/
│   ├── ISSUE_TEMPLATE/         # Bug report / Feature request 模板
│   └── workflows/ci.yml        # GitHub Actions：語法檢查 + import smoke test
├── knowledge_base/             # 知識庫資料夾（你的 FAQ 放這裡）
│   └── example_faq.txt         # 範本，請複製改寫
├── main.py                     # FastAPI 入口：webhook + AI 對話
├── chat.py                     # 互動式 terminal REPL
├── smoke_test.py               # 不需 LINE 即可驗證 AI 端
├── config.yaml.example         # 行為設定範本（persona / model / 記憶）
├── .env.example                # 金鑰範本
├── requirements.txt
├── README.md                   # 你正在看的這個
├── CHANGELOG.md
├── CONTRIBUTING.md             # 貢獻指南
├── CODE_OF_CONDUCT.md
├── SECURITY.md                 # 安全漏洞回報政策
├── LICENSE                     # MIT
├── .gitattributes              # LF 換行規範
└── .gitignore
```

未來會加入 `docker/`、`plugins/` 等——當有真正的使用者反應需要時才加，避免過早抽象化。

---

## 🐳 Docker（之後加）

MVP 階段尚未提供 Dockerfile，請先用 Python 直接跑。Docker 支援會在第二迭代加入。

---

## 🤝 貢獻

歡迎 Issue / Pull Request。請先閱讀 [`CONTRIBUTING.md`](CONTRIBUTING.md) 了解貢獻方式。

---

## 📄 授權

本專案以 [MIT License](LICENSE) 釋出。歡迎自由使用、修改、商業應用。
