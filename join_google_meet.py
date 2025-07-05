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
    # ... __init__ et load_cookies_and_go_to_meet restent les mêmes ...
    def __init__(self):
        # La configuration du driver reste la même
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

    # NOUVELLE FONCTION UTILITAIRE POUR FERMER LES POPUPS
    def dismiss_any_modal_dialog(self):
        """Cherche et ferme n'importe quelle boîte de dialogue modale qui pourrait apparaître."""
        try:
            # Sélecteur robuste pour le bouton "Ignorer" dans un dialogue
            dismiss_button_xpath = "//div[@role='alertdialog']//button"
            dismiss_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, dismiss_button_xpath))
            )
            print("=== [INFO] Boîte de dialogue modale détectée. Fermeture...")
            self.driver.execute_script("arguments[0].click();", dismiss_button)
            print("=== [INFO] Boîte de dialogue fermée.")
            time.sleep(2)  # Attendre que l'animation de fermeture se termine
        except TimeoutException:
            # C'est le cas normal si aucun popup n'apparaît.
            print("=== [INFO] Aucune boîte de dialogue modale n'est apparue.")
        except Exception as e:
            print(f"=== [AVERTISSEMENT] Impossible de fermer la boîte de dialogue : {e}")


    # VERSION AMÉLIORÉE DE turnOffMicCam
    def turnOffMicCam(self):
        try:
            print("=== [DEBUG] Attente et désactivation micro/caméra...")
            
            # Attendre que les boutons soient globalement présents
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.U26fgb"))
            )
            time.sleep(3) # Laisse le temps à l'interface de se stabiliser

            # On vérifie une première fois s'il y a des popups
            self.dismiss_any_modal_dialog()

            # --- Désactiver le Micro ---
            # Sélecteur ciblant le bouton du micro, quel que soit son état (activé/désactivé)
            mic_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[@data-promo-anchor-id='Wj0DQc']"))
            )
            print("=== [DEBUG] Tentative de désactivation du micro...")
            self.driver.execute_script("arguments[0].click();", mic_button)
            print("=== [DEBUG] Micro désactivé.")
            
            # On vérifie A NOUVEAU, juste au cas où le premier clic a déclenché un popup
            self.dismiss_any_modal_dialog()

            # --- Désactiver la Caméra ---
            # Sélecteur ciblant le bouton de la caméra
            cam_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[@data-promo-anchor-id='yhZxwc']"))
            )
            print("=== [DEBUG] Tentative de désactivation de la caméra...")
            self.driver.execute_script("arguments[0].click();", cam_button)
            print("=== [DEBUG] Caméra désactivée.")
            
            # Ultime vérification
            self.dismiss_any_modal_dialog()

        except Exception as e:
            print(f"=== [ERREUR GRAVE] Échec lors de la désactivation micro/caméra : {e}")
            print("=== [DEBUG] HTML au moment de l'erreur turnOffMicCam ===")
            print(self.driver.page_source)
            # On continue, car ce n'est pas forcément bloquant pour la suite
    
    # ... le reste du code (AskToJoin, main, etc.) ne change pas ...
    def AskToJoin(self, audio_path, duration):
        try:
            time.sleep(5)
            # Utilisons un sélecteur plus fiable qui cherche le bouton par son texte
            join_button_xpath = "//button[.//span[contains(text(), 'Participer') or contains(text(), 'Demander')]]"
            join_button = WebDriverWait(self.driver, 40).until(
                EC.element_to_be_clickable((By.XPATH, join_button_xpath))
            )
            join_button.click()
            
            print("=== [DEBUG] Demande de rejoindre la réunion envoyée ou réunion rejointe.")
            
            time.sleep(10) # Attendre d'être bien dans la salle
            
            #AudioRecorder().get_audio(audio_path, duration) # Commenté pour des tests plus rapides
        except Exception as e:
            print(f"=== [DEBUG] Erreur lors de la demande pour rejoindre : {e}")
            print("=== [DEBUG] HTML au moment de l'erreur AskToJoin ===")
            print(self.driver.page_source)

def main():
    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "output.wav")
    meet_link = os.getenv('MEET_LINK')
    duration = int(os.getenv('RECORDING_DURATION', 60))
    
    obj = JoinGoogleMeet()
    
    obj.load_cookies_and_go_to_meet(meet_link)
    obj.turnOffMicCam()
    obj.AskToJoin(audio_path, duration)
    # SpeechToText().transcribe(audio_path) # commenté pour le moment

if __name__ == "__main__":
    print("=== [DEBUG] Script Python lancé ===")
    main()
