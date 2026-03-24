import sys, os, asyncio, json, time, re, hashlib
from pathlib import Path
import edge_tts

# === НАСТРОЙКИ ===
WATCH_DIR = r'C:\Users\1\Downloads\Mount & Blade II Bannerlord (2022)\Mount & Blade II Bannerlord\Modules\AIInfluence\save_data\G6jPGE6CdZMJ' 

MALE_BASES = ["ru-RU-DmitryNeural", "ru-RU-YuryNeural", "en-US-AndrewMultilingualNeural", "en-AU-WilliamMultilingualNeural"]
FEMALE_BASES = ["ru-RU-SvetlanaNeural", "ru-RU-EkaterinaNeural", "en-US-AvaMultilingualNeural", "en-US-EmmaMultilingualNeural"]

# Сетка тюнинга - расширил для максимального разнообразия
PITCHES = ["-12Hz", "-10Hz", "-7Hz", "-4Hz", "-2Hz", "+0Hz", "+2Hz", "+4Hz", "+7Hz", "+10Hz", "+12Hz"] 
RATES = ["-10%", "-7%", "-4%", "+0%", "+4%", "+7%", "+10%"]

cache = {}
is_speaking = False

try:
    from playsound import playsound
except:
    print("!!! Ошибка: pip install playsound==1.2.2"); sys.exit()

def get_clean_speech(content):
    try:
        parts = content.split('Player:')
        text_block = parts[-1] if len(parts) > 1 else content
        
        match = re.search(r'\\",\s*\\"(.*?)\\",\\\"decision\\\"', text_block)
        if not match: match = re.search(r'\\":\s*\\"(.*?)\\"', text_block)
        if not match: return None
        
        text = match.group(1)
        if ":" in text[:30]: text = text.split(":", 1)[-1]
        
        text = re.sub(r'\*.*?\*', '', text) 
        
        # Полная очистка от nnn и мусора
        text = text.replace('\\\\n', ' ').replace('\\n', ' ').replace('\\r', ' ')
        text = re.sub(r'[^а-яА-ЯёЁa-zA-Z0-9\s\.,!\?\-]', '', text)
        
        text = " ".join(text.split()).strip()
        return text if len(text) > 2 else None
    except: return None

async def speak(text, gender="male", char_id="unknown"):
    global is_speaking
    if is_speaking: return
    is_speaking = True
    
    # --- ГЕНЕРАЦИЯ УНИКАЛЬНОГО СИДА ЧЕРЕЗ ХЭШ ---
    hash_obj = hashlib.md5(char_id.encode())
    seed = int(hash_obj.hexdigest(), 16)
    
    # Выбор голоса
    pool = FEMALE_BASES if gender == "female" else MALE_BASES
    voice = pool[seed % len(pool)]
    
    # Выбор герцовки и скорости (используем разные части хэша для независимости)
    pitch = PITCHES[(seed >> 4) % len(PITCHES)]
    rate = RATES[(seed >> 8) % len(RATES)]
    
    # Естественные паузы
    clean_text = text.replace('.', '... ').replace('!', '! ').replace('?', '? ')

    output_file = f"v_{int(time.time())}.mp3"
    
    try:
        communicate = edge_tts.Communicate(clean_text, voice, rate=rate, pitch=pitch)
        await communicate.save(output_file)
        
        print(f">>> [NPC: {char_id}] | Голос: {voice} | Pitch: {pitch} | Rate: {rate}")
        playsound(output_file)
        time.sleep(0.4)
    except Exception as e:
        print(f"!!! Ошибка: {e}")
    finally:
        is_speaking = False
        if os.path.exists(output_file):
            try: os.remove(output_file)
            except: pass

async def main():
    print("\n" + "="*65)
    print("   *** CALRADIA VOICES: RANDOMIZED EDITION 35.0 ***")
    print("   UNIQUE PITCH | NO NNN | MULTILINGUAL ACCENTS")
    print("="*65)
    
    for p in Path(WATCH_DIR).glob("*.json"):
        try:
            with open(p, 'r', encoding='utf-8-sig', errors='ignore') as f:
                msg = get_clean_speech(f.read())
                if msg: cache[p.name] = msg
        except: continue

    while True:
        for p in Path(WATCH_DIR).glob("*.json"):
            if time.time() - os.path.getmtime(p) > 5: continue
            try:
                with open(p, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    content = f.read()
                    msg = get_clean_speech(content)
                
                if msg and cache.get(p.name) != msg:
                    cache[p.name] = msg
                    data = json.loads(content)
                    gender = str(data.get("Gender", "male")).lower()
                    char_id = str(data.get("StringId", "unknown"))
                    await speak(msg, gender, char_id)
            except: continue
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Озвучка остановлена.")