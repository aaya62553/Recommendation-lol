from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Listes pour stocker les données
classements = []
win_rates = []
champions = []

# Configuration de Selenium
chrome_options = Options()
service = Service(executable_path="chromedriver.exe")  # Remplacez par le chemin vers chromedriver
driver = webdriver.Chrome(service=service)

# Ouvrir la page U.GG
url = "https://u.gg/lol/champions/chogath/duos?role=top&rank=master_plus"
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
synergies_table = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".rt-tbody")))

# Extraire les lignes du tableau
rows = synergies_table.find_elements(By.CSS_SELECTOR, ".rt-tr-group")
print(f"Nombre de lignes extraites : {len(rows)}")  # Vérification du nombre de lignes

# Extraire les données de chaque ligne
for row in rows:
    cells = row.find_elements(By.CSS_SELECTOR, ".rt-td")
    if len(cells) >= 4:  # Vérifie qu'il y a assez de cellules
        classement = cells[0].text
        champion = cells[2].text
        wr = cells[3].text

        classements.append(classement)
        champions.append(champion)
        win_rates.append(wr)

# Créer un DataFrame pandas
df = pd.DataFrame({
    'Classement': classements,
    'Champion': champions,
    'Win Rate': win_rates
}, columns=['Classement', 'Champion', 'Win Rate'])

# Afficher le DataFrame
print(df)

# Sauvegarder en CSV si nécessaire
# df.to_csv('champion_synergies.csv', index=False)

# Fermer le navigateur
driver.quit()