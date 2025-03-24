import tkinter as tk
from tkinter import ttk
from lcu_driver import Connector
import requests
import asyncio
from PIL import Image, ImageTk
from io import BytesIO
import threading

from recommendations import recommendations_champ
ROLE_MAPPING = {
    "TOP": "Top",
    "JUNGLE": "Jungle",
    "MIDDLE": "Middle",
    "BOTTOM": "Bottom",
    "UTILITY": "Support"  
        }
# Charger les noms des champions depuis Data Dragon
def load_champion_ids():
    url = "https://ddragon.leagueoflegends.com/cdn/14.6.1/data/en_US/champion.json"
    response = requests.get(url)
    champion_data = response.json()["data"]
    return {int(champ["key"]): champ["id"] for champ in champion_data.values()}

champion_ids = load_champion_ids()

# Fonction pour recommander des champions (placeholder)


# Fonction pour charger une image de champion
def load_champion_image(champion_name):
    if champion_name == "Non sélectionné" or champion_name == "Unknown":
        # Retourne une image vide
        img = Image.new('RGB', (60, 60), color='gray')
        return ImageTk.PhotoImage(img)
    
    try:
        url = f"https://ddragon.leagueoflegends.com/cdn/14.6.1/img/champion/{champion_name}.png"
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img = img.resize((60, 60), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Erreur de chargement d'image pour {champion_name}: {e}")
        img = Image.new('RGB', (60, 60), color='red')
        return ImageTk.PhotoImage(img)

# Classe principale de l'application
class DraftApp:
    def __init__(self, root):


        self.root = root
        self.root.title("Draft Recommender")
        self.root.geometry("1200x800")  # UI plus grande
        
        # Conteneur principal avec deux colonnes
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Section des bans en haut
        self.bans_frame = tk.LabelFrame(self.main_frame, text="Bans", padx=10, pady=10)
        self.bans_frame.pack(fill="x", pady=10)
        
        self.bans_content = tk.Frame(self.bans_frame)
        self.bans_content.pack(fill="both", expand=True)
        
        # Créer deux colonnes pour les bans
        self.my_bans_frame = tk.Frame(self.bans_content)
        self.my_bans_frame.pack(side=tk.LEFT, fill="both", expand=True)
        
        self.their_bans_frame = tk.Frame(self.bans_content)
        self.their_bans_frame.pack(side=tk.RIGHT, fill="both", expand=True)
        
        tk.Label(self.my_bans_frame, text="Bans alliés:", font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(self.their_bans_frame, text="Bans ennemis:", font=("Arial", 12, "bold")).pack(anchor="w")
        
        # Conteneurs d'images pour les bans
        self.my_bans_images = []
        self.my_bans_labels = tk.Frame(self.my_bans_frame)
        self.my_bans_labels.pack(anchor="w", pady=5)
        
        self.their_bans_images = []
        self.their_bans_labels = tk.Frame(self.their_bans_frame)
        self.their_bans_labels.pack(anchor="w", pady=5)
        
        # Créer deux colonnes pour les équipes
        self.teams_container = tk.Frame(self.main_frame)
        self.teams_container.pack(fill="both", expand=True, pady=10)
        
        # Mon équipe à gauche
        self.my_team_frame = tk.LabelFrame(self.teams_container, text="Mon équipe", padx=10, pady=10)
        self.my_team_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 10))
        
        # Équipe adverse à droite
        self.their_team_frame = tk.LabelFrame(self.teams_container, text="Équipe adverse", padx=10, pady=10)
        self.their_team_frame.pack(side=tk.RIGHT, fill="both", expand=True, padx=(10, 0))
        
        # Section recommandations en bas
        self.recommendations_frame = tk.LabelFrame(self.main_frame, text="Recommandations", padx=10, pady=10)
        self.recommendations_frame.pack(fill="x", pady=10)
        
        # Labels pour afficher les données (avec images)
        self.my_team_frames = []
        self.my_team_images = []
        self.my_team_labels = []
        
        for i in range(5):
            frame = tk.Frame(self.my_team_frame)
            frame.pack(anchor="w", pady=10, fill="x")
            
            img_label = tk.Label(frame)
            img_label.pack(side=tk.LEFT, padx=(0, 10))
            
            text_label = tk.Label(frame, text="Non sélectionné", font=("Arial", 12))
            text_label.pack(side=tk.LEFT)
            
            self.my_team_frames.append(frame)
            self.my_team_images.append(img_label)
            self.my_team_labels.append(text_label)
        
        self.their_team_frames = []
        self.their_team_images = []
        self.their_team_labels = []
        
        for i in range(5):
            frame = tk.Frame(self.their_team_frame)
            frame.pack(anchor="w", pady=10, fill="x")
            
            img_label = tk.Label(frame)
            img_label.pack(side=tk.LEFT, padx=(0, 10))
            
            text_label = tk.Label(frame, text="Non sélectionné", font=("Arial", 12))
            text_label.pack(side=tk.LEFT)
            
            self.their_team_frames.append(frame)
            self.their_team_images.append(img_label)
            self.their_team_labels.append(text_label)
        
        # Pour les bans, créer des images placeholder
        for i in range(5):
            img_label = tk.Label(self.my_bans_labels)
            img_label.pack(side=tk.LEFT, padx=5)
            self.my_bans_images.append(img_label)
            
            img_label = tk.Label(self.their_bans_labels)
            img_label.pack(side=tk.LEFT, padx=5)
            self.their_bans_images.append(img_label)
        
        self.recommendations_label = tk.Label(self.recommendations_frame, text="", font=("Arial", 12))
        self.recommendations_label.pack(anchor="w")
        
        # Stocker les images pour éviter le garbage collection
        self.image_references = {}
        
        # Initialiser la connexion au LCU
        self.connector = Connector()

        @self.connector.ready
        async def on_connect(connection):
            await self.on_connect(connection)

        threading.Thread(target=self.connector.start, daemon=True).start()  # Lancer LCU dans un thread séparé

    def get_next_picker(self, data):

        actions = data.get("actions", [])
        local_player_cell_id = data.get("localPlayerCellId", -1)
        my_team = {player["cellId"]: player["assignedPosition"] or "Non défini" for player in data.get("myTeam", [])}

        for action_group in actions:
            for action in action_group:
                if action["type"] == "pick" and action["isInProgress"]:
                    actor_cell_id = action["actorCellId"]
                    if actor_cell_id in my_team:
                        role = my_team[actor_cell_id]
                        mapped_role = ROLE_MAPPING.get(role, None)  # Convertir le rôle
                        return mapped_role if mapped_role else None  # Retourner None si non mappé ou "Non défini"
        return None
    # Quand la connexion au client LoL est établie
    async def on_connect(self, connection):
        print("Connecté au client League of Legends")
        await self.update_loop(connection)

    # Boucle pour mettre à jour les données
    async def update_loop(self, connection):
        while True:
            try:
                response = await connection.request('get', '/lol-champ-select/v1/session')
                if response.status == 200:
                    data = await response.json()
                    self.root.after(0, self.update_ui, data)  # Mettre à jour l'UI dans le thread principal
                else:
                    self.root.after(0, self.clear_ui)  # Réinitialiser l'UI si pas de session
            except Exception as e:
                print(f"Erreur dans la boucle de mise à jour : {e}")
                self.root.after(0, self.clear_ui)
            await asyncio.sleep(2)  # Attendre 2 secondes

    # Mettre à jour l'interface avec les données
    def update_ui(self, data):
        # Mon équipe
        my_team = data.get("myTeam", [])
        for i, player in enumerate(my_team[:5]):
            champ_id = player["championId"]
            role = player["assignedPosition"] or "Non défini"
            champ_name = champion_ids.get(champ_id, "Non sélectionné") if champ_id != 0 else "Non sélectionné"
            self.my_team_labels[i].config(text=f"{champ_name} ({role})")
            # Charger et afficher l'image
            if champ_id != 0 and champ_id in champion_ids:
                img = load_champion_image(champ_name)
                self.image_references[f"my_team_{i}"] = img  # Garder une référence
                self.my_team_images[i].config(image=img)
            else:
                img = load_champion_image("Non sélectionné")
                self.image_references[f"my_team_{i}"] = img
                self.my_team_images[i].config(image=img)

        # Équipe adverse
        their_team = data.get("theirTeam", [])
        for i, player in enumerate(their_team[:5]):
            champ_id = player["championId"]
            champ_name = champion_ids.get(champ_id, "Non sélectionné") if champ_id != 0 else "Non sélectionné"
            self.their_team_labels[i].config(text=champ_name)
            
            # Charger et afficher l'image
            if champ_id != 0 and champ_id in champion_ids:
                img = load_champion_image(champ_name)
                self.image_references[f"their_team_{i}"] = img
                self.their_team_images[i].config(image=img)
            else:
                img = load_champion_image("Non sélectionné")
                self.image_references[f"their_team_{i}"] = img
                self.their_team_images[i].config(image=img)

        # Bans
        bans = data.get("bans", {})
        my_team_bans = [champion_ids.get(ban, "Unknown") for ban in bans.get("myTeamBans", []) if ban != 0]
        their_team_bans = [champion_ids.get(ban, "Unknown") for ban in bans.get("theirTeamBans", []) if ban != 0]
        # Afficher les images de ban pour mon équipe
        for i in range(5):
            if i < len(my_team_bans):
                img = load_champion_image(my_team_bans[i])
                self.image_references[f"my_bans_{i}"] = img
                self.my_bans_images[i].config(image=img)
            else:
                img = load_champion_image("Unknown")
                self.image_references[f"my_bans_{i}"] = img
                self.my_bans_images[i].config(image=img)
        
        # Afficher les images de ban pour l'équipe adverse
        for i in range(5):
            if i < len(their_team_bans):
                img = load_champion_image(their_team_bans[i])
                self.image_references[f"their_bans_{i}"] = img
                self.their_bans_images[i].config(image=img)
            else:
                img = load_champion_image("Unknown")
                self.image_references[f"their_bans_{i}"] = img
                self.their_bans_images[i].config(image=img)

        # Recommandations
        ally_draft = {ROLE_MAPPING.get(player["assignedPosition"], f"Pos{i}"): champion_ids.get(player["championId"], "") 
              for i, player in enumerate(my_team) if player["championId"] != 0}
        enemy_draft = [champion_ids.get(player["championId"], "") for player in their_team if player["championId"] != 0]
        all_bans = my_team_bans + their_team_bans
        next_role = self.get_next_picker(data)
        print(next_role)
        recommendations = recommendations_champ(ally_draft, enemy_draft, all_bans, next_role)
        if next_role:
            self.recommendations_label.config(text=f"Prochain picker ({next_role}) : {', '.join(recommendations)}")
        else:
            self.recommendations_label.config(text=f"Recommandations : {', '.join(recommendations)}")
    # Réinitialiser l'UI si aucune session n'est active
    def clear_ui(self):
        for i in range(5):
            self.my_team_labels[i].config(text="Non sélectionné")
            self.their_team_labels[i].config(text="Non sélectionné")
            
            # Réinitialiser les images
            img = load_champion_image("Non sélectionné")
            self.image_references[f"my_team_{i}"] = img
            self.my_team_images[i].config(image=img)
            
            self.image_references[f"their_team_{i}"] = img
            self.their_team_images[i].config(image=img)
            
            # Réinitialiser les bans
            img = load_champion_image("Unknown")
            self.image_references[f"my_bans_{i}"] = img
            self.my_bans_images[i].config(image=img)
            
            self.image_references[f"their_bans_{i}"] = img
            self.their_bans_images[i].config(image=img)
        
        self.recommendations_label.config(text="")

# Lancer l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = DraftApp(root)
    root.mainloop()