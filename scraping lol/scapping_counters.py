from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import json
from tqdm import tqdm

# Listes pour stocker les données
def get_best_worst_picks(champ,role="",csv=False):
    if role=='bot' or role=='bottom':
        role='adc'
    elif role=="jgl":
        role='jungle'
    elif role=="middle":
        role='mid'
    elif role=="support":
        role='supp'
    

    win_rates = []
    champions = []

    # Configuration de Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(executable_path="chromedriver.exe")  # Remplacez par le chemin vers chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Ouvrir la page U.GG
    url = f"https://u.gg/lol/champions/{champ}/counter?role={role}&rank=diamond_plus"
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    try:
        # Chercher le bouton "Accepter les cookies" (ajustez le sélecteur CSS)
        cookie_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "fc-button.fc-cta-consent.fc-primary-button")))  # Modifier selon le texte ou le sélecteur du bouton
        cookie_button.click()
        time.sleep(2)  # Attendre que la page se mette à jour
    except:
        print("Pas de bouton de consentement trouvé ou déjà accepté.")


    # Attendre que le tableau des synergies soit visible
    wait = WebDriverWait(driver, 10)
    counter_table = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="content"]/div/div[2]/div/div/div[5]/div[1]/div[2]')))

    # Extraire les lignes du tableau
    rows = counter_table.find_elements(By.TAG_NAME, "a")
    print(f"Nombre de lignes extraites : {len(rows)}")  # Vérification du nombre de lignes

    # Extraire les données de chaque ligne
    for row in rows:
        divs=row.find_elements(By.TAG_NAME, "div")
        if len(divs) >= 3:  # Vérifie qu'il y a assez de cellules
            champion = divs[4].text.strip()  # Nom du champion
            wr_games = divs[7].text.strip().split("WR\n")  # Win rate et nombre de parties
            wr = wr_games[0]

            champions.append(champion)
            win_rates.append(wr)

    # Créer un DataFrame pandas
    df = pd.DataFrame({
        'Champion': champions,
        'Win Rate': win_rates
    }, columns=['Champion', 'Win Rate'])
    df = df.sort_values(by='Win Rate', ascending=False)
    if csv:
      df.to_csv(f'counters_csv/champion_counters_{champ}_{role}.csv', index=False)
    driver.quit()
    return df

# get_best_worst_picks("Vel'Koz",'supp',True)

def get_all_counters():
    with open("data/champions.json", "r", encoding="utf-8") as f:
        try:
            champions = json.load(f)
        except FileNotFoundError:
            print("The file 'champions.json' was not found.")
            return
    counters={}
    for champ in tqdm(champions["data"],desc="Retrieving counters",unit="champion"):
        print("\n"+champ)
        df = get_best_worst_picks(champions["data"][champ]["id"])
        if df.empty:
            continue
        counters[champ]=df.to_dict(orient='records')
    with open('data/counters.json', 'w') as f:
        json.dump(counters, f, indent=4,ensure_ascii=False)
    return counters

get_all_counters()