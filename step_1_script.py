import openai
import json
from typing import Dict, Any

from config import print_step, API_KEYS

def _generate_script_from_ai(topic: str) -> list:
    """Yapay zeka kullanarak bir video senaryosu oluşturur."""
    print("🤖 Yapay zeka ile video senaryosu oluşturuluyor...")
    client = openai.OpenAI(api_key=API_KEYS["OPENAI_API_KEY"])
    
    # --- GÜNCELLENMİŞ PROMPT ---
    # Artık doğrudan {"scenes": [...]} formatında bir obje istiyoruz.
    prompt = f"""
    Konu: '{topic}'

    Bu konu hakkında detaylı ve uzun bir YouTube videosu için senaryo oluştur.
    - Senaryo, toplamda yaklaşık 10 dakika uzunluğunda olacak şekilde **15 ila 20 sahneden** oluşmalıdır.
    - Her sahnenin "narration" (anlatım metni) bölümü, konuyu derinlemesine işleyen, ** 90 civarı kelimeden** oluşmalıdır.
    - Her sahne bir "title" (başlık) ve "narration" (anlatım metni) içermelidir.
    - Anlatım metinleri akıcı ve ilgi çekici olmalıdır.
    - Çıktı, içinde "scenes" adında bir anahtar (key) bulunan ve bu anahtarın değerinin sahne listesi olduğu, 
      tek bir JSON objesi formatında olmalıdır. Başka hiçbir metin ekleme.

    Örnek Format:
    {{
      "scenes": [
        {{
          "title": "Sahne 1 Başlığı",
          "narration": "Sahne 1 için oldukça detaylı ve uzun anlatım metni..."
        }}
      ]
    }}
    """
    
    text_response = "" # Hata durumunda loglamak için tanımlıyoruz
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a creative YouTube scriptwriter who outputs a single JSON object with a 'scenes' key containing the scene list."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"} # Bu parametre artık prompt ile uyumlu
        )
        text_response = response.choices[0].message.content
        
        # --- GÜNCELLENMİŞ PARSING MANTIĞI ---
        # Artık doğrudan 'scenes' anahtarını arıyoruz.
        data = json.loads(text_response)
        
        if 'scenes' not in data or not isinstance(data['scenes'], list):
            raise ValueError("Gelen JSON formatı beklenen gibi değil. 'scenes' anahtarı bulunamadı veya bir liste değil.")

        scenes = data['scenes']
        if not scenes:
             raise ValueError("Yapay zeka boş bir sahne listesi döndürdü.")

        print(f"✅ Senaryo oluşturuldu: {len(scenes)} sahne.")
        return scenes
        
    except Exception as e:
        print(f"❌ HATA: Senaryo üretilirken veya JSON ayrıştırılırken hata oluştu: {e}")
        # Hata anında AI'dan gelen ham cevabı yazdırarak sorunu anlamayı kolaylaştır.
        if text_response:
            print("\n--- Hatalı Ham Yapay Zeka Cevabı ---\n")
            print(text_response)
            print("\n-------------------------------------\n")
        return []

def run_script_generation(state: Dict[str, Any]) -> Dict[str, Any]:
    """Senaryo üretim adımını çalıştırır."""
    print_step("AŞAMA 1: SENARYO ÜRETİMİ")
    
    scenes = _generate_script_from_ai(state["topic"])
    if not scenes:
        raise Exception("Senaryo üretilemedi, işlem durduruldu.")
        
    state["scenes"] = scenes
    
    with open(state["script_path"], "w", encoding="utf-8") as f:
        json.dump(scenes, f, ensure_ascii=False, indent=4)
        
    state["steps_completed"]["script"] = True
    return state