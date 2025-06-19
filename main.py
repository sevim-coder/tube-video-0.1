import os
import sys
import json
import random
import requests
from datetime import datetime
from pathlib import Path
from typing import List

import openai
from bs4 import BeautifulSoup
from pydub import AudioSegment
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

TOPICS = [
    "Kadın sağlığı",
    "İlişkilerde başarı için ipuçları",
    "Astroloji",
    "Moda, takı, alışveriş gibi güncel konular",
    "Son çıkan diziler ve filmler",
    "Kişisel bakım",
    "Dekorasyon",
]

MAGAZINES = [
    "https://www.vogue.com",
    "https://www.cosmopolitan.com",
    "https://www.elle.com",
    "https://www.glamour.com",
    "https://www.harpersbazaar.com",
    "https://www.allure.com",
    "https://www.womenshealthmag.com",
    "https://www.marieclaire.com",
]

OUTPUT_DIR = Path("output")
VISUAL_DIR = "visuals"


def prompt_topic() -> str:
    print("Lütfen bir tema seçin:")
    for idx, topic in enumerate(TOPICS, 1):
        print(f"{idx}. {topic}")
    choice = int(input("Seçiminiz: ")) - 1
    return TOPICS[choice]


def fetch_magazine_articles(theme: str) -> str:
    texts = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in MAGAZINES:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(r.text, "html.parser")
            texts.append(" ".join(p.get_text() for p in soup.find_all("p")[:5]))
        except Exception as exc:
            print(f"Hata: {url}: {exc}")
    return " ".join(texts)


