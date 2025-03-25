import pandas as pd
import json,os,sys

CHAMP_DATA = None

def get_champ_role(champion: str) -> list:
    champ_role = CHAMP_DATA[CHAMP_DATA["Champion"].str.lower() == champion.lower()]
    return [role.strip().lower() for role in champ_role["Role"].values[0].split(",")] if not champ_role.empty else []

def get_champ_type(champion: str) -> str:
    champ_type = CHAMP_DATA[CHAMP_DATA["Champion"].str.lower() == champion.lower()]
    return champ_type["AD/AP"].values[0] if not champ_type.empty else ""

def get_file_path(relative_path):
    """Renvoie le chemin correct du fichier en fonction du mode (script ou .exe)."""
    if getattr(sys, 'frozen', False):  # Mode exécutable PyInstaller
        base_path = sys._MEIPASS
    else:  # Mode script Python normal
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def load_data():
    global CHAMP_DATA
    with open(get_file_path("data/champions.json"), "r", encoding="utf-8") as f:
        champions = json.load(f)
    with open(get_file_path("data/counters.json"), "r", encoding="utf-8") as f:
        counters = json.load(f)
    with open(get_file_path("data/synergy.json"), "r", encoding="utf-8") as f:
        synergies = json.load(f)
    CHAMP_DATA = pd.read_excel(get_file_path("data/champ_role.xlsx"))

    return champions, counters, synergies

def calculate_score(champ, enemy_draft, counters, ally_draft, synergies):
    score = 0
    # Pour chaque counter
    for counter in counters.get(champ, []):
        if counter["Champion"] in enemy_draft:
            try:
                win_rate = float(counter["Win Rate"].strip("% "))
                score += 0.6*(50 - win_rate)**3
            except ValueError:
                continue
    # Pour chaque synergie
    for synergy in synergies.get(champ, []):
        if synergy["Champion"] in ally_draft.values():
            try:
                win_rate = float(synergy["Win Rate"].strip("% "))
                score += 0.2*(win_rate - 50)**3
            except ValueError:
                continue
    if len(ally_draft)>=3 :
        ad_ratio = 0
        for champ in ally_draft.values():
            if get_champ_type(champ) == "AD":
                ad_ratio += 1
        ad_ratio = ad_ratio/len(ally_draft)
        if ad_ratio>0.65:
            if get_champ_type(champ) == "AP":
                score += 5
            elif get_champ_type(champ) == "AD":
                score -= 5
        elif ad_ratio<0.35:
            if get_champ_type(champ) == "AP":
                score -= 5
            elif get_champ_type(champ) == "AD":
                score += 5

    return score

def recommendations_champ(ally_draft, enemy_draft,bans ,next_role=None):
    """
    ally_draft: liste ou dict des champions alliés déjà sélectionnés
    enemy_draft: liste des champions ennemis déjà sélectionnés
    bans: liste des champions bannis
    next_role: rôle à prédire (ex: "Support")
    """
    champions_data, counters, synergies = load_data()
    # Liste des champions déjà pris
    taken = set(list(ally_draft.values()) + enemy_draft)
    
    # Initialiser les scores pour les champions disponibles
    champion_scores = {champ: 0 for champ in champions_data["data"] if champ not in taken and champ not in bans}
    
    # Calcul des scores pour chaque champion
    for champ in champion_scores.keys():
        champion_scores[champ] = calculate_score(champ, enemy_draft, counters, ally_draft, synergies)
    
    # Filtrage par rôle si spécifié
    if next_role:
        role_filtered = [champ for champ in champion_scores.keys() if next_role.lower() in get_champ_role(champ)]
        champion_scores = {champ: champion_scores[champ] for champ in role_filtered}
    else : 
        roles_taken = [role for role in ally_draft.keys() if ally_draft[role] in ["Top", "Jungle", "Middle", "Bottom", "Support"]]
        if len(roles_taken) >0:
            role_filtered = [champ for champ in champion_scores.keys() if any(role in get_champ_role(champ) for role in roles_taken)]
            champion_scores = {champ: champion_scores[champ] for champ in role_filtered}
    
    # Tri des champions par score décroissant
    # Sort champions by score (highest first) and return a list
    sorted_champions = [champ for champ, _ in sorted(champion_scores.items(), key=lambda x: x[1], reverse=True)]
    return sorted_champions[:5]

# Exemple d'utilisation
# champ_recom = recommendations_champ({"Top":"Nasus", "Bottom":"Jinx"}, ["Zed", "Bard"], next_role="Jungle")
# print(champ_recom)
