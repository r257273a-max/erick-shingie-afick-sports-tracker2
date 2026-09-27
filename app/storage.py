import csv
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "players.json"
BACKUP_DIR = DATA_DIR / "backups"
EXPORT_DIR = DATA_DIR / "exports"

def ensure_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
    EXPORT_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        atomic_save({"version": 1, "players": []})

def atomic_save(payload):
    DATA_DIR.mkdir(exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="players_", suffix=".tmp", dir=DATA_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_name, DATA_FILE)
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)

def load_players():
    ensure_dirs()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload.get("players", [])
    except (json.JSONDecodeError, OSError):
        # Recovery: preserve the damaged file and start from a safe empty store.
        if DATA_FILE.exists():
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(DATA_FILE, BACKUP_DIR / f"corrupt_players_{stamp}.json")
        atomic_save({"version": 1, "players": []})
        return []

def save_players(players):
    ensure_dirs()
    if DATA_FILE.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(DATA_FILE, BACKUP_DIR / f"players_{stamp}.json")
    atomic_save({"version": 1, "players": players})

def export_json(players):
    ensure_dirs()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"players_{stamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "players": players}, f, indent=2, ensure_ascii=False)
    return path

def export_csv(players):
    ensure_dirs()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"players_{stamp}.csv"
    fields = [
        "player_id", "full_name", "age", "position", "team", "phone", "email",
        "fitness_score", "matches_played", "goals", "assists",
        "training_attendance", "contract_start", "contract_end",
        "contract_status", "medical_status", "injuries", "training_notes"
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for p in players:
            row = dict(p)
            row["injuries"] = json.dumps(row.get("injuries", []), ensure_ascii=False)
            writer.writerow(row)
    return path
