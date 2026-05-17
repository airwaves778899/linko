# Security Policy

## 回報安全漏洞 / Reporting a vulnerability

如果你發現 Linko 有安全問題，**請不要開公開 Issue**。請透過以下任一方式私下告知：

- **GitHub Security Advisories**（推薦）：到本 repo 的 Security 分頁 → "Report a vulnerability"
- **Email**：`bryanlin1121@gmail.com`

我們會在 **7 個工作天內**回覆，並依嚴重程度安排修復時程。

請在回報中盡量包含：

- 重現步驟
- 受影響的版本
- 你判斷的影響範圍
- 建議的修復方向（如有）

---

## 支援版本

Linko 目前處於 MVP 階段（v0.x），**只支援最新版本**。等正式發布 v1.0 之後會制定明確的支援週期。

---

## 設計上的安全考量

Linko 的安全模型：

- **API 金鑰**：放在 `.env`，由 `.gitignore` 強制阻擋入版控。所有 provider 透過 LiteLLM 走標準 ENV 流程，專案本身不會記錄或傳輸金鑰
- **LINE 簽章驗證**：每個 webhook 都驗 HMAC-SHA256，不通過直接回 HTTP 400 並 log warning
- **對話記憶**：純記憶體（`collections.deque`），重啟即清空，**不持久化到磁碟或外部儲存**
- **知識庫**：可能包含商業敏感資訊。`knowledge_base/` 預設被 `.gitignore` 排除（除了 `example_faq.txt`），避免不小心 commit

---

## Deploy 在公開伺服器時的建議

如果你要把 Linko 暴露到公網，請額外考慮：

- **TLS**：用反向代理（Nginx / Caddy / Cloudflare）做 HTTPS 終結，LINE webhook 只接受 HTTPS
- **來源限制**：限制 `/callback` 只接受 LINE 公布的 webhook IP 段
- **Rate limit**：啟用 `config.yaml` 的 `rate_limit.cooldown_seconds`，避免單一 user 灌爆 API quota
- **日誌脫敏**：目前 log 會印出 user_id 與訊息內容前 80 字，如有 PII 疑慮，請改 log level 或自行 patch
- **金鑰輪替**：定期更換 LINE Channel Access Token 與 AI provider 金鑰
