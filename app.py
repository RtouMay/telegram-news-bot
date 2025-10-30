from flask import Flask
import threading
import time
import feedparser
import requests
from bs4 import BeautifulSoup
import os

# ---------------- تنظیمات ----------------
app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID", "0"))
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "30"))

SITES = [
    "https://www.destructoid.com/feed/",
    "https://www.gameinformer.com/rss.xml",
    "https://www.thegamer.com/feed/",
    "https://www.pcgamesn.com/feed",
    "https://www.gameshub.com.au/feed/"
]

sent_links = set()

# ---------------- توابع ----------------
def send_message(text):
    """ارسال پیام به تلگرام"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
        resp = requests.post(url, data=data, timeout=15)
        if resp.status_code == 200:
            print("✅ Message sent successfully.", flush=True)
        else:
            print("❌ Telegram send error:", resp.status_code, resp.text, flush=True)
    except Exception as e:
        print("⚠️ Send error:", e, flush=True)


def summarize(text, max_sentences=2):
    """خلاصه کردن متن خبر"""
    soup = BeautifulSoup(text or "", "html.parser")
    clean_text = soup.get_text()
    sentences = [s.strip() for s in clean_text.split(".") if s.strip()]
    summary = ". ".join(sentences[:max_sentences])
    return summary or clean_text[:200]


def check_feeds():
    """چک کردن سایت‌های خبری و ارسال خبر جدید"""
    print("🔄 Feed checker thread started!", flush=True)
    global sent_links
    while True:
        for site in SITES:
            try:
                print(f"🔍 Checking: {site}", flush=True)
                feed = feedparser.parse(site)
                for entry in feed.entries[:2]:
                    if entry.link not in sent_links:
                        sent_links.add(entry.link)
                        title = entry.title
                        summary = summarize(entry.get("summary", ""))
                        msg = f"🕹 <b>{title}</b>\n\n{summary}\n\n🔗 {entry.link}"
                        send_message(msg)
                        print("✅ Sent:", title, flush=True)
            except Exception as e:
                print("⚠️ Error in feed:", e, flush=True)
        time.sleep(CHECK_INTERVAL)


# ---------------- مسیرهای Flask ----------------
@app.route('/')
def home():
    return "<h3>✅ Bot is running!</h3>", 200


@app.route('/keep_alive')
def keep_alive():
    return "✅ Bot is alive!", 200


@app.route('/test_send')
def test_send():
    """ارسال پیام تستی به تلگرام"""
    test_text = "🧪 پیام تستی از ربات اخبار گیمینگ! ✅"
    send_message(test_text)
    return "✅ Test message sent (check Telegram!)", 200


# ---------------- اجرای همزمان Flask و ربات ----------------
if __name__ == "__main__":
    t = threading.Thread(target=check_feeds, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
