# 🍢 全台夜市 x 行動支付優惠即時通 (All-in-GitHub + Telegram)

專為台灣夜市與商圈打造的**行動支付優惠追蹤與防踩雷神器**！自動追蹤街口支付、台灣Pay、LINE Pay、全支付、悠遊付等各大夜市最新吃喝回饋，具備**即時額滿檢驗**、**回饋率高至低排行**與 **Telegram 自動通知**。

👉 **線上即時成果網址：** [https://jmscyc.github.io/taiwan-nightmarket-pay/](https://jmscyc.github.io/taiwan-nightmarket-pay/)

---

## 🤖 給 AI 改版專用指南（以後改版看這裡！）

為了讓你在日後**最方便、最直覺地下載檔案直接丟給 AI 改版**，本專案已完成**極致單一檔案架構 (Monolithic Architecture)** 收斂，重點功能**絕不拆碎到十幾個檔案**：

### 📌 改版時你只需要下載這 2 個檔案（挑你要改的下載）：

| 改版目標 | 要下載給 AI 的檔案 | 說明 |
| :--- | :--- | :--- |
| **🎨 1. 改介面 / 加功能 / 調整排版** | **`index.html`** | **前端所有功能與樣式都在這一個檔案內！**<br>包含所有 HTML 結構、Tailwind CSS、排行榜排序演算法、台北市預設過濾、夜市/縣市篩選標籤、一鍵複製攻略（含 LINE 內開相容）、iOS Safe Area 安全邊界、查無結果一鍵重設按鈕、雙分頁切換。**以後改介面只需下載 `index.html` 丟給 AI 即可！** |
| **⚙️ 2. 改爬蟲 / 額滿判定 / Telegram** | **`scripts/scan_and_notify.py`** | **後端所有自動化邏輯都在這一個檔案內！**<br>包含爬蟲抓取、額滿/終止關鍵字驗證、每週六早上十點定時週報推播、手動即時額滿檢查、資料庫更新回寫。**以後改後端自動化只需下載它！** |

> 💡 **資料庫備註**：若要手動新增或修改夜市活動資料，直接編輯 `data/promotions.json` 即可。

---

## 🌟 核心特色功能與手機優化細節

1. **🏆 預設首頁：回饋排行榜 (預設台北市)**：
   - 開啟網頁直接顯示「台北市推薦」的最高回饋排行（例如：士林夜市台灣Pay 20%）。
   - **嚴格過濾**：自動排除「已額滿 (FULL)」與「已過期 (EXPIRED)」的活動，**只保留真正尚有名額的有效回饋**。
   - 具備 🥇 冠軍、🥈 亞軍、🥉 季軍視覺標籤。
   - 剩餘天數 $\le 3$ 天自動標示 `⏳ 剩 X 天` 倒數提醒。
   - 支援依縣市（台北/新北/台中/高雄/花蓮/全部）或指定夜市快速篩選。

2. **🔍 夜市搜尋與額滿監控**：
   - 即時關鍵字搜尋夜市名稱（寧夏、士林、逢甲、六合等）或支付工具。
   - 保留「⚠️ 已額滿」項目並清楚標記官方公告，避免現場白跑一趟。

3. **📱 行動端極致優化（防卡頓與邊界處理）**：
   - **iOS Home Bar 安全邊界**：底部導覽列支援 `env(safe-area-inset-bottom)`，在全螢幕 iPhone 上不被橫條遮擋。
   - **全環境剪貼簿相容 (Clipboard Fallback)**：點擊「📋 複製分享」時，即使在 LINE 內建瀏覽器或 FB 內開網頁，也能 100% 成功複製攻略文字至剪貼簿！
   - **查無結果一鍵回血重設**：若在特定夜市查無有效優惠，空狀態提供明顯的「🔄 查看全台所有夜市優惠」按鈕，單點即可快速重設所有標籤。

4. **📲 Telegram 每週週報與手動即時驗證**：
   - **每週定時推播**：每週六早上 10:00 (台灣時間) 自動發送本週夜市優惠精選排行榜 TOP 5 與額滿避雷名單。
   - **手動一鍵驗證**：出發逛夜市前，在 GitHub Actions 點選 `manual_check` 即時抓取最新名額狀況並回報到 Telegram。

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

# 執行即時手動額滿檢驗
python3 scripts/scan_and_notify.py --mode manual_check

# 執行每週六週報推播測試
python3 scripts/scan_and_notify.py --mode saturday_digest

# 本機預覽網頁
python3 -m http.server 8000
```
