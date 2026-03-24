import sys, os, asyncio, json, time, requests, re
from pathlib import Path

# === НАСТРОЙКИ ===
API_KEY = "YOUR_API".strip() 
WATCH_DIR = r'C:\Users\1\Downloads\Mount & Blade II Bannerlord (2022)\Mount & Blade II Bannerlord\Modules\AIInfluence\save_data\G6jPGE6CdZMJ' 

# ТВОИ АКТУАЛЬНЫЕ ПУЛЫ ГОЛОСОВ
MALE_POOL = ["C9fbwSpEaejywLWx722Z", "bqbHGIIO5oETYIqhWmfk", "m0OQuJtWCw1V23P0pQmG", "x0Y0LPGWyrjIpXHcMCxT", "Obuyk6KKzg9olSLPaCbl", "yr43K8H5LoTp6S1QFSGg", "UaYTS0wayjmO9KD1LR4R"]
FEMALE_POOL = ["dVRDrbP5ULGXB94se4KZ", "qWWAqFomnJ99VwQLREfT", "Xb7hH29zW4Wp0i8p4ZEY"]

# Если захочешь закрепить голос за конкретным лордом вручную:
# Пример: "Duvain": "ID_ГОЛОСА",
SPECIAL_VOICES = {}

# Запаски на случай 404
FALLBACK_MALE = "C9fbwSpEaejywLWx722Z" 
FALLBACK_FEMALE = "Xb7hH29zW4Wp0i8p4ZEY"
# =================

cache = {}

try:
    from playsound import playsound
except:
    print("!!! Ошибка: pip install playsound==1.2.2"); sys.exit()

def check_balance():
    url = "https://api.elevenlabs.io/v1/user/subscription"
    headers = {"xi-api-key": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            rem = data['character_limit'] - data['character_count']
            print(f"--- БАЛАНС: Осталось {rem} символов ---")
        else: print("--- Баланс не проверен (проверь API_KEY) ---")
    except: pass

def get_clean_speech(content):
    try:
        parts = content.split('Player:')
        if len(parts) < 2: return None
        text_block = parts[-1]
        match = re.search(r'\\",\s*\\"(.*?)\\",\\\"decision\\\"', text_block)
        if not match: match = re.search(r'\\":\s*\\"(.*?)\\"', text_block)
        if not match: return None
        text = match.group(1)
        if ":" in text: text = text.split(":", 1)[-1]
        text = re.sub(r'\*.*?\*', '', text)
        text = re.sub(r'[^а-яА-ЯёЁ0-9\s\.,!\?\-]', '', text)
        text = text.replace('\\\\n', ' ').replace('\\n', ' ')
        text = " ".join(text.split()).strip()
        if not any(c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for c in text.lower()): return None
        return text
    except: return None

def speak(text, gender="male", char_id="unknown"):
    time.sleep(0.5) # Пауза для стабильности записи файла
    
    # 1. Выбор ID голоса
    if char_id in SPECIAL_VOICES:
        voice_id = SPECIAL_VOICES[char_id]
    else:
        pool = FEMALE_POOL if gender == "female" else MALE_POOL
        char_seed = sum(ord(c) for c in char_id)
        voice_id = pool[char_seed % len(pool)]

    # 2. Динамический тюнинг (разные интонации для одного ID)
    char_seed = sum(ord(c) for c in char_id)
    c_stability = round(0.4 + (char_seed % 30) / 100, 2)
    c_similarity = round(0.6 + (char_seed % 20) / 100, 2)

    def send_req(vid):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
        headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": API_KEY}
        payload = {
            "text": text, "model_id": "eleven_multilingual_v2", 
            "voice_settings": {"stability": c_stability, "similarity_boost": c_similarity, "use_speaker_boost": True}
        }
        return requests.post(url, json=payload, headers=headers)

    try:
        response = send_req(voice_id)
        if response.status_code == 404:
            response = send_req(FALLBACK_FEMALE if gender == "female" else FALLBACK_MALE)

        if response.status_code == 200:
            print(f">>> ГОВОРИТ {char_id} ({gender}): {text[:55]}...")
            temp_name = f"v_{int(time.time())}.mp3"
            with open(temp_name, 'wb') as f: f.write(response.content)
            playsound(temp_name)
            time.sleep(0.5)
            try: os.remove(temp_name)
            except: pass 
        else:
            print(f"!!! API Ошибка {response.status_code}: {response.text}")
    except Exception as e:
        print(f"!!! Ошибка озвучки: {e}")

async def main():
    print("*** СКРИПТ 15.3 (STABLE & DYNAMIC) ЗАПУЩЕН ***")
    check_balance()
    
    # Инициализация 
    for p in Path(WATCH_DIR).glob("*.json"):
        try:
            with open(p, 'rb') as f:
                c = f.read().decode('utf-8', errors='ignore'); msg = get_clean_speech(c)
                if msg: cache[p.name] = msg
        except: continue
    print("Готов к работе. Кальрадия ждет!")

    while True:
        for p in Path(WATCH_DIR).glob("*.json"):
            if time.time() - os.path.getmtime(p) > 10: continue
            try:
                with open(p, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore'); msg = get_clean_speech(content)
                if msg and cache.get(p.name) != msg:
                    cache[p.name] = msg
                    with open(p, 'r', encoding='utf-8-sig', errors='ignore') as f_meta:
                        data = json.load(f_meta)
                        gender = data.get("Gender", "male").lower()
                        char_id = data.get("StringId", "unknown")
                    await asyncio.to_thread(speak, msg, gender, char_id)
            except: continue
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass