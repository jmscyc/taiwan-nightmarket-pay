# 🍢 全台夜市 x 行動支付優惠即時通 (All-in-GitHub + Telegram)

專為台灣夜市與商圈打造的**行動支付優惠追蹤神器**！自動追蹤街口支付、台灣Pay、LINE Pay、全支付、悠遊付等各大夜市最新吃喝回饋，具備**即時額滿檢驗**與 **Telegram 自動通知**。

👉 **線上即時成果網址：** [https://jmscyc.github.io/taiwan-nightmarket-pay/](https://jmscyc.github.io/taiwan-nightmarket-pay/)

---

## 🤖 給 AI 改版專用指南（以後改版看這裡！）

為了讓你日後**最方便、最直覺地下載檔案直接丟給 AI 改版**，本專案已完成**極致單一檔案架構 (Monolithic Architecture)** 收斂，重點功能**絕不拆碎到十幾個檔案**：

### 📌 改版時你只需要下載這 2 個檔案（挑你要改的下載）：

| 改版目標 | 要下載給 AI 的檔案 | 說明 |
| :--- | :--- | :--- |
| **🎨 1. 改介面 / 加功能 / 調整排版** | **`index.html`** | **前端所有功能與樣式都在這一個檔案內！**<br>包含所有 HTML 結構、Tailwind CSS、排行榜演算法、夜市/縣市過濾邏輯、Toast 複製分享、雙分頁切換。**以後改介面只需下載 `index.html` 丟給 AI 即可！** |
| **⚙️ 2. 改爬蟲 / 額滿判定 / Telegram** | **`scripts/scan_and_notify.py`** | **後端所有自動化邏輯都在這一個檔案內！**<br>包含爬蟲抓取、額滿/終止關鍵字驗證、Telegram 自動推播格式、資料庫更新回寫。**以後改後端自動化只需下載它！** |

> 💡 **資料庫備註**：若要手動新增或修改夜市活動資料，直接編輯 `data/promotions.json` 即可。

---

## 🌟 核心特色功能

1. **🏆 預設首頁：回饋排行榜 (預設台北市)**：
   - 打開即看到台北市最高回饋排行（例如：士林夜市台灣Pay 20%）。
   - 僅展示「🟢 尚有名額」的進行中項目，自動排除額滿與過期活動。
   - 具備 🥇 冠軍、🥈 亞軍、🥉 季軍視覺標籤。
   - 剩餘天數 $\le 3$ 天自動標示 `⏳ 剩 X 天` 倒數提醒。
   - 支援依縣市（台北/新北/台中/高雄/花蓮/全部）或指定夜市快速篩選。

2. **🔍 夜市搜尋與額滿監控**：
   - 即時關鍵字搜尋夜市名稱（寧夏、士林、逢甲、六合等）或支付工具。
   - 保留「⚠️ 已額滿」項目並清楚標記官方公告，避免現場白跑一趟。

3. **📋 一鍵複製攻略**：
   - 點擊卡片「📋 複製分享」，自動將該夜市名稱、支付方式與結帳規則排版成簡潔訊息，方便直接貼到 LINE 聊天室跟朋友約攤！

4. **📲 Telegram 即時推播**：
   - 當排程偵測到「新優惠上架」或「活動名額剛好額滿」，自動發送帶有直達按鈕的 Telegram 警報。

---

## 🚀 部署與設定指引

### 1. 啟用 GitHub Pages (手機網頁)
1. 進入 Repo -> **Settings** -> **Pages**。
2. **Branch** 選擇 `master`，目錄選擇 `/(root)`，點擊 **Save**。
3. 手機 Safari (iPhone) 或 Chrome (Android) 開啟網址，點擊「加入主畫面」即可全螢幕秒開。

### 2. 設定 Telegram 自動通知 (可選)
1. Telegram 搜尋 `@BotFather` 輸入 `/newbot` 建立機器人取得 Token。
2. Telegram 搜尋 `@userinfobot` 傳送任一訊息取得 Chat ID。
3. 進入 GitHub Repo -> **Settings** -> **Secrets and variables** -> **Actions**，新增：
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

---

## 🛠️ 本地測試指令

```bash
# 執行單元測試
python3 -m unittest discover tests

# 執行爬蟲與額滿檢驗
python3 scripts/scan_and_notify.py

# 本機預覽網頁
python3 -m http.server 8000
```
