import os
import re
import time
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

VERGE_AI_URL = "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
VENTUREBEAT_AI_URL = "https://venturebeat.com/category/ai/feed/"
MIT_AI_URL = "https://www.technologyreview.com/topic/artificial-intelligence/feed/"

SENT_FILE = "sent.json"
token = ("9095973216:AAEQWXbCXqDopIuVy0cUP_d8AxS4saY7HPw")
chat_id = ("-1003775176290")

# ⚠️ Укажи свой email здесь (не обязательно, но повышает лимит до 50k)
MYMEMORY_EMAIL = os.getenv("MYMEMORY_EMAIL", "")

def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_sent(sent):
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent)[-200:], f)

def translate_text(text):
    if not text:
        return text
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text[:1000], "langpair": "en|ru"}
        # Если email указан, лимит вырастет до 50 000 символов в день
        if MYMEMORY_EMAIL:
            params["de"] = MYMEMORY_EMAIL
        
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        translated = data.get('responseData', {}).get('translatedText', '')
        
        # ⚠️ КЛЮЧЕВАЯ ПРОВЕРКА: MyMemory присылает предупреждение как обычный текст.
        # Если видим WARNING или quota — считаем перевод неудачным.
        if "WARNING" in translated.upper() or "QUOTA" in translated.upper() or "MYMEMORY" in translated.upper():
            print(f"⚠️ Лимит MyMemory исчерпан. Ответ: {translated[:100]}...")
            return None  # Возвращаем None, чтобы сигнализировать об ошибке
        
        return translated
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return None

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
            
            image = None
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
    if not token or not chat_id:
        print("ОШИБКА: не заданы TG_TOKEN или TG_CHAT_ID")
        return False
        
    text = f"🤖 **{category}**\n\n🔥 **{title_ru}**\n\n📝 {desc_ru}..."
    
    if it['image'] and "http" in it['image']:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": it['image'], "caption": text, "parse_mode": "Markdown"}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Пост успешно отправлен!")
        return True
    else:
        print(f"Ошибка отправки: {response.text}")
        return False

def main():
    print("=== Сбор 1 новости про ИИ ===")
    sent = load_sent()
    
    all_items = []
    all_items.extend(fetch_rss(VERGE_AI_URL))
    all_items.extend(fetch_rss(VENTUREBEAT_AI_URL))
    all_items.extend(fetch_rss(MIT_AI_URL))

    fresh = [i for i in all_items if i['link'] not in sent]

    if not fresh:
        print("Все новости уже отправлены.")
        return

    it = fresh[0]
    print(f"Отправляем: {it['title']}")
    
    # Переводим заголовок и описание
    title_ru = translate_text(it['title'])
    desc_ru = translate_text(it['description'])
    
    # ⚠️ Если перевод вернул None (лимит), НЕ отправляем пост, чтобы не спамить предупреждением
    if title_ru is None or desc_ru is None:
        print("❌ Пропускаем новость: не удалось перевести из-за лимита API. Ссылка не сохранена, попробуем в следующий раз.")
        return
    
    success = send_to_telegram("Новости ИИ", it, title_ru, desc_ru)
    
    if success:
        sent.add(it['link'])
        save_sent(sent)
        print("Ссылка сохранена в sent.json")

if __name__ == "__main__":
    main()
