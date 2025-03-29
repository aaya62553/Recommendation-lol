import requests
import json
from tqdm import tqdm
import pandas as pd
import time
import os
from dotenv import load_dotenv
from collections import deque
from threading import Lock

load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY not found in environment variables.")


REQUESTS_MADE = {"match": deque(maxlen=100)}  # Suivi des 100 dernières requêtes
REQUESTS_PER_SEC = 0
LAST_SEC = time.time()
REQUEST_LOCK = Lock()

# Limites officielles
MAX_PER_SEC = 20  # 20 requêtes/seconde
MAX_PER_2MIN = 100  # 100 requêtes/2 minutes
WINDOW_2MIN = 120  # 120 secondes

def wait_if_needed():
    global REQUESTS_PER_SEC, LAST_SEC
    with REQUEST_LOCK:
        current_time = time.time()

        # Réinitialiser le compteur par seconde
        if current_time - LAST_SEC >= 1:
            REQUESTS_PER_SEC = 0
            LAST_SEC = current_time

        # Vérifier la limite par seconde
        if REQUESTS_PER_SEC >= MAX_PER_SEC:
            sleep_time = 1 - (current_time - LAST_SEC)
            if sleep_time > 0:
                print(f"Limite de 20/sec atteinte, attente de {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            REQUESTS_PER_SEC = 0
            LAST_SEC = time.time()

        # Vérifier la limite sur 2 minutes
        while len(REQUESTS_MADE["match"]) >= MAX_PER_2MIN:
            oldest_time = REQUESTS_MADE["match"][0]
            time_to_wait = WINDOW_2MIN - (current_time - oldest_time)
            if time_to_wait > 0:
                print(f"Limite de 100/2min atteinte, attente de {time_to_wait:.2f}s...")
                time.sleep(time_to_wait)
            current_time = time.time()

        REQUESTS_PER_SEC += 1
        REQUESTS_MADE["match"].append(current_time)

def get_match_details(match_id, retries=3, timeout=30):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
    for attempt in range(retries):
        wait_if_needed()
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                print(f"403 Forbidden pour match {match_id} - Vérifiez la clé API")
                return None
            elif response.status_code == 429:
                print(f"429 Rate Limit pour match {match_id}, attente 10s...")
                time.sleep(10)
            else:
                print(f"Erreur {response.status_code} pour match {match_id}")
                return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"Erreur de connexion pour match {match_id}: {e}")
            time.sleep(5 * (attempt + 1))
    return None

def get_match_timeline(match_id, retries=3, timeout=30):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline?api_key={API_KEY}"
    for attempt in range(retries):
        wait_if_needed()
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                print(f"403 Forbidden pour timeline {match_id} - Vérifiez la clé API")
                return None
            elif response.status_code == 429:
                print(f"429 Rate Limit pour timeline {match_id}, attente 10s...")
                time.sleep(10)
            else:
                print(f"Erreur {response.status_code} pour timeline {match_id}")
                return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"Erreur de connexion pour timeline {match_id}: {e}")
            time.sleep(5 * (attempt + 1))
    return None

def process_match(match_id, lane="MIDDLE"):
    match = get_match_details(match_id)
    timeline = get_match_timeline(match_id)
    if not match or not timeline:
        return None

    players = {}
    for participant in match["info"]["participants"]:
        if participant["teamPosition"] == lane:
            players[participant["participantId"]] = {
                "champion": participant["championName"],
                "win": participant["win"]
            }

    if len(players) != 2:
        return None

    data = []
    p1_id, p2_id = list(players.keys())
    for frame in timeline["info"]["frames"][:15]:
        timestamp = round(frame["timestamp"] / 60000, 1)
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
            "armor_p1": p1_frame["championStats"]["armor"],
            "moveSpeed_p1": p1_frame["championStats"]["movementSpeed"],
            "attackSpeed_p1": p1_frame["championStats"]["attackSpeed"],
            "level_p1": p1_frame["level"],
            "hp_p2": p2_frame["championStats"]["health"],
            "ad_p2": p2_frame["championStats"]["attackDamage"],
            "ap_p2": p2_frame["championStats"]["abilityPower"],
            "armor_p2": p2_frame["championStats"]["armor"],
            "moveSpeed_p2": p2_frame["championStats"]["movementSpeed"],
            "attackSpeed_p2": p2_frame["championStats"]["attackSpeed"],
            "level_p2": p2_frame["level"],
            "win": 1 if players[p1_id]["win"] else 0
        })
    return data

# Traitement par rang
ranks = ["BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND", "GRANDMASTER", "CHALLENGER"]
lanes = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]

for rank in ranks:
    with open(f"retrieving_data_model/matches_id/matches_id_{rank}.json", "r") as f:
        rank_id = json.load(f)[rank]

    training_data = []
    for player in tqdm(rank_id, desc=f"Processing {rank} matches"):
        for match_id in player["match_id"]:
            for lane in lanes:
                match_data = process_match(match_id, lane)
                if match_data:
                    training_data.extend(match_data)

    # Sauvegarde par rang
    training_data_pd = pd.DataFrame(training_data)
    training_data_pd.to_csv(f"retrieving_data_model/training_data/training_data_{rank}.csv", index=False)
    with open(f"retrieving_data_model/training_data/training_data_{rank}.json", "w") as f:
        json.dump(training_data, f)
    print(f"Données pour {rank} sauvegardées !")
    training_data = []  # Libère la mémoire

print("Traitement terminé !")