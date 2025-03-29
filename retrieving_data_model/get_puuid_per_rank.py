import requests
import os
import json
from dotenv import load_dotenv
from tqdm import tqdm
import time
from threading import Thread
from queue import Queue

load_dotenv()
API_KEY = os.getenv("API_KEY")

REQUESTS_MADE = {"league": 0, "match": 0}
LIMITS = {"league": 50, "match": 2000}
SAFETY_THRESHOLD = {"league": 45, "match": 1900}  # Stopper un peu avant la limite

def wait_if_needed(endpoint):
    global REQUESTS_MADE
    if REQUESTS_MADE[endpoint] >= SAFETY_THRESHOLD[endpoint]:  # Arrêter avant la limite max
        print(f"Approche de la limite pour {endpoint} ({REQUESTS_MADE[endpoint]}/{LIMITS[endpoint]}), attente de 10 secondes...")
        time.sleep(10)
        REQUESTS_MADE[endpoint] = 0  # Réinitialise après l'attente

def get_summoner_puuid(summoner_id):
    url = f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}?api_key={API_KEY}"
    while True:
        wait_if_needed("league")
        response = requests.get(url)
        REQUESTS_MADE["league"] += 1
        if response.status_code == 200:
            return response.json()["puuid"]
        elif response.status_code == 429:
            print(f"Erreur 429 pour summonerId {summoner_id}, attente 10s...")
            time.sleep(10)
        else:
            print(f"Erreur {response.status_code} pour summonerId {summoner_id}")
            return None

def get_puuid_per_rank(rank, nb_puuid):
    puuids = []
    if rank == "MASTER":
        url = f"https://euw1.api.riotgames.com/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5?api_key={API_KEY}"
    elif rank == "GRANDMASTER":
        url = f"https://euw1.api.riotgames.com/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5?api_key={API_KEY}"
    elif rank == "CHALLENGER":
        url = f"https://euw1.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5?api_key={API_KEY}"
    else:
        url = f"https://euw1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/{rank}/IV/?api_key={API_KEY}"

    wait_if_needed("league")
    response = requests.get(url)
    REQUESTS_MADE["league"] += 1
    if response.status_code == 200:
        data = response.json()
        if rank in ["MASTER", "GRANDMASTER", "CHALLENGER"]:
            data = data["entries"]
            for i in range(min(nb_puuid, len(data))):
                puuid = get_summoner_puuid(data[i]["summonerId"])
                if puuid:
                    puuids.append(puuid)
                time.sleep(0.2)  # Petit délai pour rester fluide
        else:
            for i in range(min(nb_puuid, len(data))):
                puuid = data[i].get("puuid") or get_summoner_puuid(data[i]["summonerId"])
                if puuid:
                    puuids.append(puuid)
                time.sleep(0.2)
    elif response.status_code == 429:
        print(f"Erreur 429 pour rank {rank}, attente 10s...")
        time.sleep(10)
        return get_puuid_per_rank(rank, nb_puuid)
    return puuids

def get_matches_id_per_player(puuid, nb_matches):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&type=ranked&start=0&count={nb_matches}&api_key={API_KEY}"
    wait_if_needed("match")
    response = requests.get(url)
    REQUESTS_MADE["match"] += 1
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        time.sleep(10)
        return get_matches_id_per_player(puuid, nb_matches)
    return []

def process_rank(rank, nb_players, nb_matches, queue):
    print(f"Début du traitement pour {rank}")
    puuids = get_puuid_per_rank(rank, nb_players)
    data = []
    for puuid in tqdm(puuids, desc=f"Processing {rank} players"):
        match_ids = get_matches_id_per_player(puuid, nb_matches)
        data.append({"puuid": puuid, "match_id": match_ids})
    with open(f"retrieving_data_model/matches_id_{rank}.json", "w") as f:
        json.dump({rank: data}, f)
    queue.put((rank, data))

def get_matches_id_all_rank_data(nb_player_per_rank, nb_matches_per_player):
    data = {}
    ranks = ["BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]
    ranks=["MASTER"]
    queue = Queue()
    threads = []

    for rank in ranks:
        t = Thread(target=process_rank, args=(rank, nb_player_per_rank, nb_matches_per_player, queue))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    while not queue.empty():
        rank, rank_data = queue.get()
        data[rank] = rank_data

    with open("retrieving_data_model/matches_id.json", "w") as f:
        json.dump(data, f)
    print("Sauvegarde finale effectuée")

if __name__ == "__main__":
    get_matches_id_all_rank_data(nb_player_per_rank=1000, nb_matches_per_player=50)