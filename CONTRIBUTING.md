# 貢獻指南 / Contributing to Linko

歡迎參與 Linko！這份文件說明如何回報問題、貢獻程式碼、改進文件。

---

## 🐛 回報問題 / Reporting issues

請開 Issue 並使用對應的 template：

- **Bug 回報**：用 `Bug report` template
- **新功能提議**：用 `Feature request` template
- **問題詢問**：直接開 Issue 並加 `question` label

開 Issue 前請先搜尋確認沒有重複。

---

## 💻 貢獻程式碼 / Contributing code

### 開發環境設定

```bash
git clone https://github.com/airwaves778899/linko
cd linko
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
cp config.yaml.example config.yaml
# 編輯 .env 跟 config.yaml 填入你的金鑰與設定
```

### 跑驗證

提交 PR 前請至少做這三件事：

```bash
# 1. Python 語法檢查
python -m py_compile main.py chat.py smoke_test.py

# 2. Smoke test（需要 AI provider 設定好）
python smoke_test.py

# 3. 手動互動測試
python chat.py
```

CI 會在每個 PR 自動跑前兩個。

### Coding 風格

- 用 **type hints**（`from __future__ import annotations` 已在用）
- Docstring 用 triple-quoted 風格，公開函式必寫
- 行寬建議在 **100 字元**以內
- 變數 / 函式：`snake_case`；class：`CamelCase`；常數：`UPPER_SNAKE`
- 設計哲學：**簡單 > 完整**。優先做能 ship 的最小版本，避免過早抽象化

### Commit message

採用 [Conventional Commits](https://www.conventionalcommits.org/) 風格：

- `feat: 加入 RAG 知識庫支援`
- `fix: webhook timeout 防呆`
- `docs: 補英文 README`
- `refactor: 把 LINE client 抽出獨立模組`
- `chore: 升級 LiteLLM 到 1.42`
- `test: 為 _resolve_model_id 加單元測試`

### Pull Request 流程

1. **Fork** → 在自己 fork 開新 branch（命名如 `feat/pdf-knowledge-base`、`fix/cooldown-edge-case`）
2. 改完 + 自己驗過（見上方「跑驗證」）
3. 開 PR 時：
   - 標題寫清楚做了什麼
   - 描述包含「為什麼要這個改動」、影響範圍、有沒有 breaking change
   - Link 對應的 Issue（如有）
4. 等 reviewer 看，依 feedback 修改
5. Merge 採 **squash & merge**，由 maintainer 操作

---

## 📝 文件貢獻

任何文字、文件、範例知識庫、翻譯的改進都歡迎。typo 修正、英文翻譯、截圖補充都算。

特別歡迎：

- **英文文件**：目前 README 主要是繁體中文，英文化的 PR 非常受歡迎
- **使用案例**：如果你用 Linko 做了什麼有趣的應用，歡迎到 Discussions 分享，或直接 PR 加入 README 的「Showcase」區段

---

## ❓ 有問題？

- 開 Issue 用 `question` label
- 在現有 issue 留言
- 或到 Discussions 發問

---

## 📄 授權

提交 PR 等同同意你的貢獻會以 [MIT License](LICENSE) 釋出。
