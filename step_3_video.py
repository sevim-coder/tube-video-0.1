from moviepy.editor import *
from pathlib import Path
from typing import Dict, Any
import random

from config import print_step, MUSIC_DIR

def run_video_assembly(state: Dict[str, Any]) -> Dict[str, Any]:
    """Final videoyu birleştirme adımını çalıştırır."""
    print_step("AŞAMA 3: FİNAL VİDEOYU BİRLEŞTİRME")
    
    final_clips = []
    
    for i, scene in enumerate(state["scenes"]):
        scene_num = i + 1
        scene_audio_path = state["assets"]["audio"][i]
        scene_visual_paths = state["assets"]["visuals"][i]

        if not Path(scene_audio_path).exists() or not scene_visual_paths:
            print(f"⚠️ Uyarı: Sahne {scene_num} için ses veya görsel eksik, atlanıyor.")
            continue
            
        try:
            audio_clip = AudioFileClip(scene_audio_path)
            if audio_clip.duration == 0:
                print(f"⚠️ Uyarı: Sahne {scene_num} ses dosyası boş, atlanıyor.")
                continue

            scene_duration = audio_clip.duration
            duration_per_image = scene_duration / len(scene_visual_paths)
            
            image_clips = []
            for img_path_str in scene_visual_paths:
                img_path = Path(img_path_str)
                if not img_path.exists():
                    print(f"⚠️ Uyarı: Görsel dosyası bulunamadı, atlanıyor: {img_path.name}")
                    continue
                
                clip = (ImageClip(str(img_path))
                        .set_duration(duration_per_image)
                        .set_position("center")
                        .resize(height=1080)
                        # Ken Burns Efekti (Hafif Zoom)
                        .fx(vfx.resize, lambda t: 1 + 0.02 * t))
                image_clips.append(clip)
            
            if not image_clips:
                print(f"⚠️ Uyarı: Sahne {scene_num} için geçerli görsel bulunamadı, atlanıyor.")
                continue

            scene_video = concatenate_videoclips(image_clips, method="compose").set_audio(audio_clip)
            final_clips.append(scene_video)

        except Exception as e:
            print(f"❌ HATA: Sahne {scene_num} işlenirken hata oluştu: {e}")
            continue

    if not final_clips:
        raise Exception("Birleştirilecek hiçbir geçerli sahne oluşturulamadı.")

    final_video = concatenate_videoclips(final_clips)
    
    # Arkaplan Müziği Ekle
    music_files = list(MUSIC_DIR.glob("*.mp3"))
    if music_files:
        music_path = random.choice(music_files)
        print(f"🎵 Arkaplan müziği ekleniyor: {music_path.name}")
        music = AudioFileClip(str(music_path)).volumex(0.1)
        final_video.audio = CompositeAudioClip([final_video.audio, music.fx(vfx.loop, duration=final_video.duration)])

    print("✅ Video render ediliyor... Bu işlem uzun sürebilir.")
    final_video.write_videofile(
    state["final_video_path"],
    codec="libx264",
    audio_codec="aac",
    temp_audiofile="temp-audio.m4a",
    remove_temp=True,
    fps=24,
    preset="medium",
    bitrate="5000k",
    ffmpeg_params=["-pix_fmt", "yuv420p"]  # eski pix_fmt’nin yerine
)

    
    state["steps_completed"]["video"] = True
    print(f"\n🎉 VİDEO TAMAMLANDI: {state['final_video_path']}")
    return state