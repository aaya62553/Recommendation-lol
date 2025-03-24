import pandas as pd
import json

def get_champ_role(champion:str)->list:
    df=pd.read_excel("data/champ_role.xlsx")
    champ_role = df[df["Champion"].str.lower() == champion.lower()]
    return [role.strip().lower() for role in champ_role["Role"].values[0].split(",")] if not champ_role.empty else []


def load_data():
    with open("data/champions.json", "r", encoding="utf-8") as f:
        champions = json.load(f)
    with open("data/counters.json", "r", encoding="utf-8") as f:
        counters = json.load(f)
    with open("data/synergy.json", "r", encoding="utf-8") as f:
        synergies = json.load(f)
    return champions, counters, synergies

def calculate_score(champ, enemy_draft, counters, ally_draft, synergies):
    score = 0
    # Pour chaque counter
    for counter in counters.get(champ, []):
        if counter["Champion"] in enemy_draft:
            try:
                win_rate = float(counter["Win Rate"].strip("% "))
                score += 50 - win_rate
            except ValueError:
                continue
    # Pour chaque synergie
    for synergy in synergies.get(champ, []):
        if synergy["Champion"] in ally_draft.values():
            try:
                win_rate = float(synergy["Win Rate"].strip("% "))
                score += win_rate - 50
            except ValueError:
                continue
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
    champion_scores = {champ: 0 for champ in champions_data["data"] if champ not in taken}
    
    # Calcul des scores pour chaque champion
    for champ in champion_scores.keys():
        champion_scores[champ] = calculate_score(champ, enemy_draft, counters, ally_draft, synergies)
    
    # Filtrage par rôle si spécifié
    if next_role:
        role_filtered = [champ for champ in champion_scores.keys() if next_role.lower() in get_champ_role(champ)]
        champion_scores = {champ: champion_scores[champ] for champ in role_filtered}
    # else : 
    #     roles_taken = [role for role in ally_draft.keys() if ally_draft[role] != ""]
    #     if roles_taken:
    #         role_filtered = [champ for champ in champion_scores.keys() if any(role in get_champ_role(champ) for role in roles_taken)]
    #         champion_scores = {champ: champion_scores[champ] for champ in role_filtered}
    
    # Tri des champions par score décroissant
    # Sort champions by score (highest first) and return a list
    sorted_champions = [champ for champ, _ in sorted(champion_scores.items(), key=lambda x: x[1], reverse=True)]
    return sorted_champions[:5]

# Exemple d'utilisation
# champ_recom = recommendations_champ({"Top":"Nasus", "Bottom":"Jinx"}, ["Zed", "Bard"], next_role="Jungle")
# print(champ_recom)
