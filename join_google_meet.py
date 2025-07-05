from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
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

    # VERSION FINALE DE turnOffMicCam - PLUS ROBUSTE
    def turnOffMicCam(self):
        print("=== [DEBUG] Initialisation de la désactivation micro/caméra...")
        
        # On attend que la page soit interactive en cherchant le bouton pour participer
        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Participer')]"))
            )
        except TimeoutException:
            print("=== [ERREUR] La page de pré-connexion ne s'est pas chargée en 30 secondes.")
            return

        # On boucle jusqu'à 5 fois pour s'assurer que tout est bien cliqué
        for i in range(5):
            # On cherche tous les pop-ups possibles et on les ferme
            try:
                dialog_buttons = self.driver.find_elements(By.XPATH, "//div[@role='alertdialog']//button")
                if dialog_buttons:
                    print(f"--- [INFO] Tentative {i+1}: Boîte de dialogue détectée, fermeture...")
                    for button in dialog_buttons:
                        try:
                            self.driver.execute_script("arguments[0].click();", button)
                        except:
                            pass # On ignore les erreurs si un bouton disparaît
                    time.sleep(1)
            except:
                pass

            try:
                # On ré-identifie les boutons à chaque boucle
                all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "div.U26fgb")
                mic_button, cam_button = all_buttons[0], all_buttons[1]

                # Vérifier si le micro est déjà désactivé (l'icône change)
                if "mic_off" not in mic_button.find_element(By.TAG_NAME, "i").text:
                    print(f"--- [INFO] Tentative {i+1}: Désactivation du micro...")
                    self.driver.execute_script("arguments[0].click();", mic_button)
                    time.sleep(0.5)
                
                # Vérifier si la caméra est déjà désactivée
                if "videocam_off" not in cam_button.find_element(By.TAG_NAME, "i").text:
                    print(f"--- [INFO] Tentative {i+1}: Désactivation de la caméra...")
                    self.driver.execute_script("arguments[0].click();", cam_button)
                    time.sleep(0.5)

                # Si les deux sont bien désactivés, on sort de la boucle
                if "mic_off" in all_buttons[0].find_element(By.TAG_NAME, "i").text and \
                   "videocam_off" in all_buttons[1].find_element(By.TAG_NAME, "i").text:
                    print("=== [DEBUG] Micro et Caméra désactivés avec succès.")
                    return # C'est gagné !
            
            except Exception as e:
                print(f"--- [AVERTISSEMENT] Erreur dans la boucle de la tentative {i+1}: {e.__class__.__name__}")
        
        print("=== [ERREUR GRAVE] Échec de la désactivation du micro/caméra après plusieurs tentatives.")


    def AskToJoin(self, audio_path, duration):
        # ... (cette fonction reste la même) ...
        try:
            time.sleep(5)
            join_button_xpath = "//button[.//span[contains(text(), 'Participer') or contains(text(), 'Demander')]]"
            join_button = WebDriverWait(self.driver, 40).until(
                EC.element_to_be_clickable((By.XPATH, join_button_xpath))
            )
            join_button.click()
            print("=== [DEBUG] Demande de rejoindre la réunion envoyée ou réunion rejointe.")
            time.sleep(10)
            #AudioRecorder().get_audio(audio_path, duration)
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
    # SpeechToText().transcribe(audio_path)

if __name__ == "__main__":
    print("=== [DEBUG] Script Python lancé ===")
    main()
