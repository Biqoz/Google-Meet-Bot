from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import json
import os
import tempfile
from dotenv import load_dotenv

# Charger les variables d'environnement (depuis Coolify)
load_dotenv()

class JoinGoogleMeet:
    def __init__(self):
        # --- Configuration de Chrome pour un serveur (Coolify/Docker) ---
        opt = Options()
        # Le profil temporaire est crucial pour la gestion des cookies
        user_data_dir = tempfile.mkdtemp()
        opt.add_argument(f"--user-data-dir={user_data_dir}")
        opt.add_argument('--no-sandbox')
        opt.add_argument('--disable-dev-shm-usage')
        opt.add_argument('--headless=new') # Mode headless indispensable pour serveur
        
        # Se faire passer pour un navigateur normal
        opt.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
        opt.add_argument('--disable-blink-features=AutomationControlled')
        opt.add_argument('--start-maximized')

        # --- LA STRATÉGIE CLÉ : BLOQUER LES PÉRIPHÉRIQUES DÈS LE DÉPART ---
        # On dit à Chrome de refuser automatiquement les demandes de micro et caméra.
        # 1 = Autoriser, 2 = Bloquer
        opt.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.notifications": 2
        })
        
        print("=== [DEBUG] Initialisation du driver Chrome en mode headless...")
        self.driver = webdriver.Chrome(options=opt)
        self.driver.set_window_size(1920, 1080) # Définir une taille de fenêtre aide en headless


    def login_with_cookies(self, meet_link):
        """
        La seule méthode de connexion fiable sur un serveur.
        Elle se rend sur le lien du Meet, injecte les cookies, puis rafraîchit.
        """
        try:
            print(f"=== [DEBUG] Navigation vers le lien Google Meet : {meet_link}")
            # On va directement sur la page du Meet pour avoir le bon domaine
            self.driver.get(meet_link)
            time.sleep(2) # Laisser le temps à la page de se charger

            cookies_path = "cookies.json"
            if not os.path.exists(cookies_path):
                print(f"=== [ERREUR FATALE] Le fichier de cookies '{cookies_path}' est introuvable.")
                raise FileNotFoundError(f"Le fichier {cookies_path} est manquant.")

            with open(cookies_path, 'r') as f:
                cookies = json.load(f)

            print(f"=== [DEBUG] Chargement de {len(cookies)} cookies...")
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            
            print("=== [DEBUG] Cookies chargés. Rafraîchissement de la page...")
            self.driver.refresh()
            time.sleep(5) # Laisser le temps à la session de s'appliquer
            print("=== [DEBUG] Connexion par cookies réussie.")

        except Exception as e:
            print(f"=== [ERREUR FATALE] Échec de la connexion par cookies : {e}")
            self.driver.quit()
            raise


    def join_meeting(self):
        """
        Clique sur le bouton pour rejoindre la réunion.
        Micro/Caméra sont déjà désactivés par la configuration de Chrome.
        """
        try:
            # Sélecteur robuste pour "Participer" ou "Demander à participer"
            join_button_xpath = "//button[.//span[contains(text(), 'Participer') or contains(text(), 'Demander')]]"
            
            print("=== [DEBUG] Attente du bouton pour rejoindre la réunion...")
            join_button = WebDriverWait(self.driver, 40).until(
                EC.element_to_be_clickable((By.XPATH, join_button_xpath))
            )

            # On utilise JavaScript pour un clic plus fiable
            print("=== [DEBUG] Clic sur le bouton pour rejoindre...")
            self.driver.execute_script("arguments[0].click();", join_button)
            
            print("=== [DEBUG] Demande de participation envoyée.")
            
        except TimeoutException:
            print("=== [ERREUR FATALE] Impossible de trouver le bouton pour rejoindre la réunion après 40 secondes.")
            print("=== [DEBUG] HTML au moment de l'erreur ===")
            print(self.driver.page_source)
            self.driver.quit()
            raise
        except Exception as e:
            print(f"=== [ERREUR FATALE] Échec pour rejoindre la réunion : {e}")
            self.driver.quit()
            raise


def main():
    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "output.wav")
    meet_link = os.getenv('MEET_LINK')
    duration = int(os.getenv('RECORDING_DURATION', 60))

    if not meet_link:
        print("=== [ERREUR FATALE] La variable d'environnement MEET_LINK n'est pas définie.")
        return

    print("=== [INFO] Lancement du bot Google Meet ===")
    
    obj = JoinGoogleMeet()
    
    try:
        # Étape 1 : Connexion avec les cookies
        obj.login_with_cookies(meet_link)
        
        # Étape 2 : Rejoindre l'appel (le micro/cam est déjà géré)
        obj.join_meeting()

        # Étape 3 : Lancement de l'enregistrement
        print("=== [INFO] Enregistrement audio démarré...")
        time.sleep(10) # Petite attente pour s'assurer que tout est stable
        # AudioRecorder().get_audio(audio_path, duration)
        print("=== [INFO] Enregistrement terminé (simulation).")
        
        # Étape 4 : Transcription
        # SpeechToText().transcribe(audio_path)
        print("=== [INFO] Bot terminé avec succès. ===")

    finally:
        # S'assurer que le navigateur se ferme correctement
        if 'driver' in obj.__dict__:
            obj.driver.quit()
            print("=== [DEBUG] Driver Chrome fermé.")

# Point d'entrée du script
if __name__ == "__main__":
    main()
