import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Источники
TECHCRUNCH_AI_URL = "https://techcrunch.com/category/artificial-intelligence/feed/"
NAKED_SCIENCE_AI_URL = "https://naked-science.ru/rubric/artificial-intelligence/feed"

def translate_text(text):
    if not text:
        return text
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": "en|ru"}
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

def send_to_telegram(category, it, title_ru, desc_ru):
    # ВСТАВЬ СЮДА ТОКЕН И ID КАНАЛА
    token = "9095973216:AAEQWXbCXqDopIuVy0cUP_d8AxS4saY7HPw"
    chat_id = "-1003775176290" 
    
    text = (
        f"🤖 **{category}**\n\n"
        f"🔥 **{title_ru}**\n\n"
        f"📝 {desc_ru}..."
    )
    
    if it['image'] and "http" in it['image']:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": it['image'],
            "caption": text,
            "parse_mode": "Markdown"
        }
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
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
        # 08:00 МСК - TechCrunch AI
        category = "Новости ИИ"
        items = fetch_rss(TECHCRUNCH_AI_URL)
        if items:
            it = items[0]
            print(f"Отправляем: {it['title']}")
            title_ru = translate_text(it['title'])
            desc_ru = translate_text(it['description'])
            send_to_telegram(category, it, title_ru, desc_ru)
            
    elif hour == 9:
        # 12:00 МСК - Naked Science AI
        category = "Наука и ИИ"
        items = fetch_rss(NAKED_SCIENCE_AI_URL)
        if items:
            it = items[0]
            print(f"Отправляем: {it['title']}")
            # Naked Science на русском, переводить не нужно
            send_to_telegram(category, it, it['title'], it['description'])
            
    elif hour == 14:
        # 17:00 МСК - TechCrunch AI
        category = "Новости ИИ"
        items = fetch_rss(TECHCRUNCH_AI_URL)
        if items and len(items) > 1:
            it = items[1]
            print(f"Отправляем: {it['title']}")
            title_ru = translate_text(it['title'])
            desc_ru = translate_text(it['description'])
            send_to_telegram(category, it, title_ru, desc_ru)
            
    elif hour == 16:
        # 19:00 МСК - Naked Science AI
        category = "Наука и ИИ"
        items = fetch_rss(NAKED_SCIENCE_AI_URL)
        if items and len(items) > 1:
            it = items[1]
            print(f"Отправляем: {it['title']}")
            send_to_telegram(category, it, it['title'], it['description'])
            
    else:
        print(f"Запуск в {hour} UTC не соответствует расписанию. Ждем следующего.")

if __name__ == "__main__":
    main()
