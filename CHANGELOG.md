# Changelog

依 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/) 格式，版號採 [Semantic Versioning](https://semver.org/lang/zh-TW/)。

## [Unreleased]

### 規劃中

- LINE Channel 端對端測試
- `Dockerfile` + `docker-compose.yml`
- 知識庫升級至 RAG（向量檢索）
- 管理後台（FastAPI + 簡易 HTML）
- 插件系統

---

## [0.1.0] - 2026-05-17

第一版 MVP。

### Added

- **LINE webhook 接收**：FastAPI + `line-bot-sdk-python` v3，含簽章驗證
- **多 AI 模型支援**：透過 LiteLLM 整合 OpenAI / Anthropic / Gemini / LM Studio / Ollama
- **多輪對話記憶**：in-memory `deque`，per-user 隔離，可設定保留輪數
- **人格 / 行為設定**：`config.yaml` 的 `bot.persona` 欄位，支援多行
- **簡易知識庫**：讀取 `knowledge_base/*.txt` 與 `*.md`，concat 後附加到 system prompt，含 `max_chars` 上限保護
- **Per-user cooldown**：防濫用，可設定同一人兩則訊息最小間隔
- **`smoke_test.py`**：三輪對話腳本，不需 LINE 即可驗證 AI 端
- **`chat.py`**：互動式 terminal REPL，內建 `/reset`、`/info`、`/history`、`/help` 指令
- **設定檔自動 fallback**：缺 `config.yaml` 時退回讀 `config.yaml.example`，降低新手 onboarding 摩擦
- **Lifespan 啟動檢查**：LINE 金鑰只在 server 啟動時驗證，方便測試腳本 import 主模組
- **完整文件**：繁中 `README.md`、貢獻指南 `CONTRIBUTING.md`、行為準則、安全政策

### Known limitations

- 對話記憶不持久化，重啟即清空
- 知識庫為純 concat（非 RAG），總長受 `max_chars` 限制
- 尚未提供 Dockerfile（規劃中）
- LINE 端尚未完整端對端測試
