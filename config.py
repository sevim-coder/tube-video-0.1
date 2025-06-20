import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

# --- TEMEL KONFİGÜRASYON ---
TOPICS = [
    "Kadın sağlığı ve zindelik",
    "İlişkilerde başarı için ipuçları",
    "Astroloji ve burç yorumları",
    "Moda ve güzellik trendleri",
    "Popüler kültür: Dizi ve film analizleri",
    "Kişisel gelişim ve motivasyon",
    "Ev dekorasyonu ve kendin yap (DIY) fikirleri",
]

# --- DİZİN ve DOSYA YOLLARI ---
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
VISUAL_DIR_NAME = "visuals"

# --- API ANAHTARLARI (.env dosyasından okunur) ---
API_KEYS = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "PEXELS_API_KEY": os.getenv("PEXELS_API_KEY"),
    "UNSPLASH_ACCESS_KEY": os.getenv("UNSPLASH_ACCESS_KEY"),
}

# --- YARDIMCI FONKSİYONLAR ---
def print_step(message: str):
    """Konsola biçimli bir başlık yazdırır."""
    print(f"\n{'='*60}\n➡️  {message.upper()}\n{'='*60}")

def check_api_keys():
    """Gerekli API anahtarlarının mevcut olup olmadığını kontrol eder."""
    if not API_KEYS["OPENAI_API_KEY"]:
        print("❌ HATA: .env dosyasında OPENAI_API_KEY bulunamadı veya ayarlanmadı.")
        return False
    if not any([API_KEYS["PEXELS_API_KEY"], API_KEYS["UNSPLASH_ACCESS_KEY"]]):
        print("❌ HATA: .env dosyasında en az bir görsel API anahtarı (PEXELS veya UNSPLASH) gereklidir.")
        return False
    print("✅ Tüm gerekli API anahtarları bulundu.")
    return True