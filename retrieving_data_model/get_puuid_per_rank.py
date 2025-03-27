import requests,os,json
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")


def get_puuid_per_rank(rank,nb_puuid):
    if rank == "MASTER":
        url = f"https://euw1.api.riotgames.com/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5X5?api_key={API_KEY}"
        response = requests.get(url)
        if response.status_code==200:
            data = response.json()["entries"]
    elif rank == "GRANDMASTER":
        url=f"https://euw1.api.riotgames.com/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5X5?api_key={API_KEY}"
        response = requests.get(url)
        if response.status_code==200:
            data = response.json()["entries"]
    elif rank == "CHALLENGER":
        url = f"https://euw1.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5X5?api_key={API_KEY}"
        response = requests.get(url)
        if response.status_code==200:
            data = response.json()["entries"]
    else:
        url = f"https://euw1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5X5/{rank}/IV/?api_key={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
        puuid = []
        for i in range(nb_puuid):
            try :
                puuid.append(data[i]['puuid'])
            except :
                break
        return puuid



def get_matches_id_per_player(puuid,nb_matches):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&queueId=420&start=0&count={nb_matches}&api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def get_matches_id_all_rank_data(nb_player_per_rank,nb_matches_per_player):
    data={}
    for rank in ["BRONZE","SILVER","GOLD","PLATINUM","EMERALD","DIAMOND","MASTER","GRANDMASTER","CHALLENGER"]:
        data[rank]=[]
        puuids=get_puuid_per_rank(rank,nb_player_per_rank)
        for puuid in puuids:
            data[rank].append({"puuid":puuid,"match_id":get_matches_id_per_player(puuid,nb_matches_per_player)})
    with open("retrieving_data_model/matches_id.json","w") as f:
        json.dump(data,f)

get_matches_id_all_rank_data(10,2)


