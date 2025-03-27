import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")

def load_champion_ids():
    url = "https://ddragon.leagueoflegends.com/cdn/14.6.1/data/en_US/champion.json"
    response = requests.get(url)
    champion_data = response.json()["data"]
    return {int(champ["key"]): champ["id"] for champ in champion_data.values()}



def get_summoner_id(summoner_name):
    """ Récupère l'ID d'un joueur à partir de son pseudo """
    gameName, tagLine = summoner_name.split("#")
    id_url=f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}?api_key={API_KEY}"
    response = requests.get(id_url)
    if response.status_code == 200:
        return response.json()["puuid"]
    return None

def get_champ_masteries(summoner_name):
    """ Récupère les maîtrises de champions d'un joueur """
    summoner_id = get_summoner_id(summoner_name)
    url = f"https://euw1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{summoner_id}?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    masteries={}
    data=response.json()
    champ_ids=load_champion_ids()
    for champ in data :
        try:
          masteries[champ_ids[int(champ["championId"])]] = champ["championLevel"]
        except KeyError:
            continue
    return masteries




