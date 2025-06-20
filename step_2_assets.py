import openai
import requests
from pathlib import Path
from typing import Dict, Any, List

from config import print_step, API_KEYS

# --- GÖRSEL ARAMA FONKSİYONLARI ---
def _search_unsplash(query: str, count: int) -> List[str]:
    """Unsplash üzerinden görsel arar ve URL'lerini döndürür."""
    if not API_KEYS["UNSPLASH_ACCESS_KEY"]: return []
    print(f"      -> '{query}' için Unsplash'te aranıyor...")
    try:
        headers = {"Authorization": f"Client-ID {API_KEYS['UNSPLASH_ACCESS_KEY']}"}
        params = {"query": query, "per_page": count, "orientation": "landscape"}
        response = requests.get("https://api.unsplash.com/search/photos", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        return [photo["urls"]["regular"] for photo in results]
    except Exception as e:
        print(f"      - Unsplash API Hatası: {e}")
        return []

def _search_pexels(query: str, count: int) -> List[str]:
    """Pexels üzerinden görsel arar ve URL'lerini döndürür."""
    if not API_KEYS["PEXELS_API_KEY"]: return []
    print(f"      -> '{query}' için Pexels'da aranıyor...")
    try:
        headers = {"Authorization": API_KEYS["PEXELS_API_KEY"]}
        params = {"query": query, "per_page": count, "orientation": "landscape"}
        response = requests.get("https://api.pexels.com/v1/search", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json().get("photos", [])
        return [photo["src"]["large"] for photo in results]
    except Exception as e:
        print(f"      - Pexels API Hatası: {e}")
        return []

def _get_images(query: str, count: int) -> List[str]:
    """Görsel arama servislerini sırayla deneyerek görsel URL'leri bulur."""
    urls = _search_unsplash(query, count)
    if not urls:
        print("      - Unsplash'te sonuç bulunamadı, Pexels deniyor.")
        urls = _search_pexels(query, count)
    
    if not urls:
        print(f"      - UYARI: '{query}' için hiçbir görsel bulunamadı.")
    
    return urls[:count] # Her zaman istenen sayıda URL döndür

# --- DİĞER YARDIMCI FONKSİYONLAR ---
def _download_image(url: str, path: Path):
    """Verilen URL'den bir görsel indirir."""
    try:
        print(f"      -> İndiriliyor: {path.name}") # EKLENDİ
        response = requests.get(url, stream=True, timeout=20)
        response.raise_for_status()
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        print(f"      - İndirme hatası: {url} - {e}")

def _text_to_speech(text: str, output_path: Path):
    """Verilen metni seslendirir ve dosyaya kaydeder."""
    print(f"      -> Seslendiriliyor: \"{text[:40]}...\"")
    client = openai.OpenAI(api_key=API_KEYS["OPENAI_API_KEY"])
    try:
        response = client.audio.speech.create(model="tts-1", voice="nova", input=text)
        response.stream_to_file(output_path)
    except Exception as e:
        print(f"      - TTS Hatası: {e}")

# --- ANA FONKSİYON ---
def run_asset_generation(state: Dict[str, Any]) -> Dict[str, Any]:
    """Görsel ve ses varlıklarını üretme adımını çalıştırır."""
    print_step("AŞAMA 2: GÖRSEL VE SES DOSYALARINI ÜRETME")
    visuals_dir = Path(state["visuals_dir"])
    visuals_dir.mkdir(exist_ok=True)
    
    all_audio_paths = []
    all_visual_paths = []

    for i, scene in enumerate(state["scenes"]):
        scene_num = i + 1
        print(f"\n--- Sahne {scene_num}/{len(state['scenes'])} işleniyor: {scene['title']} ---")
        
        # --- Seslendirme ---
        audio_path = visuals_dir / f"scene_{scene_num}_audio.mp3"
        if not audio_path.exists():
            _text_to_speech(scene["narration"], audio_path)
        else:
            print("      -> Ses dosyası zaten mevcut, atlanıyor.")
        all_audio_paths.append(str(audio_path))

        # --- Görsel İndirme ---
        image_count_needed = 3
        existing_images = sorted(list(visuals_dir.glob(f"scene_{scene_num}_img_*.jpg")))
        
        scene_visual_paths = [str(p) for p in existing_images]
        if len(scene_visual_paths) >= image_count_needed:
            print("      -> Görseller zaten mevcut, atlanıyor.")
        else:
            search_query = scene['title']
            image_urls = _get_images(search_query, image_count_needed)
            
            for j, url in enumerate(image_urls):
                img_path = visuals_dir / f"scene_{scene_num}_img_{j+1}.jpg"
                if not img_path.exists():
                    _download_image(url, img_path)
                scene_visual_paths.append(str(img_path))
        
        all_visual_paths.append(scene_visual_paths)

    state["assets"]["audio"] = all_audio_paths
    state["assets"]["visuals"] = all_visual_paths
    state["steps_completed"]["assets"] = True
    return state