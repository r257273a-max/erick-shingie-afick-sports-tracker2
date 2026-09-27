from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any

@dataclass
class Player:
    player_id: str
    full_name: str
    age: int
    position: str
    team: str
    phone: str = ""
    email: str = ""
    fitness_score: float = 0.0
    matches_played: int = 0
    goals: int = 0
    assists: int = 0
    training_attendance: float = 0.0
    contract_start: str = ""
    contract_end: str = ""
    contract_status: str = "Active"
    medical_status: str = "Fit"
    injuries: List[Dict[str, Any]] = field(default_factory=list)
    training_notes: str = ""

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        allowed = {f.name for f in Player.__dataclass_fields__.values()}
        clean = {k: v for k, v in data.items() if k in allowed}
        return Player(**clean)
