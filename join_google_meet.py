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

load_dotenv()

class JoinGoogleMeet:
    # ... __init__ reste le même ...
    def __init__(self):
        opt = Options()
        user_data_dir = tempfile.mkdtemp()
        opt.add_argument(f"--user-data-dir={user_data_dir}")
        opt.add_argument('--no-sandbox')
        opt.add_argument('--disable-dev-shm-usage')
        opt.add_argument('--headless=new')
        opt.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
        opt.add_argument('--disable-blink-features=AutomationControlled')
        opt.add_argument('--start-maximized')
        opt.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.notifications": 2
        })
        print("=== [DEBUG] Initialisation du driver Chrome en mode headless...")
        self.driver = webdriver.Chrome(options=opt)
        self.driver.set_window_size(1920, 1080)

    # --- VERSION CORRIGÉE de login_with_cookies ---
    def login_with_cookies(self, meet_link):
        """
        Charge les cookies de session pour se connecter sans formulaire.
        Inclut un nettoyage des valeurs de 'sameSite' pour la compatibilité avec Selenium.
        """
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
                # --- SECTION DE NETTOYAGE ---
                # Si 'sameSite' n'existe pas ou n'est pas une des valeurs valides, on le supprime.
                # Selenium le gérera correctement. C'est plus sûr que de deviner la bonne valeur.
                if 'sameSite' not in cookie or cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                    if 'sameSite' in cookie:
                        print(f"--- [INFO] Cookie '{cookie['name']}' : valeur 'sameSite' ('{cookie['sameSite']}') invalide. Suppression de la clé.")
                        del cookie['sameSite']
                # -----------------------------
                
                try:
                    self.driver.add_cookie(cookie)
                except Exception as cookie_error:
                    # On ignore les cookies qui pourraient quand même poser problème (ex: domaine)
                    print(f"--- [AVERTISSEMENT] Impossible de charger un cookie : {cookie.get('name')} - Erreur: {cookie_error}")

            print("=== [DEBUG] Cookies chargés. Rafraîchissement de la page...")
            self.driver.refresh()
            time.sleep(5)
            print("=== [DEBUG] Connexion par cookies réussie.")

        except Exception as e:
            print(f"=== [ERREUR FATALE] Échec de la connexion par cookies : {e}")
            self.driver.quit()
            raise

    # ... le reste du code (join_meeting, main) est identique à la version précédente ...
    def join_meeting(self):
        try:
            join_button_xpath = "//button[.//span[contains(text(), 'Participer') or contains(text(), 'Demander')]]"
            print("=== [DEBUG] Attente du bouton pour rejoindre la réunion...")
            join_button = WebDriverWait(self.driver, 40).until(
                EC.element_to_be_clickable((By.XPATH, join_button_xpath))
            )
            print("=== [DEBUG] Clic sur le bouton pour rejoindre...")
            self.driver.execute_script("arguments[0].click();", join_button)
            print("=== [DEBUG] Demande de participation envoyée.")
        except TimeoutException:
            print("=== [ERREUR FATALE] Impossible de trouver le bouton pour rejoindre la réunion après 40 secondes.")
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
        obj.login_with_cookies(meet_link)
        obj.join_meeting()
        print("=== [INFO] Enregistrement audio démarré (simulation)...")
        time.sleep(duration)
        print("=== [INFO] Bot terminé avec succès. ===")
    finally:
        if 'driver' in obj.__dict__:
            obj.driver.quit()
            print("=== [DEBUG] Driver Chrome fermé.")

if __name__ == "__main__":
    main()