def fetch_wikipedia_content(theme: str) -> str:
    api = f"https://en.wikipedia.org/api/rest_v1/page/summary/{theme}"
    try:
        r = requests.get(api, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get("extract", "")
    except Exception as exc:
        print(f"Wikipedia hatası: {exc}")
    return ""


def generate_script(theme: str, content: str) -> List[dict]:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = (
        f"Aşağıdaki içeriklere dayanarak '{theme}' temalı 1500 kelimelik bir video senaryosu oluştur. "
        "Senaryo en az 7 sahneden oluşsun. Her sahnenin başlığı ve 2-3 cümlelik açıklaması olsun. "
        "Çıktıyı JSON listesi olarak döndür. Örnek: [{'title': '...', 'content': '...'}]"
    )
    messages = [
        {"role": "system", "content": "You are a creative writer."},
        {"role": "user", "content": prompt + "\n" + content},
    ]
    resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    text = resp.choices[0].message.content
    try:
        scenes = json.loads(text)
    except json.JSONDecodeError:
        scenes = []
    return scenes


def extract_keywords(text: str) -> List[str]:
    words = [w.strip(".,!?") for w in text.split()]
    freq = {}
    for w in words:
        if len(w) > 4:
            freq[w.lower()] = freq.get(w.lower(), 0) + 1
    sorted_words = sorted(freq, key=freq.get, reverse=True)
    return sorted_words[:5]


def search_image(api_key: str, query: str, api: str) -> List[str]:
    if api == "pexels":
        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=3"
        r = requests.get(url, headers=headers, timeout=5)
        return [p["src"]["large"] for p in r.json().get("photos", [])]
    elif api == "unsplash":
        url = f"https://api.unsplash.com/search/photos?query={query}&per_page=3&client_id={api_key}"
        r = requests.get(url, timeout=5)
        return [p["urls"]["regular"] for p in r.json().get("results", [])]
    elif api == "pixabay":
        url = f"https://pixabay.com/api/?key={api_key}&q={query}&per_page=3"
        r = requests.get(url, timeout=5)
        return [h["largeImageURL"] for h in r.json().get("hits", [])]
    return []


def download_images(keywords: List[str], scene_no: int, out_dir: Path) -> List[Path]:
    apis = [
        ("pexels", os.getenv("PEXELS_API_KEY")),
        ("unsplash", os.getenv("UNSPLASH_ACCESS_KEY")),
        ("pixabay", os.getenv("PIXABAY_API_KEY")),
    ]
    paths = []
    for keyword in keywords:
        success = False
        for name, key in apis:
            if not key:
                continue
            try:
                urls = search_image(key, keyword, name)
                if urls:
                    for idx, url in enumerate(urls):
                        r = requests.get(url, timeout=5)
                        fname = out_dir / f"scene_{scene_no}_{idx}.jpg"
                        with open(fname, "wb") as f:
                            f.write(r.content)
                        paths.append(fname)
                    success = True
                    break
            except Exception:
                continue
        if success:
            break
    return paths


def tts_synthesize(text: str, out_path: Path) -> None:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    resp = openai.audio.speech.create(model="tts-1", voice="nova", input=text)
    with open(out_path, "wb") as f:
        f.write(resp.content)


def choose_music(used: List[str]) -> Path:
    music_dir = Path("assets/music")
    choices = [p for p in music_dir.glob("*.mp3") if p.name not in used]
    if not choices:
        choices = list(music_dir.glob("*.mp3"))
    return random.choice(choices)


def loop_music(music_path: Path, duration: int, out_path: Path) -> None:
    music = AudioSegment.from_file(music_path)
    looped = (music * (duration // len(music) + 1))[:duration]
    looped.export(out_path, format="mp3")


def assemble_video(scene_image_paths: List[List[Path]], narration: Path, music: Path, out_path: Path) -> None:
    narration_clip = AudioFileClip(str(narration))
    music_clip = AudioFileClip(str(music)).volumex(0.2)
    audio = narration_clip.audio.set_fps(44100).fx(lambda c: c.volumex(1.0))
    audio = audio.set_duration(narration_clip.duration)
    final_audio = audio.set_audio(music_clip)

    clips = []
    scene_duration = narration_clip.duration / len(scene_image_paths)
    for paths in scene_image_paths:
        duration_per_img = scene_duration / len(paths)
        for p in paths:
            clip = ImageClip(str(p)).set_duration(duration_per_img).resize((1920, 1080))
            clips.append(clip)
    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(final_audio)
    video.write_videofile(str(out_path), fps=30)


def main():
    topic = prompt_topic()
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_base = OUTPUT_DIR / topic / now
    visual_dir = out_base / VISUAL_DIR
    visual_dir.mkdir(parents=True, exist_ok=True)

    content = fetch_magazine_articles(topic) + fetch_wikipedia_content(topic)
    scenes = generate_script(topic, content)
    script_path = out_base / "script.txt"
    with open(script_path, "w", encoding="utf-8") as f:
        for s in scenes:
            f.write(f"{s['title']}\n{s['content']}\n\n")

    scene_image_paths = []
    narration_parts = []
    for idx, scene in enumerate(scenes, 1):
        keywords = extract_keywords(scene["content"])
        paths = download_images(keywords, idx, visual_dir)
        scene_image_paths.append(paths)
        audio_path = out_base / f"scene_{idx}.mp3"
        tts_synthesize(scene["content"], audio_path)
        narration_parts.append(AudioSegment.from_file(audio_path))
        narration_parts.append(AudioSegment.silent(duration=500))

    narration = sum(narration_parts)
    narration_path = out_base / "narration.mp3"
    narration.export(narration_path, format="mp3")

    log_path = out_base / "process.log"
    with open(log_path, "w") as log:
        json.dump({"scenes": scenes, "images": [[str(p) for p in ps] for ps in scene_image_paths]}, log, indent=2)

    used_music = []
    music_path = choose_music(used_music)
    background_path = out_base / "background.mp3"
    loop_music(music_path, int(narration.duration_seconds * 1000), background_path)

    video_path = out_base / "video.mp4"
    assemble_video(scene_image_paths, narration_path, background_path, video_path)

    print(f"Video hazır: {video_path}")


if __name__ == "__main__":
    main()
