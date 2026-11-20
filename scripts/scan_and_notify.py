#!/usr/bin/env python3
"""
台灣各大夜市與吃喝行動支付優惠爬蟲、額滿驗證與 Telegram 週報推播腳本
支援功能：
1. 每週六早上 10:00 (台灣時間) 自動發送本週精選夜市支付優惠週報。
2. 隨時手動執行 (CLI / GitHub Actions 手動按鈕) 即時驗證名額是否額滿。
"""

import os
import sys
import json
import re
import argparse
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


def fetch_url_text(url: str, timeout: int = 8) -> str:
    """抓取指定網頁並提取純文字內容"""
    if not url or not url.startswith("http"):
        return ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
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

    current_status = promo.get("status", "ACTIVE")
    
    # 2. 檢查額滿關鍵字
    if html_text:
        for kw in QUOTA_FULL_KEYWORDS:
            if kw in html_text:
                return "FULL", f"⚠️ 偵測到官方網頁出現【{kw}】相關公告，名額已額滿！"
                
    # 3. 若原先是 FULL，維持狀態
    if current_status == "FULL":
        return "FULL", promo.get("status_note", "⚠️ 官方已公告預算全數回饋完畢/額滿")

    return "ACTIVE", "尚有名額，進行中"


def send_telegram_message(bot_token: str, chat_id: str, message: str, reply_markup: dict = None) -> bool:
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
    if reply_markup:
        payload["reply_markup"] = reply_markup

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print("[Telegram] 推播發送成功！")
                return True
    except Exception as e:
        print(f"[Telegram Error] 推播失敗: {e}", file=sys.stderr)
    return False


def send_saturday_weekly_digest(promos: list, bot_token: str, chat_id: str):
    """每週六早上 10:00 發送當週精選夜市支付優惠週報"""
    active_promos = [p for p in promos if p.get("status") == "ACTIVE"]
    full_promos = [p for p in promos if p.get("status") == "FULL"]

    def parse_rate(p):
        r_str = p.get("discount_rate") or p.get("discount") or ""
        m = re.search(r"(\d+(\.\d+)?)", r_str)
        return float(m.group(1)) if m else 0

    active_promos.sort(key=parse_rate, reverse=True)

    today_str = datetime.now().strftime("%Y/%m/%d")
    msg = f"🍢 <b>【全台夜市 x 行動支付】週末吃喝回饋週報 ({today_str})</b>\n"
    msg += "週末迺夜市！已為您自動檢驗各大行動支付最新名額狀態：\n\n"

    msg += "🏆 <b>【本週尚有名額・回饋排行榜 TOP 5】</b>\n"
    for i, p in enumerate(active_promos[:5]):
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i] if i < 5 else "🔹"
        msg += f"{medal} <b>{p['night_market']}</b> ({p.get('city', '')})\n"
        msg += f"   💳 {p['payment']} ｜ <b>{p['discount']}</b>\n"
        msg += f"   💡 {p.get('rules_summary', '')}\n\n"

    if full_promos:
        msg += "⚠️ <b>【額滿警報！現場請勿刷這幾檔】</b>\n"
        for p in full_promos[:3]:
            msg += f"❌ {p['night_market']} ({p['payment']})：{p.get('status_note', '額滿')}\n"
        msg += "\n"

    msg += "👉 點擊下方按鈕可開啟網頁查看全台排行榜與商圈篩選！"

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📱 開啟夜市支付排行榜", "url": "https://jmscyc.github.io/taiwan-nightmarket-pay/"}
            ]
        ]
    }
    send_telegram_message(bot_token, chat_id, msg, reply_markup)


def send_manual_check_report(promos: list, newly_full: list, bot_token: str, chat_id: str):
    """手動更新時發送即時驗證回報"""
    active_count = len([p for p in promos if p.get("status") == "ACTIVE"])
    full_count = len([p for p in promos if p.get("status") == "FULL"])
    
    msg = "🔍 <b>【夜市支付名額・即時手動檢驗報告】</b>\n\n"
    msg += f"✅ 驗證完成時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    msg += f"🟢 進行中且尚有名額：<b>{active_count}</b> 檔\n"
    msg += f"⚠️ 已額滿項目：<b>{full_count}</b> 檔\n\n"

    if newly_full:
        msg += "🚨 <b>本次新發現額滿活動：</b>\n"
        for p in newly_full:
            msg += f"• <b>{p['night_market']}</b> - {p['payment']} ({p['title']})\n"
    else:
        msg += "✨ 本次檢查無新增的額滿警訊，請安心出發！\n"

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📱 查看即時排行榜", "url": "https://jmscyc.github.io/taiwan-nightmarket-pay/"}
            ]
        ]
    }
    send_telegram_message(bot_token, chat_id, msg, reply_markup)


def run_scanner(data_path: str = "data/promotions.json", mode: str = "auto"):
    print(f"=== 開始執行夜市優惠掃描與額滿檢驗 [模式: {mode}]: {datetime.now(timezone.utc).isoformat()} ===")
    
    if not os.path.exists(data_path):
        print(f"[Error] 找不到資料庫檔案: {data_path}", file=sys.stderr)
        return

    with open(data_path, "r", encoding="utf-8") as f:
        existing_promos = json.load(f)

    old_status_map = {p["id"]: p.get("status", "ACTIVE") for p in existing_promos}
    
    updated_promos = []
    newly_full_promos = []
    
    for promo in existing_promos:
        check_url = promo.get("quota_check_url") or promo.get("source_url")
        page_text = ""
        if check_url and promo.get("status") != "EXPIRED":
            page_text = fetch_url_text(check_url, timeout=5)

        new_status, note = check_quota_status(promo, page_text)
        old_status = old_status_map.get(promo["id"], "ACTIVE")

        if new_status == "FULL" and old_status != "FULL":
            newly_full_promos.append(promo)
            print(f"[STATUS CHANGE] {promo['night_market']} - {promo['payment']} 名額已滿！")

        promo["status"] = new_status
        if note:
            promo["status_note"] = note
        promo["last_checked"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        updated_promos.append(promo)

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(updated_promos, f, ensure_ascii=False, indent=2)
    print(f"[Success] 已更新 {len(updated_promos)} 筆活動資料至 {data_path}")

    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if tg_token and tg_chat_id:
        if mode == "saturday_digest":
            send_saturday_weekly_digest(updated_promos, tg_token, tg_chat_id)
        elif mode == "manual_check":
            send_manual_check_report(updated_promos, newly_full_promos, tg_token, tg_chat_id)
        elif newly_full_promos:
            send_manual_check_report(updated_promos, newly_full_promos, tg_token, tg_chat_id)
    else:
        print("[Info] TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 未提供，僅更新本地資料庫。")

    print("=== 掃描與驗證完成 ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="夜市支付優惠掃描與 Telegram 推播")
    parser.add_argument("--mode", choices=["auto", "saturday_digest", "manual_check"], default="auto",
                        help="執行模式: auto (自動更新), saturday_digest (每週六週報), manual_check (即時手動檢驗)")
    args = parser.parse_args()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    default_json_path = os.path.join(current_dir, "..", "data", "promotions.json")
    run_scanner(default_json_path, mode=args.mode)
