import os
import sys
import time
import random
import requests
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

PINCODE = "125051"  # Your 6-digit delivery pincode
PRODUCT_URL = "https://www.croma.com/apple-iphone-17-256gb-sage-/p/317403"  # Croma iPhone 17 URL

# Runs for 5 hours 45 minutes, then exits so GitHub Actions can auto-restart a fresh session
MAX_RUN_DURATION_SECONDS = 20700

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def set_pincode_if_present(page):
    try:
        pincode_input = page.locator("input[placeholder*='Pincode'], input[placeholder*='pincode'], #pincode")
        if pincode_input.count() > 0 and pincode_input.first.is_visible():
            pincode_input.first.fill(PINCODE)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2500)
    except Exception:
        pass

def run_continuous_monitor():
    start_time = time.time()
    notified_in_stock = False
    check_count = 0

    send_telegram_alert(
        f"✅ <b>24/7 High-Speed Croma Tracker Active!</b>\n"
        f"📍 Pincode: {PINCODE}\n"
        f"⏱ Checking every 5–8 seconds..."
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Block heavy images and fonts to make page refreshes take only ~1-2 seconds
        page.route("**/*.{png,jpg,jpeg,webp,gif,svg,woff,woff2}", lambda route: route.abort())

        while (time.time() - start_time) < MAX_RUN_DURATION_SECONDS:
            check_count += 1
            try:
                if check_count == 1:
                    page.goto(PRODUCT_URL, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(3000)
                    set_pincode_if_present(page)
                else:
                    page.reload(wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(1500)

                page_text = page.locator("body").inner_text().lower()
                buy_now_btn = page.locator("button:has-text('Buy Now')")

                is_available = (
                    buy_now_btn.count() > 
