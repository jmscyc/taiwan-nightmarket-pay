#!/usr/bin/env python3
"""
台灣各大夜市與吃喝行動支付優惠爬蟲、額滿驗證與 Telegram 自動通知腳本
可單獨在本機執行，亦可由 GitHub Actions 排程定時觸發。
"""

import os
import sys
import json
import re
from datetime import datetime, timezone
import urllib.request
import urllib.parse
from html.parser import HTMLParser

# 額滿/提早結束偵測關鍵字
QUOTA_FULL_KEYWORDS = [
    "額滿", "已達回饋上限", "名額已滿", "預算已用罄", "回饋完畢", 
    "提前結束", "活動終止", "已結束", "暫停發放", "感謝支持，已發放完畢"
]

class SimpleHTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.ignore = False

    def handle_starttag(self, tag, attrs):
        if tag in ["script", "style", "noscript"]:
            self.ignore = True

    def handle_endtag(self, tag):
        if tag in ["script", "style", "noscript"]:
            self.ignore = False

    def handle_data(self, data):
        if not self.ignore:
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned)

    def get_text(self):
        return " ".join(self.text_parts)


def fetch_url_text(url: str, timeout: int = 10) -> str:
    """抓取指定網頁並提取純文字內容"""
    if not url or not url.startswith("http"):
        return ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            html_content = response.read().decode("utf-8", errors="ignore")
            parser = SimpleHTMLTextExtractor()
            parser.feed(html_content)
            return parser.get_text()
    except Exception as e:
        print(f"[Warning] Failed to fetch {url}: {e}", file=sys.stderr)
        return ""


def check_quota_status(promo: dict, html_text: str = "") -> tuple[str, str]:
    """
    驗證活動狀態：
    回傳: (狀態[ACTIVE/FULL/EXPIRED], 說明)
    """
    now = datetime.now(timezone.utc).date()
    end_date_str = promo.get("end_date")
    
    # 1. 檢查是否自然過期
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if now > end_date:
                return "EXPIRED", f"活動已於 {end_date_str} 自然截止"
        except ValueError:
            pass

    # 2. 如果先前已經標記為 FULL，且備註明確，保留或進一步複查
    current_status = promo.get("status", "ACTIVE")
    
    # 3. 若有抓到頁面文字，檢查額滿關鍵字
    if html_text:
        for kw in QUOTA_FULL_KEYWORDS:
            if kw in html_text:
                return "FULL", f"⚠️ 偵測到官方網頁出現【{kw}】相關公告，名額已額滿！"
                
    # 4. 若原先是 FULL，維持狀態
    if current_status == "FULL":
        return "FULL", promo.get("status_note", "⚠️ 官方已公告預算全數回饋完畢/額滿")

    return "ACTIVE", "尚有名額，進行中"


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """發送訊息至 Telegram Bot"""
    if not bot_token or not chat_id:
        print("[Telegram] Bot Token 或 Chat ID 未設定，略過推播。")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print("[Telegram] 推播成功！")
                return True
    except Exception as e:
        print(f"[Telegram Error] 推播失敗: {e}", file=sys.stderr)
    return False


def notify_status_changes(new_promos: list, full_promos: list, bot_token: str, chat_id: str):
    """有新活動或額滿活動時推播 Telegram"""
    messages = []
    
    if new_promos:
        msg = "📢 <b>【全台夜市 x 行動支付】新優惠上架！</b>\n\n"
        for p in new_promos:
            msg += f"🔥 <b>{p['night_market']}</b> ({p.get('city', '')})\n"
            msg += f"💳 <b>支付工具</b>：{p['payment']} ({p['discount']})\n"
            msg += f"📝 <b>內容</b>：{p['title']}\n"
            msg += f"📅 <b>期間</b>：{p.get('start_date', '')} ~ {p.get('end_date', '')}\n"
            msg += f"🔗 <a href='{p['source_url']}'>查看官方詳情</a>\n\n"
        messages.append(msg)

    if full_promos:
        msg = "⚠️ <b>【夜市優惠額滿警告！勿白跑】</b>\n\n"
        for p in full_promos:
            msg += f"❌ <b>{p['night_market']} - {p['payment']}</b>\n"
            msg += f"📌 <b>活動</b>：{p['title']}\n"
            msg += f"💬 <b>狀態</b>：{p.get('status_note', '名額已額滿')}\n\n"
        messages.append(msg)

    for msg in messages:
        send_telegram_message(bot_token, chat_id, msg)


def run_scanner(data_path: str = "data/promotions.json"):
    print(f"=== 開始執行夜市優惠掃描與額滿檢驗: {datetime.now(timezone.utc).isoformat()} ===")
    
    if not os.path.exists(data_path):
        print(f"[Error] 找不到資料庫檔案: {data_path}", file=sys.stderr)
        return

    with open(data_path, "r", encoding="utf-8") as f:
        existing_promos = json.load(f)

    # 記錄舊狀態以便對比異動
    old_status_map = {p["id"]: p.get("status", "ACTIVE") for p in existing_promos}
    
    updated_promos = []
    newly_full_promos = []
    
    for promo in existing_promos:
        check_url = promo.get("quota_check_url") or promo.get("source_url")
        # 僅在特定狀態下選擇性抓取，避免不必要的流量
        page_text = ""
        if check_url and promo.get("status") != "EXPIRED":
            # 抓取頁面驗證額滿關鍵字
            page_text = fetch_url_text(check_url, timeout=5)

        new_status, note = check_quota_status(promo, page_text)
        old_status = old_status_map.get(promo["id"], "ACTIVE")

        # 狀態改變或原有備註更新
        if new_status == "FULL" and old_status != "FULL":
            newly_full_promos.append(promo)
            print(f"[STATUS CHANGE] {promo['night_market']} - {promo['payment']} 已額滿！")

        promo["status"] = new_status
        if note:
            promo["status_note"] = note
        promo["last_checked"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        updated_promos.append(promo)

    # 回寫 promotions.json
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(updated_promos, f, ensure_ascii=False, indent=2)
    print(f"[Success] 已更新 {len(updated_promos)} 筆活動資料至 {data_path}")

    # Telegram 推播
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    
    if newly_full_promos:
        notify_status_changes(new_promos=[], full_promos=newly_full_promos, bot_token=tg_token, chat_id=tg_chat_id)
    else:
        print("[Info] 沒有新增的額滿警報。")

    print("=== 掃描與驗證完成 ===")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    default_json_path = os.path.join(current_dir, "..", "data", "promotions.json")
    run_scanner(default_json_path)
