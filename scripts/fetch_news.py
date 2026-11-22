import os
import re
import time
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Источники
ANEKDOT_URL = "https://www.anekdot.ru/rss/export_j.xml"
ITHOME_URL = "https://www.ithome.com/rss/"

# Ключевые слова для поиска смешного на IT之家 (роботы, курьёзы, ИИ)
HUMOR_KEYWORDS = ["搞笑", "奇葩", "翻车", "乌龙", "笑话", "趣闻", "AI", "机器人", "人工智能"]

def translate_text(text):
    if not text:
        return text
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": "zh-CN|ru"} # Переводим с китайского
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data['responseData']['translatedText']
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return text

def fetch_rss(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = []
        for item in root.findall(".//item"):
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            description = item.findtext("description") or ""
            
            img_match = re.search(r'<img[^>]+src="([^"]+)"', description)
            image = img_match.group(1) if img_match else "Картинка не найдена в RSS"
            
            clean_desc = re.sub(r"<[^>]+>", "", description).strip()[:300]
            
            items.append({
                "title": title.strip(),
                "link": link.strip(),
                "description": clean_desc,
                "image": image,
            })
        return items
    except Exception as e:
        print(f"Ошибка загрузки {url}: {e}")
        return []

def send_to_telegram(category, text_to_send, image_url=None):
    # ВСТАВЬ СЮДА СВОЙ ТОКЕН И ID КАНАЛА
    token = "9095973216:AAEQWXbCXqDopIuVy0cUP_d8AxS4saY7HPw"
    chat_id = "-1003775176290" 
    
    emoji = "😄" if "Анекдот" in category else "🤖"
    
    full_text = f"{emoji} **{category}**\n\n{text_to_send}"
    
    if image_url and "http" in image_url:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": image_url,
            "caption": full_text,
            "parse_mode": "Markdown"
        }
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": full_text,
            "parse_mode": "Markdown"
        }
        
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Пост успешно отправлен!")
    else:
        print(f"Ошибка отправки: {response.text}")

def main():
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    
    print(f"=== Запуск в {hour} UTC ===")
    
    if True:
        # 08:00 МСК - Анекдот
        items = fetch_rss(ANEKDOT_URL)
        if items:
            it = random.choice(items[:5]) # Берем случайный из 5 свежих
            text = f"{it['title']}\n\n{it['description']}"
            send_to_telegram("Анекдот дня", text)
            
    elif hour == 9:
        # 12:00 МСК - Смешная новость про ИИ
        items = fetch_rss(ITHOME_URL)
        humor_items = [i for i in items if any(k in (i['title'] + i['description']).lower() for k in HUMOR_KEYWORDS)]
        if humor_items:
            it = humor_items[0]
            print(f"Нашли юмор: {it['title']}")
            text = translate_text(it['description'])
            send_to_telegram("Курьёзы технологий", text, it['image'])
            
    elif hour == 14:
        # 17:00 МСК - Еще один анекдот
        items = fetch_rss(ANEKDOT_URL)
        if items and len(items) > 5:
            it = random.choice(items[5:10]) # Берем из следующей партии
            text = f"{it['title']}\n\n{it['description']}"
            send_to_telegram("Анекдот", text)
            
    elif hour == 16:
        # 19:00 МСК - Смешная новость про ИИ
        items = fetch_rss(ITHOME_URL)
        humor_items = [i for i in items if any(k in (i['title'] + i['description']).lower() for k in HUMOR_KEYWORDS)]
        if humor_items and len(humor_items) > 1:
            it = humor_items[1]
            print(f"Нашли юмор: {it['title']}")
            text = translate_text(it['description'])
            send_to_telegram("Курьёзы технологий", text, it['image'])
            
    else:
        print(f"Запуск в {hour} UTC не соответствует расписанию. Ждем следующего.")

if __name__ == "__main__":
    main()
