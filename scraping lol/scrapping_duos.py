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
def get_best_duos(champ,role="",csv=False):
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
    roles=[]

    # Configuration de Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(executable_path="chromedriver.exe")  # Remplacez par le chemin vers chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Ouvrir la page U.GG
    url = f"https://u.gg/lol/champions/{champ}/duos?role={role}&rank=diamond_plus"
    driver.get(url)
    wait = WebDriverWait(driver, 5)

    try:
        # Chercher le bouton "Accepter les cookies" (ajustez le sélecteur CSS)
        cookie_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "fc-button.fc-cta-consent.fc-primary-button")))  # Modifier selon le texte ou le sélecteur du bouton
        cookie_button.click()
        time.sleep(1)  # Attendre que la page se mette à jour
    except:
        print("Pas de bouton de consentement trouvé ou déjà accepté.")


    # Attendre que le tableau des synergies soit visible
    wait = WebDriverWait(driver, 1)
    synergies_table = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".rt-tbody")))

    # Extraire les lignes du tableau
    rows = synergies_table.find_elements(By.CSS_SELECTOR, ".rt-tr-group")
    print(f"Nombre de lignes extraites : {len(rows)}")  # Vérification du nombre de lignes

    # Extraire les données de chaque ligne
    for row in rows:
        cells = row.find_elements(By.CSS_SELECTOR, ".rt-td")
        if len(cells) >= 4:  # Vérifie qu'il y a assez de cellules
            
            champion = cells[2].text
            wr = cells[3].text
            
            role_img = cells[1].find_element(By.TAG_NAME, 'img')
            roles.append(role_img.get_attribute('alt'))
            champions.append(champion)
            win_rates.append(wr)
    # Créer un DataFrame pandas
    df = pd.DataFrame({
        "Role":roles,
        'Champion': champions,
        'Win Rate': win_rates
    }, columns=["Role",'Champion', 'Win Rate'])
    df = df.sort_values(by='Win Rate', ascending=False)
    if csv:
        df.to_csv(f'duos_csv/champion_synergies_{champ}_{role}.csv', index=False)

    driver.quit()

    return df

#get_best_duos('nasus','top')

def get_all_best_duos():
    with open("champions.json", "r", encoding="utf-8") as f:
        try:
            champions = json.load(f)
        except FileNotFoundError:
            print("The file 'champions.json' was not found.")
            return
    duos={}
    for champ in tqdm(champions["data"],desc="Retrieving duos",unit="champion"):
        print("\n"+champ)
        df = get_best_duos(champions["data"][champ]["id"])
        if df.empty:
            continue
        duos[champ]=df.to_dict(orient='records')
    with open('data/synergy.json', 'w') as f:
        json.dump(duos, f, indent=4,ensure_ascii=False)
    return duos

get_all_best_duos()