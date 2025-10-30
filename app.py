from flask import Flask
import threading
import time
import feedparser
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "180"))

SITES = [
    "https://www.destructoid.com/feed/",
    "https://www.gameinformer.com/rss.xml",
    "https://www.thegamer.com/feed/",
    "https://www.pcgamesn.com/feed",
    "https://www.gameshub.com.au/feed/"
]

sent_links = set()

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
        resp = requests.post(url, data=data, timeout=15)
        if resp.status_code == 200:
            print("✅ Message sent successfully.")
        else:
            print("❌ Telegram error:", resp.status_code, resp.text)
    except Exception as e:
        print("⚠️ Send error:", e)

def summarize(text, max_sentences=2):
    soup = BeautifulSoup(text or "", "html.parser")
    clean = soup.get_text()
    sentences = [s.strip() for s in clean.split(".") if s.strip()]
    summary = ". ".join(sentences[:max_sentences])
    return summary or clean[:200]

def check_feeds():
    while True:
        for site in SITES:
            try:
                feed = feedparser.parse(site)
                for entry in feed.entries[:2]:
                    if entry.link not in sent_links:
                        sent_links.add(entry.link)
                        title = entry.title
                        summary = summarize(entry.get("summary", ""))
                        msg = f"🕹 <b>{title}</b>\n\n{summary}\n\n🔗 {entry.link}"
                        send_message(msg)
                        print("✅ Sent:", title)
            except Exception as e:
                print("⚠️ Error in feed:", e)
        time.sleep(CHECK_INTERVAL)

@app.route('/')
def home():
    return "<h3>✅ Bot is running!</h3>", 200

@app.route('/keep_alive')
def keep_alive():
    return "✅ Bot is alive!", 200

if __name__ == "__main__":
    threading.Thread(target=check_feeds, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
