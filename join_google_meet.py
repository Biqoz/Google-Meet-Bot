from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

class JoinGoogleMeet:
    def __init__(self):
        # ... (le __init__ ne change pas) ...
        opt = Options()
        user_data_dir = tempfile.mkdtemp()
        opt.add_argument(f"--user-data-dir={user_data_dir}")
        opt.add_argument('--no-sandbox')
        opt.add_argument('--disable-dev-shm-usage')
        opt.add_argument('--headless=new')
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

    def load_cookies_and_go_to_meet(self, meet_link):
        # ... (cette fonction a bien fonctionné, on ne la change pas) ...
        try:
            print("=== [DEBUG] Tentative de connexion via les cookies...")
            print(f"=== [DEBUG] Navigation vers le lien Google Meet : {meet_link}")
            self.driver.get(meet_link)
            self.driver.implicitly_wait(5)
            cookies_path = "cookies.json"
            if not os.path.exists(cookies_path):
                print(f"=== [ERREUR] Le fichier {cookies_path} n'a pas été trouvé !")
                raise FileNotFoundError(f"Le fichier {cookies_path} est manquant.")
            with open(cookies_path, 'r') as f:
                cookies = json.load(f)
            print(f"=== [DEBUG] Chargement de {len(cookies)} cookies...")
            for cookie in cookies:
                if 'sameSite' in cookie and cookie['sameSite'] not in ('Strict', 'Lax', 'None'):
                    cookie['sameSite'] = 'Lax'
                try:
                    self.driver.add_cookie(cookie)
                except Exception as cookie_error:
                    print(f"--- [INFO] Impossible de charger un cookie : {cookie.get('name')} - Erreur: {cookie_error}")
            print("=== [DEBUG] Cookies chargés.")
            print("=== [DEBUG] Rafraîchissement de la page pour appliquer la session.")
            self.driver.refresh()
            self.driver.implicitly_wait(10)
            print("=== [DEBUG] Page Meet atteinte et connectée.")
        except Exception as e:
            print(f"=== [ERREUR] Erreur lors du chargement des cookies ou de la navigation.")
            print(f"Type d'erreur : {type(e)}")
            print(f"Message d'erreur : {e}")
            print("=== [DEBUG] HTML actuel ===")
            print(self.driver.page_source)
            raise

    # VERSION CORRIGÉE DE turnOffMicCam
    def turnOffMicCam(self):
        try:
            print("=== [DEBUG] Attente et désactivation micro/caméra...")
            
            # --- Étape 1 : Gérer la boîte de dialogue d'erreur potentielle ---
            try:
                # On attend maximum 10 secondes pour voir si le popup "Micro introuvable" apparaît
                dismiss_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Ignorer')]"))
                )
                print("=== [INFO] Boîte de dialogue 'Micro introuvable' détectée. Fermeture...")
                dismiss_button.click()
                time.sleep(2) # On attend que la boîte de dialogue disparaisse
            except TimeoutException:
                # Si le popup n'apparaît pas en 10s, c'est normal. On continue.
                print("=== [INFO] Aucune boîte de dialogue d'erreur micro/caméra détectée. On continue.")

            # --- Étape 2 : Désactiver micro et caméra ---
            # Utilisons des sélecteurs plus simples et directs
            all_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".U26fgb")
            
            # Désactiver le micro
            print("=== [DEBUG] Tentative de désactivation du micro...")
            mic_button = all_buttons[0]
            mic_button.click()
            print("=== [DEBUG] Micro désactivé")

            # Désactiver la caméra
            time.sleep(1)
            print("=== [DEBUG] Tentative de désactivation de la caméra...")
            cam_button = all_buttons[1]
            cam_button.click()
            print("=== [DEBUG] Caméra désactivée")

        except Exception as e:
            print(f"=== [DEBUG] Erreur lors de la désactivation micro/caméra : {e}")
            print("=== [DEBUG] HTML au moment de l'erreur turnOffMicCam ===")
            print(self.driver.page_source)
            # On continue, au cas où

    # ... AskToJoin reste la même pour l'instant ...
    def AskToJoin(self, audio_path, duration):
        try:
            time.sleep(5)
            join_button = WebDriverWait(self.driver, 40).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Participer')] | //button[contains(., 'Demander')]"))
            )
            join_button.click()
            print("=== [DEBUG] Demande de rejoindre la réunion envoyée ou réunion rejointe.")
            time.sleep(10)
            AudioRecorder().get_audio(audio_path, duration)
        except Exception as e:
            print(f"=== [DEBUG] Erreur lors de la demande pour rejoindre : {e}")
            print("=== [DEBUG] HTML au moment de l'erreur AskToJoin ===")
            print(self.driver.page_source)
            
# ... la fonction main() reste identique ...
def main():
    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "output.wav")
    meet_link = os.getenv('MEET_LINK')
    duration = int(os.getenv('RECORDING_DURATION', 60))
    
    obj = JoinGoogleMeet()
    obj.load_cookies_and_go_to_meet(meet_link)
    obj.turnOffMicCam()
    obj.AskToJoin(audio_path, duration)
    # SpeechToText().transcribe(audio_path) # commenté pour le moment pour accélérer les tests

if __name__ == "__main__":
    print("=== [DEBUG] Script Python lancé ===")
    main()
