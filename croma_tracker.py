import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

PINCODE = "125051"

# Complete list of all products you want to track simultaneously
PRODUCT_VARIANTS = [
    {
        "name": "Apple iPhone 17 (256GB, Black)",
        "url": "https://www.croma.com/apple-iphone-17-256gb-black-/p/317396"
    },
    {
        "name": "Apple iPhone 17 (256GB, Sage)",
        "url": "https://www.croma.com/apple-iphone-17-256gb-sage-/p/317403"
    },
    {
        "name": "Apple iPhone 17 (256GB, Mist Blue)",
        "url": "https://www.croma.com/apple-iphone-17-256gb-mist-blue-/p/324462"
    },
    {
        "name": "Apple iPhone 17 (256GB, Lavender)",
        "url": "https://www.croma.com/apple-iphone-17-256gb-lavender-/p/324465"
    },
    {
        "name": "Apple iPhone 17 (256GB, White)",
        "url": "https://www.croma.com/apple-iphone-17-256gb-white-/p/324461"
    },
    {
        "name": "OnePlus Nord CE6 Lite 5G (8GB RAM, 128GB, Hyper Black)",
        "url": "https://www.croma.com/oneplus-nord-ce6-lite-5g-8gb-ram-128gb-hyper-black-/p/322994"
    }
]

# Set to True while testing so you get a confirmation ping. Set to False later to stay silent until in stock.
SEND_STATUS_PING = False

# Run continuously for 5 hours 45 minutes before auto-restarting
MAX_RUN_DURATION_SECONDS = 20700

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Telegram error: {e}")

def run_continuous_monitor():
    start_time = time.time()
    check_count = 0

    send_telegram_alert(f"🚀 <b>60-Second Multi-Product Tracker Started!</b>\nTracking iPhones and OnePlus Nord CE6 Lite for pincode {PINCODE}.")

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

        while (time.time() - start_time) < MAX_RUN_DURATION_SECONDS:
            check_count += 1
            print(f"\n--- Check Cycle #{check_count} ---")
            in_stock_found = False

            for variant in PRODUCT_VARIANTS:
                name = variant["name"]
                url = variant["url"]

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(2000)

                    # Set pincode if prompt appears
                    pincode_input = page.locator("input[placeholder*='Pincode'], input[placeholder*='pincode'], #pincode")
                    if pincode_input.count() > 0 and pincode_input.first.is_visible():
                        pincode_input.first.fill(PINCODE)
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(2000)

                    page_text = page.locator("body").inner_text().lower()
                    buy_now_btn = page.locator("button:has-text('Buy Now')")

                    is_available = (
                        buy_now_btn.count() > 0
                        and buy_now_btn.first.is_enabled()
                        and "out of stock" not in page_text
                        and "currently unavailable" not in page_text
                    )

                    # Extract price dynamically
                    price = "Check website"
                    try:
                        price_locator = page.locator(".amount, span:has-text('₹')").first
                        if price_locator.count() > 0:
                            price = price_locator.inner_text().strip()
                    except Exception:
                        pass

                    if is_available:
                        in_stock_found = True
                        alert_msg = (
                            f"🚨 <b>HURRY! ITEM IN STOCK!</b>\n\n"
                            f"📱 <b>Model:</b> {name}\n"
                            f"💰 <b>Price:</b> {price}\n"
                            f"📍 <b>Pincode:</b> {PINCODE}\n"
                            f"🛒 <a href='{url}'>TAP HERE TO BUY NOW</a>"
                        )
                        send_telegram_alert(alert_msg)
                        print(f"-> {name} IN STOCK! Alert sent.")
                    else:
                        print(f"-> {name}: Out of stock.")

                except Exception as e:
                    print(f"Error checking {name}: {e}")

            if not in_stock_found and SEND_STATUS_PING and check_count == 1:
                send_telegram_alert(f"⏱️ Multi-product tracker active. Checking all listed models every minute.")

            # Wait 60 seconds before the next check cycle across all links
            time.sleep(60)

        browser.close()

if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing credentials.")
        sys.exit(1)
    run_continuous_monitor()
