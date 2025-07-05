# Fichier : join_google_meet.py

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

# Ces imports sont nécessaires pour l'enregistrement et la transcription
from record_audio import AudioRecorder
from speech_to_text import SpeechToText
from dotenv import load_dotenv

# Charger les variables d'environnement (depuis Coolify)
load_dotenv()

class JoinGoogleMeet:
    def __init__(self):
        opt = Options()
        self.temp_dir = tempfile.mkdtemp() # On stocke le répertoire temporaire
        print(f"=== [DEBUG] Répertoire temporaire créé : {self.temp_dir}")
        opt.add_argument(f"--user-data-dir={self.temp_dir}")
        opt.add_argument('--no-sandbox')
        opt.add_argument('--disable-dev-shm-usage')
        opt.add_argument('--headless=new')
        opt.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
        opt.add_argument('--disable-blink-features=AutomationControlled')
        opt.add_argument('--start-maximized')
        
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
        self.driver.set_window_size(1920, 1080)

    def login_with_cookies(self, meet_link):
        """Charge les cookies de session pour se connecter sans formulaire."""
        try:
            print(f"=== [DEBUG] Navigation vers le lien Google Meet : {meet_link}")
            self.driver.get(meet_link)
            time.sleep(2)

            cookies_path = "cookies.json"
            if not os.path.exists(cookies_path):
                raise FileNotFoundError(f"Le fichier de cookies '{cookies_path}' est introuvable.")

            with open(cookies_path, 'r') as f:
                cookies = json.load(f)
            
            print(f"=== [DEBUG] Nettoyage et chargement de {len(cookies)} cookies...")
            for cookie in cookies:
                if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                    del cookie['sameSite']
                
                try:
                    self.driver.add_cookie(cookie)
                except Exception as cookie_error:
                    print(f"--- [AVERTISSEMENT] Impossible de charger le cookie '{cookie.get('name')}': {cookie_error}")

            print("=== [DEBUG] Cookies chargés. Rafraîchissement de la page...")
            self.driver.refresh()
            time.sleep(5)
            print("=== [DEBUG] Connexion par cookies réussie.")

        except Exception as e:
            print(f"=== [ERREUR FATALE] Échec de la connexion par cookies : {e}")
            self.driver.quit()
            raise

    def join_and_record(self, audio_path, duration):
        """Rejoint la réunion et lance l'enregistrement audio."""
        try:
            # Sélecteur robuste pour "Participer" ou "Demander à participer"
            join_button_xpath = "//button[.//span[contains(text(), 'Participer') or contains(text(), 'Demander')]]"
            
            print("=== [DEBUG] Attente du bouton pour rejoindre la réunion...")
            join_button = WebDriverWait(self.driver, 40).until(
                EC.element_to_be_clickable((By.XPATH, join_button_xpath))
            )

            print("=== [DEBUG] Clic sur le bouton pour rejoindre...")
            self.driver.execute_script("arguments[0].click();", join_button)
            print("=== [DEBUG] Demande de participation envoyée.")
            
            print("=== [INFO] Attente de 10 secondes pour la stabilisation de la connexion...")
            time.sleep(10)
            
            print("=== [INFO] Lancement de l'enregistrement audio...")
            recorder = AudioRecorder()
            recorder.get_audio(audio_path, duration)
            print(f"=== [INFO] Enregistrement audio terminé. Fichier sauvegardé dans {audio_path}")

        except Exception as e:
            print(f"=== [ERREUR FATALE] Échec pour rejoindre ou enregistrer : {e}")
            self.driver.quit()
            raise

def main():
    # Définition des chemins et variables
    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "output.wav")
    meet_link = os.getenv('MEET_LINK')
    duration = int(os.getenv('RECORDING_DURATION', 18000))

    if not meet_link:
        print("=== [ERREUR FATALE] La variable d'environnement MEET_LINK n'est pas définie.")
        return

    print("=== [INFO] Lancement du bot Google Meet ===")
    print(f"=== [INFO] Lien de la réunion : {meet_link}")
    print(f"=== [INFO] Durée d'enregistrement : {duration} secondes")
    print(f"=== [INFO] Le fichier audio sera sauvegardé dans : {audio_path}")
    
    obj = None
    try:
        obj = JoinGoogleMeet()
        
        obj.login_with_cookies(meet_link)
        obj.join_and_record(audio_path, duration)

        print("=== [INFO] Lancement de la transcription...")
        transcriber = SpeechToText()
        transcriber.transcribe(audio_path)
        print("=== [INFO] Transcription terminée.")
        
        print("=== [SUCCÈS] Le bot a terminé toutes ses tâches.")

    except Exception as e:
        print(f"=== [ERREUR] Une erreur non gérée est survenue : {e}")

    finally:
        if obj and hasattr(obj, 'driver'):
            obj.driver.quit()
            print("=== [DEBUG] Driver Chrome fermé.")
        print("=== [INFO] Fin du script. ===")

if __name__ == "__main__":
    main()
