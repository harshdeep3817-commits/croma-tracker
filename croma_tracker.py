
import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

PINCODE = "125051"

PRODUCT_VARIANTS = [
    {
        "name": "iPhone 17 (Black)",
        "url": "https://www.croma.com/apple-iphone-17-256gb-black-/p/317396"
    },
    {
        "name": "iPhone 17 (Sage)",
        "url": "https://www.croma.com/apple-iphone-17-256gb-sage-/p/317403"
    },
    {
        "name": "iPhone 17 (Mist Blue)",
        "url": "https://www.croma.com/apple-iphone-17-256gb-mist-blue-/p/324462"
    },
    {
        "name": "iPhone 17 (Lavender)",
        "url": "https://www.croma.com/apple-iphone-17-256gb-lavender-/p/324465"
    },
    {
        "name": "iPhone 17 (White)",
        "url": "https://www.croma.com/apple-iphone-17-256gb-white-/p/324461"
    },
    {
        "name": "OnePlus Nord CE6 Lite 5G",
        "url": "https://www.croma.com/oneplus-nord-ce6-lite-5g-8gb-ram-128gb-hyper-black-/p/322994"
    }
]

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

    send_telegram_alert(f"🚀 <b>Fixed Tracker Started!</b> Monitoring all products for pincode {PINCODE}.")

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
            status_report = f"🔍 <b>Check Cycle #{check_count}</b>\n"

            for variant in PRODUCT_VARIANTS:
                name = variant["name"]
                url = variant["url"]

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(2500)

                    # Enter pincode and apply if visible
                    pincode_input = page.locator("input[placeholder*='Pincode'], input[placeholder*='pincode'], #pincode")
                    if pincode_input.count() > 0 and pincode_input.first.is_visible():
                        pincode_input.first.fill(PINCODE)
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(2500)
                        
                        apply_btn = page.locator("button:has-text('Apply'), span:has-text('Apply')")
                        if apply_btn.count() > 0:
                            try:
                                apply_btn.first.click(timeout=2000)
                                page.wait_for_timeout(2000)
                            except Exception:
                                pass

                    # Look specifically at the main purchase action buttons
                    purchase_btn = page.locator("button:has-text('Buy Now'), button:has-text('Add to Cart'), button:has-text('Add To Cart')")
                    
                    btn_text = ""
                    if purchase_btn.count() > 0:
                        btn_text = purchase_btn.first.inner_text().lower()

                    # Determine availability strictly from the action button state
                    is_available = (
                        purchase_btn.count() > 0
                        and purchase_btn.first.is_enabled()
                        and "notify" not in btn_text
                        and "out of stock" not in btn_text
                        and "unavailable" not in btn_text
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
                        alert_msg = (
                            f"🚨 <b>HURRY! ITEM IN STOCK!</b>\n\n"
                            f"📱 <b>Model:</b> {name}\n"
                            f"💰 <b>Price:</b> {price}\n"
                            f"📍 <b>Pincode:</b> {PINCODE}\n"
                            f"🛒 <a href='{url}'>TAP HERE TO BUY NOW</a>"
                        )
                        send_telegram_alert(alert_msg)
                        status_report += f"✅ {name}: <b>IN STOCK! ({price})</b>\n"
                        print(f"-> {name} IN STOCK! Alert sent.")
                    else:
                        status_report += f"❌ {name}: Out of Stock\n"
                        print(f"-> {name}: Out of stock.")

                except Exception as e:
                    status_report += f"⚠️ {name}: Error\n"
                    print(f"Error checking {name}: {e}")

            # Send cycle report to Telegram
            send_telegram_alert(status_report)

            # Wait 60 seconds before next loop
            time.sleep(60)

        browser.close()

if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        sys.exit(1)
    run_continuous_monitor()
    
