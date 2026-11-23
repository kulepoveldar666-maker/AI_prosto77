import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# 3 источника новостей про ИИ
VERGE_AI_URL = "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
VENTUREBEAT_AI_URL = "https://venturebeat.com/category/ai/feed/"
MIT_AI_URL = "https://www.technologyreview.com/topic/artificial-intelligence/feed/"

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
            
            # Поиск картинки
            image = "Картинка не найдена в RSS"
            img_match = re.search(r'<img[^>]+src="([^"]+)"', description)
            if img_match:
                image = img_match.group(1)
            else:
                enclosure = item.find("enclosure")
                if enclosure is not None and enclosure.get("url"):
                    image = enclosure.get("url")
                else:
                    media = item.find("{http://search.yahoo.com/mrss/}content")
                    if media is not None and media.get("url"):
                        image = media.get("url")
            
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
    # ВСТАВЬ СЮДА СВОЙ ТОКЕН И ID КАНАЛА
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
    print("=== Начинаем сбор 3 новостей про ИИ ===")
    
    all_items = []
    all_items.extend(fetch_rss(VERGE_AI_URL))
    all_items.extend(fetch_rss(VENTUREBEAT_AI_URL))
    all_items.extend(fetch_rss(MIT_AI_URL))
    
    if not all_items:
        print("Свежих новостей не найдено.")
        return

    # Берем 3 самые свежие новости из общего списка
    selected = all_items[:3]

    for it in selected:
        print(f"Отправляем: {it['title']}")
        
        title_ru = translate_text(it['title'])
        desc_ru = translate_text(it['description'])
        
        send_to_telegram("Новости ИИ", it, title_ru, desc_ru)
        time.sleep(3)

if __name__ == "__main__":
    main()
