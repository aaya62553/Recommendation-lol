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
    "top": "Top",
    "jungle": "Jungle",
    "middle": "Middle",
    "bottom": "Bottom",
    "utility": "Support"  
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
        # Define color scheme
        self.colors = {
            "bg_main": "#1a1a2e",  # Dark blue background
            "bg_frame": "#16213e",  # Slightly lighter blue for frames
            "text_light": "#e2e2e2",  # Light text
            "accent_blue": "#0f3460",  # Deep blue for accents
            "accent_red": "#950740",  # Red accent for enemy team
            "accent_blue_light": "#246eb9",  # Lighter blue for highlights
            "accent_red_light": "#c70039",  # Lighter red for highlights
            "neutral": "#2c394b",  # Neutral color for general elements
            "ban_bg": "#440a67",  # Purple color for ban sections
        }

        self.root = root
        self.root.title("Draft Recommender")
        self.root.geometry("1200x800")  # UI plus grande
        self.root.configure(bg=self.colors["bg_main"])
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TFrame", background=self.colors["bg_frame"])
        style.configure("TLabel", background=self.colors["bg_frame"], foreground=self.colors["text_light"])
        style.configure("TLabelframe", background=self.colors["bg_frame"], foreground=self.colors["text_light"])
        
        # Conteneur principal avec deux colonnes
        self.main_frame = tk.Frame(root, bg=self.colors["bg_main"], bd=2)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Section des bans en haut
        self.bans_frame = tk.LabelFrame(self.main_frame, text="Bans", 
                                        bg=self.colors["ban_bg"], 
                                        fg=self.colors["text_light"],
                                        font=("Arial", 12, "bold"),
                                        padx=10, pady=10)
        self.bans_frame.pack(fill="x", pady=10)
        
        self.bans_content = tk.Frame(self.bans_frame, bg=self.colors["ban_bg"])
        self.bans_content.pack(fill="both", expand=True)
        
        # Créer deux colonnes pour les bans
        self.my_bans_frame = tk.Frame(self.bans_content, bg=self.colors["ban_bg"])
        self.my_bans_frame.pack(side=tk.LEFT, fill="both", expand=True)
        
        self.their_bans_frame = tk.Frame(self.bans_content, bg=self.colors["ban_bg"])
        self.their_bans_frame.pack(side=tk.RIGHT, fill="both", expand=True)
        
        tk.Label(self.my_bans_frame, text="Bans alliés:", font=("Arial", 12, "bold"), 
                bg=self.colors["ban_bg"], fg=self.colors["text_light"]).pack(anchor="w")
        tk.Label(self.their_bans_frame, text="Bans ennemis:", font=("Arial", 12, "bold"), 
                bg=self.colors["ban_bg"], fg=self.colors["text_light"]).pack(anchor="w")
        
        # Conteneurs d'images pour les bans
        self.my_bans_images = []
        self.my_bans_labels = tk.Frame(self.my_bans_frame, bg=self.colors["ban_bg"])
        self.my_bans_labels.pack(anchor="w", pady=5)
        
        self.their_bans_images = []
        self.their_bans_labels = tk.Frame(self.their_bans_frame, bg=self.colors["ban_bg"])
        self.their_bans_labels.pack(anchor="w", pady=5)
        
        # Créer deux colonnes pour les équipes
        self.teams_container = tk.Frame(self.main_frame, bg=self.colors["bg_main"])
        self.teams_container.pack(fill="both", expand=True, pady=10)
        
        # Mon équipe à gauche
        self.my_team_frame = tk.LabelFrame(self.teams_container, text="Mon équipe", 
                                          bg=self.colors["accent_blue"], 
                                          fg=self.colors["text_light"],
                                          font=("Arial", 12, "bold"),
                                          highlightbackground=self.colors["accent_blue_light"], 
                                          highlightthickness=2,
                                          padx=10, pady=10)
        self.my_team_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 10))
        
        # Équipe adverse à droite
        self.their_team_frame = tk.LabelFrame(self.teams_container, text="Équipe adverse", 
                                             bg=self.colors["accent_red"], 
                                             fg=self.colors["text_light"],
                                             font=("Arial", 12, "bold"),
                                             highlightbackground=self.colors["accent_red_light"], 
                                             highlightthickness=2,
                                             padx=10, pady=10)
        self.their_team_frame.pack(side=tk.RIGHT, fill="both", expand=True, padx=(10, 0))
        
        # Section recommandations en bas
        self.recommendations_frame = tk.LabelFrame(self.main_frame, text="Recommandations", 
                                                  bg=self.colors["neutral"], 
                                                  fg=self.colors["text_light"],
                                                  font=("Arial", 12, "bold"),
                                                  padx=10, pady=10)
        self.recommendations_frame.pack(fill="x", pady=10)
        
        # Labels pour afficher les données (avec images)
        self.my_team_frames = []
        self.my_team_images = []
        self.my_team_labels = []
        
        for i in range(5):
            frame = tk.Frame(self.my_team_frame, bg=self.colors["accent_blue"])
            frame.pack(anchor="w", pady=10, fill="x")
            
            img_label = tk.Label(frame, bg=self.colors["accent_blue"])
            img_label.pack(side=tk.LEFT, padx=(0, 10))
            
            text_label = tk.Label(frame, text="Non sélectionné", 
                                 font=("Arial", 12), 
                                 bg=self.colors["accent_blue"], 
                                 fg=self.colors["text_light"])
            text_label.pack(side=tk.LEFT)
            
            self.my_team_frames.append(frame)
            self.my_team_images.append(img_label)
            self.my_team_labels.append(text_label)
        
        self.their_team_frames = []
        self.their_team_images = []
        self.their_team_labels = []
        
        for i in range(5):
            frame = tk.Frame(self.their_team_frame, bg=self.colors["accent_red"])
            frame.pack(anchor="w", pady=10, fill="x")
            
            img_label = tk.Label(frame, bg=self.colors["accent_red"])
            img_label.pack(side=tk.LEFT, padx=(0, 10))
            
            text_label = tk.Label(frame, text="Non sélectionné", 
                                 font=("Arial", 12), 
                                 bg=self.colors["accent_red"], 
                                 fg=self.colors["text_light"])
            text_label.pack(side=tk.LEFT)
            
            self.their_team_frames.append(frame)
            self.their_team_images.append(img_label)
            self.their_team_labels.append(text_label)
        
        # Pour les bans, créer des images placeholder
        for i in range(5):
            img_label = tk.Label(self.my_bans_labels, bg=self.colors["ban_bg"])
            img_label.pack(side=tk.LEFT, padx=5)
            self.my_bans_images.append(img_label)
            
            img_label = tk.Label(self.their_bans_labels, bg=self.colors["ban_bg"])
            img_label.pack(side=tk.LEFT, padx=5)
            self.their_bans_images.append(img_label)
        
        self.recommendations_label = tk.Label(self.recommendations_frame, text="", 
                                             font=("Arial", 12, "bold"),
                                             bg=self.colors["neutral"], 
                                             fg=self.colors["text_light"])
        self.recommendations_label.pack(anchor="w", pady=5)
        
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
        my_team = {player["cellId"]: player["assignedPosition"] or "Non défini" for player in data.get("myTeam", [])}

        for action_group in actions:
            for action in action_group:
                if action["type"] == "pick" and action["isInProgress"]==True:
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
            await asyncio.sleep(3)  # Attendre 2 secondes

    # Mettre à jour l'interface avec les données
    def update_ui(self, data):
        # Mon équipe
        my_team = data.get("myTeam", [])
        for i, player in enumerate(my_team[:5]):
            champ_id = player["championId"]
            role = player["assignedPosition"] or "Non défini"
            champ_name = champion_ids.get(champ_id, "Non sélectionné") if champ_id != 0 else "Non sélectionné"
            self.my_team_labels[i].config(text=f"{champ_name} ({role})")
            
            # Highlight the player row if a champion is selected
            if champ_id != 0 and champ_id in champion_ids:
                self.my_team_frames[i].config(bg=self.colors["accent_blue_light"])
                self.my_team_labels[i].config(bg=self.colors["accent_blue_light"])
                self.my_team_images[i].config(bg=self.colors["accent_blue_light"])
            else:
                self.my_team_frames[i].config(bg=self.colors["accent_blue"])
                self.my_team_labels[i].config(bg=self.colors["accent_blue"])
                self.my_team_images[i].config(bg=self.colors["accent_blue"])
            
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
            
            # Highlight the player row if a champion is selected
            if champ_id != 0 and champ_id in champion_ids:
                self.their_team_frames[i].config(bg=self.colors["accent_red_light"])
                self.their_team_labels[i].config(bg=self.colors["accent_red_light"])
                self.their_team_images[i].config(bg=self.colors["accent_red_light"])
            else:
                self.their_team_frames[i].config(bg=self.colors["accent_red"])
                self.their_team_labels[i].config(bg=self.colors["accent_red"])
                self.their_team_images[i].config(bg=self.colors["accent_red"])
            
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

        if my_team_bans==[]:
            my_team_cell = [player["cellId"] for player in data.get("myTeam", [])]
            for ban in data.get("actions", [])[0]:
                if ban["type"] == "ban" and ban["actorCellId"] in my_team_cell:
                    my_team_bans.append(champion_ids.get(ban["championId"], "Unknown"))

        if their_team_bans==[]:
            their_team_cell = [player["cellId"] for player in data.get("theirTeam", [])]
            for ban in data.get("actions", [])[0]:
                if ban["type"] == "ban" and ban["actorCellId"] in their_team_cell:
                    their_team_bans.append(champion_ids.get(ban["championId"], "Unknown"))
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
            
            # Reset background colors
            self.my_team_frames[i].config(bg=self.colors["accent_blue"])
            self.my_team_labels[i].config(bg=self.colors["accent_blue"])
            self.my_team_images[i].config(bg=self.colors["accent_blue"])
            
            self.their_team_frames[i].config(bg=self.colors["accent_red"])
            self.their_team_labels[i].config(bg=self.colors["accent_red"])
            self.their_team_images[i].config(bg=self.colors["accent_red"])
            
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