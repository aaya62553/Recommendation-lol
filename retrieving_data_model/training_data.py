import requests
import json
from tqdm import tqdm
import time,os
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv("API_KEY")

REQUESTS_MADE = {"match": 0}
LIMITS = {"match": 2000}
SAFETY_THRESHOLD = {"match": 1900}

def wait_if_needed(endpoint):
    global REQUESTS_MADE
    if REQUESTS_MADE[endpoint] >= SAFETY_THRESHOLD[endpoint]:
        print(f"Approche de la limite pour {endpoint}, attente de 10 secondes...")
        time.sleep(10)
        REQUESTS_MADE[endpoint] = 0

def get_match_details(match_id):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
    wait_if_needed("match")
    response = requests.get(url)
    REQUESTS_MADE["match"] += 1
    return response.json() if response.status_code == 200 else None

def get_match_timeline(match_id):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline?api_key={API_KEY}"
    wait_if_needed("match")
    response = requests.get(url)
    REQUESTS_MADE["match"] += 1
    return response.json() if response.status_code == 200 else None

def process_match(match_id, lane="MIDDLE"):
    match = get_match_details(match_id)
    timeline = get_match_timeline(match_id)
    if not match or not timeline:
        return None


    # Associer participantId à champion et victoire
    players = {}
    for participant in match["info"]["participants"]:
        if participant["teamPosition"] == lane:
            players[participant["participantId"]] = {
                "champion": participant["championName"],
                "win": participant["win"]
            }

    if len(players) != 2:  # Pas un matchup clair
        return None

    # Extraire les données par frame
    data = []
    p1_id, p2_id = list(players.keys())
    for frame in timeline["info"]["frames"][:15]:  # Jusqu’à 15 min
        timestamp = frame["timestamp"] / 60000  # En minutes
        p1_frame = frame["participantFrames"][str(p1_id)]
        p2_frame = frame["participantFrames"][str(p2_id)]

        data.append({
            "time": timestamp,
            "gold_diff": p1_frame["currentGold"] - p2_frame["currentGold"],
            "champion_p1": players[p1_id]["champion"],
            "champion_p2": players[p2_id]["champion"],
            "hp_p1": p1_frame["championStats"]["health"],
            "ad_p1": p1_frame["championStats"]["attackDamage"],
            "ap_p1": p1_frame["championStats"]["abilityPower"],
            "hp_p2": p2_frame["championStats"]["health"],
            "ad_p2": p2_frame["championStats"]["attackDamage"],
            "ap_p2": p2_frame["championStats"]["abilityPower"],
            "win": 1 if players[p1_id]["win"] else 0
        })
    return data

# Charger les match IDs et traiter
with open("retrieving_data_model/matches_id/matches_id_BRONZE.json", "r") as f:
    bronze_data = json.load(f)["BRONZE"]

training_data = []
for player in tqdm(bronze_data[:5], desc="Processing matches"):  # Test sur 5 joueurs
    for match_id in player["match_id"]:
        match_data = process_match(match_id)
        if match_data:
            training_data.extend(match_data)

with open("training_data.json", "w") as f:
    json.dump(training_data, f)
print("Données d’entraînement sauvegardées !")