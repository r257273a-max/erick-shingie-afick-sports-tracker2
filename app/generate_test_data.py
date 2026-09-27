import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import storage

players = []
positions = ["Goalkeeper","Defender","Midfielder","Forward"]
for i in range(1, 501):
    players.append({
        "player_id": f"P{i:04d}", "full_name": f"Test Player {i}", "age": 18 + i % 15,
        "position": positions[i % 4], "team": "Test Team", "phone": "", "email": "",
        "fitness_score": float(50 + i % 51), "matches_played": i % 100,
        "goals": i % 25, "assists": i % 30, "training_attendance": float(60 + i % 41),
        "contract_start": "2026-01-01", "contract_end": "2028-12-31",
        "contract_status": "Active", "medical_status": "Fit", "injuries": [],
        "training_notes": "Generated stress-test record."
    })
storage.save_players(players)
print("Generated 500 test player records.")
