import os
import sys
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

PINCODE = "125051"
PRODUCT_URL = "https://www.croma.com/apple-iphone-17-256gb-sage-/p/317403"

# --- SETTINGS ---
# Set to True if you want a Telegram message every time it checks and is Out of Stock.
# Set to False so it ONLY messages you when it comes IN STOCK (recommended to avoid spam).
SEND_OUT_OF_STOCK_ALERT = True 

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        print("Telegram Response Code:", response.status_code)
        print("Telegram Response Body:", response.text)
    except Exception as e:
        print(f"Telegram error exception: {e}")

def check_stock():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        try:
            print("Checking Croma page...")
            page.goto(PRODUCT_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            # Set pincode if input prompt is visible
            pincode_input = page.locator("input[placeholder*='Pincode'], input[placeholder*='pincode'], #pincode")
            if pincode_input.count() > 0 and pincode_input.first.is_visible():
                pincode_input.first.fill(PINCODE)
                page.keyboard.press("Enter")
                page.wait_for_timeout(3000)

            page_text = page.locator("body").inner_text().lower()
            buy_now_btn = page.locator("button:has-text('Buy Now')")

            is_available = (
                buy_now_btn.count() > 0
                and buy_now_btn.first.is_enabled()
                and "out of stock" not in page_text
                and "currently unavailable" not in page_text
            )

            return is_available

        except Exception as e:
            print(f"Error checking Croma: {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing Telegram credentials.")
        sys.exit(1)

    print("Running single-check stock verification...")
    in_stock = check_stock()

    if in_stock:
        alert_msg = (
            f"🚨 <b>HURRY! iPhone 17 (Sage) is IN STOCK on Croma!</b>\n\n"
            f"📍 Pincode: {PINCODE}\n"
            f"🛒 <a href='{PRODUCT_URL}'>TAP HERE TO BUY NOW</a>"
        )
        send_telegram_alert(alert_msg)
        print("IN STOCK! Telegram alert sent.")
    else:
        print("Item is currently out of stock.")
        if SEND_OUT_OF_STOCK_ALERT:
            status_msg = (
                f"ℹ️ <b>Croma Status Check</b>\n\n"
                f"iPhone 17 (Sage) is currently <b>Out of Stock</b> for pincode {PINCODE}.\n"
                f"<i>Tracker is active and running smoothly.</i>"
            )
            send_telegram_alert(status_msg)
            print("Out of stock status message sent to Telegram.")
