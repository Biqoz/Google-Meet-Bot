from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from record_audio import AudioRecorder
from speech_to_text import SpeechToText
import os
import json # <--- IMPORTER LA LIBRAIRIE JSON
import tempfile
from dotenv import load_dotenv

load_dotenv()

# ... (vos print de DEBUG restent les mêmes) ...
print("=== [DEBUG] Démarrage du bot Google Meet ===")
print(f"EMAIL_ID: {os.getenv('EMAIL_ID')}")
print(f"MEET_LINK: {os.getenv('MEET_LINK')}")
# etc.

class JoinGoogleMeet:
    def __init__(self):
        # La configuration du driver reste la même
        opt = Options()
        user_data_dir = tempfile.mkdtemp()
        opt.add_argument(f"--user-data-dir={user_data_dir}")
        opt.add_argument('--no-sandbox')
        opt.add_argument('--disable-dev-shm-usage')
        opt.add_argument('--headless=new')
        # On peut essayer d'ajouter un User-Agent pour paraître plus humain
        opt.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        opt.add_argument('--disable-blink-features=AutomationControlled')
        opt.add_argument('--start-maximized')
        opt.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.geolocation": 0,
            "profile.default_content_setting_values.notifications": 1
        })
        print(f"=== [DEBUG] Profil Chrome utilisé: {user_data_dir}")
        self.driver = webdriver.Chrome(options=opt)

    # L'ANCIENNE FONCTION Glogin n'est plus utile
    # def Glogin(self): ...

    # NOUVELLE FONCTION POUR CHARGER LES COOKIES
    def load_cookies_and_go_to_meet(self, meet_link):
        try:
            print("=== [DEBUG] Tentative de connexion via les cookies...")
            # 1. Aller sur le domaine principal pour pouvoir charger les cookies
            self.driver.get("https://google.com")
            
            # 2. Charger les cookies depuis le fichier
            cookies_path = "cookies.json"
            if not os.path.exists(cookies_path):
                print(f"=== [ERREUR] Le fichier {cookies_path} n'a pas été trouvé !")
                raise FileNotFoundError(f"Le fichier {cookies_path} est manquant.")

            with open(cookies_path, 'r') as f:
                cookies = json.load(f)

            for cookie in cookies:
                # Certains cookies peuvent ne pas avoir 'sameSite', ce qui peut causer une erreur
                if 'sameSite' not in cookie:
                    cookie['sameSite'] = 'None' # ou 'Strict' ou 'Lax' selon le cookie
                self.driver.add_cookie(cookie)
            
            print("=== [DEBUG] Cookies chargés avec succès.")
            
            # 3. Maintenant, aller directement au lien du Meet
            print("=== [DEBUG] Navigation vers le lien Google Meet...")
            self.driver.get(meet_link)
            self.driver.implicitly_wait(10)
            print("=== [DEBUG] Page Meet atteinte.")
            
        except Exception as e:
            print(f"=== [DEBUG] Erreur lors du chargement des cookies ou de la navigation : {e}")
            print("=== [DEBUG] HTML actuel ===")
            print(self.driver.page_source)
            raise
 
    def turnOffMicCam(self): # Note : le paramètre meet_link n'est plus nécessaire ici
        try:
            print("=== [DEBUG] Attente de la page de pré-connexion...")
            time.sleep(5) # Laisser un peu de temps à la page pour se charger complètement

            # Les sélecteurs pour le micro et la caméra peuvent changer. Il faudra peut-être les ajuster.
            # Voici des sélecteurs plus robustes basés sur les attributs aria-label ou jsname
            
            # Désactiver le micro
            print("=== [DEBUG] Tentative de désactivation du micro...")
            mic_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-promo-anchor-id="Wj0DQc"] button[aria-label*="microphone"]'))
            )
            mic_button.click()
            print("=== [DEBUG] Micro désactivé")
            
            # Désactiver la caméra
            time.sleep(2)
            print("=== [DEBUG] Tentative de désactivation de la caméra...")
            cam_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-promo-anchor-id="Wj0DQc"] button[aria-label*="camera"]'))
            )
            cam_button.click()
            print("=== [DEBUG] Caméra désactivée")

        except Exception as e:
            print(f"=== [DEBUG] Erreur lors de la désactivation micro/caméra : {e}")
            print("=== [DEBUG] HTML actuel lors de l'erreur turnOffMicCam ===")
            print(self.driver.page_source)
            # Ne pas relancer l'erreur ici, on peut peut-être continuer même si ça échoue
 
    def AskToJoin(self, audio_path, duration):
        try:
            time.sleep(5)
            # Le bouton "Demander à participer" ou "Participer"
            join_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[jsname="Qx7uuf"]'))
            )
            join_button.click()
            
            print("=== [DEBUG] Demande de rejoindre la réunion envoyée ou réunion rejointe.")
            
            # Attendre un peu pour être sûr d'être dans la réunion avant d'enregistrer
            time.sleep(10)
            
            AudioRecorder().get_audio(audio_path, duration)
        except Exception as e:
            print(f"=== [DEBUG] Erreur lors de la demande pour rejoindre : {e}")
            print("=== [DEBUG] HTML actuel lors de l'erreur AskToJoin ===")
            print(self.driver.page_source)

def main():
    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "output.wav")
    meet_link = os.getenv('MEET_LINK')
    duration = int(os.getenv('RECORDING_DURATION', 60))
    
    obj = JoinGoogleMeet()
    
    # MODIFICATION : On n'appelle plus Glogin(), mais la nouvelle fonction
    obj.load_cookies_and_go_to_meet(meet_link)
    
    obj.turnOffMicCam() # Plus besoin de passer le lien ici
    obj.AskToJoin(audio_path, duration)
    SpeechToText().transcribe(audio_path)

if __name__ == "__main__":
    print("=== [DEBUG] Script Python lancé ===")
    main()
