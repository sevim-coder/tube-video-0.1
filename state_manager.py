import json
from pathlib import Path
from typing import Dict, Any

STATE_FILE_NAME = "session_state.json"

def get_initial_state(topic: str, session_dir: Path) -> Dict[str, Any]:
    """Yeni bir proje için başlangıç durumunu oluşturur."""
    return {
        "topic": topic,
        "session_dir": str(session_dir),
        "visuals_dir": str(session_dir / "visuals"),
        "script_path": str(session_dir / "script.json"),
        "final_video_path": str(session_dir / "final_video.mp4"),
        "steps_completed": {
            "script": False,
            "assets": False,
            "video": False,
        },
        "scenes": [],
        "assets": {
            "audio": [],
            "visuals": [],
        }
    }

def save_state(state: Dict[str, Any]):
    """Mevcut durumu dosyaya kaydeder."""
    session_dir = Path(state["session_dir"])
    state_path = session_dir / STATE_FILE_NAME
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)
    print(f"💾 İlerleme kaydedildi: {state_path.name}")

def load_state(session_dir: Path) -> Dict[str, Any] | None:
    """Mevcut durumu dosyadan yükler."""
    state_path = session_dir / STATE_FILE_NAME
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                print(f"✅ Kayıtlı oturum bulundu, yükleniyor: {state_path}")
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            print("⚠️ Uyarı: Kayıt dosyası bozuk, yeni bir oturum başlatılıyor.")
            return None
    return None