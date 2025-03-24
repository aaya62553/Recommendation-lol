import requests
import matplotlib.pyplot as plt

# 🔑 Ta clé API Riot (remplace-la par la tienne)
API_KEY = "RGAPI-179530c6-500b-460d-b7bb-313983e2c59f"

# 🌍 Région du serveur (ex: "euw1", "na1", "kr", "br1")
REGION = "euw1"

# 🏆 Nom du joueur (à modifier)
SUMMONER_NAME = "Mayner#RAZE"

# 📌 Base de données statique des champions (tu peux automatiser ça)


def get_summoner_id(summoner_name):
    """ Récupère l'ID d'un joueur à partir de son pseudo """
    gameName, tagLine = summoner_name.split("#")
    id_url=f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}?api_key={API_KEY}"
    response = requests.get(id_url)
    if response.status_code == 200:
        return response.json()["puuid"]
    return None

def get_summoner_info(summoner_id):
    """ Vérifie si le joueur est en partie et récupère les informations """
    url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{summoner_id}?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def get_matches_id(summoner_id,start=0,count=20):
    """ Récupère les ID des parties d'un joueur """
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_id}/ids?start={start}&count={count}&api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return list(response.json())
    return None


def get_match_timeline(match_id):
    """ Récupère les informations d'une partie """
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_match_info(match_id):
    """ Récupère les informations d'une partie """
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def plot_gold_timeline(match_timeline):
    """ Affiche l'évolution de l'or des joueurs """
    match_info = match_timeline["info"]["frames"]
    gold_timeline= {"timestamp": [], "red": [], "blue": [],"delta":[]}

    for frame in match_info:
        r_gold_sum = 0
        b_gold_sum = 0
        for participant in frame["participantFrames"]:
            if int(participant) <= 5:
                r_gold_sum+=frame["participantFrames"][participant]["totalGold"]
            else:
                b_gold_sum+=frame["participantFrames"][participant]["totalGold"]
        gold_timeline["red"].append(r_gold_sum)
        gold_timeline["blue"].append(b_gold_sum)
        gold_timeline["timestamp"].append(frame["timestamp"]/60000)
        gold_timeline["delta"].append(r_gold_sum-b_gold_sum)
    for i in range(len(gold_timeline["timestamp"])-1):
        if gold_timeline["delta"][i] < 0:
            plt.plot(gold_timeline["timestamp"][i:i+2], gold_timeline["delta"][i:i+2], 'r')
        else:
            plt.plot(gold_timeline["timestamp"][i:i+2], gold_timeline["delta"][i:i+2], 'b')
    print(gold_timeline["delta"])
    plt.legend()
    plt.show()
    return gold_timeline

def get_draft_info(match_info):
    """ Récupère les informations de la draft """
    draft_info = match_info["info"]["participants"]
    draft = {"blue": [], "red": []}

    for participant in draft_info:
        if participant["teamId"] == 100:
            draft["blue"].append(participant["championName"])
        else:
            draft["red"].append(participant["championName"])
    return draft





# Test
id=get_summoner_id(SUMMONER_NAME)
#print(get_summoner_info(id))
#print(get_matches_id(id))

match_id = get_matches_id(id)[11]
#match_timeline = plot_gold_timeline(get_match_timeline(match_id))
print(get_draft_info(get_match_info(match_id)))


