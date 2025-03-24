import requests
import json

# Remplace par ta clé API Riot (attention, elle est rate-limited et expire pour les clés de développement)
API_KEY = "RGAPI-4d13fb73-9ca1-40cf-8667-6ad364f2d560"
REGION = "euw1"  # Exemple pour EUW

# Dictionnaire de mapping champion ID -> nom (à compléter ou récupérer depuis Data Dragon)
with open("data/champions.json", "r", encoding="utf-8") as f:
    champion_data = json.load(f)["data"]

CHAMPION_ID_MAP = {int(champion_data[champ]["key"]): champ for champ in champion_data}



def get_summoner_by_name(summoner_name):
    gameName, tagLine = summoner_name.split("#")
    url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["puuid"]
    
    else:
        print(f"Erreur {response.status_code} lors de la récupération du summoner")
        return None

def get_active_game(summoner_id):
    url = f"https://{REGION}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{summoner_id}"
    headers = {"X-Riot-Token": API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Aucune partie en cours ou erreur:", response.json())
        return None

def extract_draft(active_game, summoner_id):
    ally_picks = []
    enemy_picks = []
    
    for participant in active_game.get("participants", []):
        champ_id = participant.get("championId")
        champ_name = CHAMPION_ID_MAP.get(champ_id, f"ID {champ_id}")
        # Dans la Spectator API, teamId 100 correspond souvent à l'équipe bleue
        if participant["teamId"] == 100:
            ally_picks.append(champ_name)
        else:
            enemy_picks.append(champ_name)
    return ally_picks, enemy_picks

# Exemple d'utilisation
summoner_name = "El CowSlayer#6388"  # Remplace par le nom du joueur
summoner_id = get_summoner_by_name(summoner_name)
if summoner_id:
    active_game = get_active_game(summoner_id)
    print(active_game)
    if active_game:
        ally_draft, enemy_draft = extract_draft(active_game, summoner_id)
        print("Alliés :", ally_draft)
        print("Ennemis :", enemy_draft)
        
        # Ensuite, on peut utiliser ces données dans ton algorithme de recommandation.
        # Par exemple, en supposant que ta fonction recommendations_champ prend :
        #   ally_draft (liste de noms déjà choisis)
        #   enemy_draft (liste de noms déjà choisis)
        #   next_role (rôle à prédire, ex: "Support")
        # champion_recommendations = recommendations_champ(ally_draft, enemy_draft, next_role="Support")
        # print("Recommandations :", champion_recommendations)
    else:
        print("Le joueur n'est pas en partie.")
else:
    print("Impossible de récupérer le summoner.")
