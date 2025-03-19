from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import requests
import pandas as pd
import os
from datetime import datetime
import pytz

# Telegram Bot Config
TELEGRAM_BOT_TOKEN = "7833485758:AAGxvnMHB6mm-LZnMZ-kYFkB5EVjYQj5jy8"
CHAT_IDS = ["1397852365"]  # Replace with your two chat IDs

# Load existing data if available
price_data = []
if os.path.exists("market_price_updates.csv"):
    df = pd.read_csv("market_price_updates.csv")
    price_data = df.to_dict('records')

def get_gold_price():
    # Configure Chrome options for headless operation
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    try:
        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://milli.gold/")
        
        # Wait for the page to load completely
        time.sleep(5)
        
        # Extract gold price using JavaScript execution
        try:
            price_script = """
            return Array.from(document.querySelectorAll('p')).find(el => 
                el.classList.contains('font-bold') && 
                el.classList.contains('text-deepOcean-focus')
            )?.textContent || 'Not Found';
            """
            gold_price = driver.execute_script(price_script).strip()
        except Exception as e:
            gold_price = "Not Found"
            print(f"❌ Error finding gold price: {e}")
            
        # Extract price change using JavaScript
        try:
            change_script = """
            const el = Array.from(document.querySelectorAll('p')).find(el =>  
                el.classList.contains('text-green-focus') || 
                el.classList.contains('text-red-focus')
            );
            if (!el) return 'Not Found';
            return Array.from(el.querySelectorAll('span'))
                .map(span => span.textContent.trim())
                .join('');
            """
            change_percentage = driver.execute_script(change_script)
        except Exception as e:
            change_percentage = "Not Found"
            print(f"❌ Error finding price change: {e}")
            
        result = {
            "gold_price": gold_price,
            "change_percentage": change_percentage
        }
        
        return result
        
    except Exception as e:
        print(f"❌ General error: {e}")
        return {"gold_price": "Not Found", "change_percentage": "Not Found"}
    finally:
        if 'driver' in locals():
            driver.quit()

def get_usdt_price():
    # Configure Chrome options for headless operation
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    try:
        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://nobitex.ir/usdt/")
        
        # Wait for the page to load completely
        time.sleep(5)
        
        # Extract USDT price using JavaScript
        try:
            price_script = """
            return document.querySelector('div.text-headline-medium.text-txt-neutral-default.dark\\\\:text-txt-neutral-default.desktop\\\\:text-headline-large')?.textContent.trim() || 'Not Found';
            """
            usdt_price = driver.execute_script(price_script)
            
            # If not found, try alternate method
            if usdt_price == 'Not Found':
                usdt_price = driver.find_element(By.CSS_SELECTOR, 
                    'div.text-headline-medium.text-txt-neutral-default.dark\\:text-txt-neutral-default.desktop\\:text-headline-large').text.strip()
        except Exception as e:
            usdt_price = "Not Found"
            print(f"❌ Error finding USDT price: {e}")
            
        return usdt_price
        
    except Exception as e:
        print(f"❌ General error getting USDT price: {e}")
        return "Not Found"
    finally:
        if 'driver' in locals():
            driver.quit()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    for chat_id in CHAT_IDS:
        if chat_id.strip():
            payload = {"chat_id": chat_id.strip(), "text": message, "parse_mode": "HTML"}
            try:
                response = requests.post(url, json=payload)
                print(f"Telegram message sent to {chat_id}, response: {response.status_code}")
            except Exception as e:
                print(f"Failed to send Telegram message: {e}")

def get_shamsi_datetime():
    try:
        # Using pytz to get Tehran time
        tehran_tz = pytz.timezone('Asia/Tehran')
        now = datetime.now(tehran_tz)
        
        # Format as needed
        shamsi_date = now.strftime("%Y/%m/%d")
        shamsi_time = now.strftime("%H:%M:%S")
        return shamsi_date, shamsi_time
    except Exception as e:
        print(f"Error getting Shamsi datetime: {e}")
        # Return current UTC time as fallback
        now = datetime.utcnow()
        return now.strftime("%Y/%m/%d"), now.strftime("%H:%M:%S")

def main():
    try:
        # Get gold price data
        gold_data = get_gold_price()
        gold_price = gold_data["gold_price"]
        change_percentage = gold_data["change_percentage"]
        
        # Get USDT price
        usdt_price = get_usdt_price()
        
        # Get current Shamsi date and time
        shamsi_date, shamsi_time = get_shamsi_datetime()
        
        # Store data
        price_data.append({
            "Time": f"{shamsi_date} {shamsi_time}",
            "Gold Price": gold_price,
            "Gold Change": change_percentage,
            "USDT Price": usdt_price
        })

        # Print current data
        print(f"{shamsi_date} {shamsi_time} - Gold Price: {gold_price} - Change: {change_percentage} - USDT Price: {usdt_price}")

        # Send update to Telegram
        message = f"""📢 <b>بروزرسانی قیمت‌ها</b>
⏰ <b>زمان:</b> {shamsi_date} - {shamsi_time}
💰 <b>قیمت طلا:</b> {gold_price}
📈 <b> تغییرات طلا :</b> {change_percentage}
💵 <b>قیمت تتر:</b> {usdt_price}
"""
        send_telegram_message(message)

        # Save data to CSV
        df = pd.DataFrame(price_data)
        df.to_csv("market_price_updates.csv", index=False)
        print("✅ Data saved to CSV")
            
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
        # Send error message to Telegram
        send_telegram_message(f"❌ Error in price checker: {str(e)}")

# Run the main function
if __name__ == "__main__":
    main()
