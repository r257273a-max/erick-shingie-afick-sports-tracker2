def efficiency(player):
    matches = max(int(player.get("matches_played", 0)), 1)
    goals = int(player.get("goals", 0))
    assists = int(player.get("assists", 0))
    fitness = float(player.get("fitness_score", 0))
    attendance = float(player.get("training_attendance", 0))
    # Transparent 0-100 local efficiency index.
    contribution = min(((goals * 3 + assists * 2) / matches) * 10, 50)
    fitness_component = min(max(fitness, 0), 100) * 0.35
    attendance_component = min(max(attendance, 0), 100) * 0.15
    return round(min(contribution + fitness_component + attendance_component, 100), 2)

def performance_summary(player):
    score = efficiency(player)
    injuries = player.get("injuries", [])
    return (
        f"PLAYER PERFORMANCE SUMMARY\n"
        f"Name: {player.get('full_name','')}\n"
        f"Player ID: {player.get('player_id','')}\n"
        f"Position: {player.get('position','')}\n"
        f"Team: {player.get('team','')}\n"
        f"Matches: {player.get('matches_played',0)}\n"
        f"Goals: {player.get('goals',0)}\n"
        f"Assists: {player.get('assists',0)}\n"
        f"Fitness Score: {player.get('fitness_score',0)} / 100\n"
        f"Training Attendance: {player.get('training_attendance',0)}%\n"
        f"Medical Status: {player.get('medical_status','Fit')}\n"
        f"Injury Records: {len(injuries)}\n"
        f"Efficiency Index: {score} / 100\n"
    )
