# Fichier : join_google_meet.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import os
from dotenv import load_dotenv

from record_audio import AudioRecorder
from speech_to_text import SpeechToText

load_dotenv()

class JoinGoogleMeet:
    def __init__(self):
        print("=== [BOT_INIT] Initialisation...")
        opt = Options()
        opt.add_argument('--no-sandbox')
        opt.add_argument('--disable-dev-shm-usage')
        opt.add_argument('--headless=new')
        opt.add_argument('--start-maximized')
        opt.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
        opt.add_argument('--disable-blink-features=AutomationControlled')
        
        opt.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.notifications": 2
        })
        
        print("=== [DRIVER_INIT] Lancement du driver Chrome...")
        self.driver = webdriver.Chrome(options=opt)
        self.driver.set_window_size(1920, 1080)
        print("=== [DRIVER_INIT] Driver initialisé.")

    def login_with_cookies(self, meet_link):
        try:
            print(f"=== [LOGIN] Navigation vers {meet_link}")
            self.driver.get(meet_link)
            time.sleep(2)
            cookies_path = "cookies.json"
            if not os.path.exists(cookies_path):
                raise FileNotFoundError(f"'{cookies_path}' introuvable.")
            with open(cookies_path, 'r') as f:
                cookies = json.load(f)
            
            print(f"=== [LOGIN] Injection de {len(cookies)} cookies...")
            for cookie in cookies:
                if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                    del cookie['sameSite']
                self.driver.add_cookie(cookie)
            
            print("=== [LOGIN] Rafraîchissement pour activer la session...")
            self.driver.refresh()
            time.sleep(5)
            print("=== [LOGIN] Connexion réussie.")
        except Exception as e:
            print(f"=== [ERREUR_FATALE] Échec de la connexion par cookies : {e}")
            raise

    def get_participant_count(self):
        """Tente de récupérer le nombre de participants. Retourne -1 si non trouvé."""
        try:
            # Sélecteur pour l'icône qui contient le nombre de participants
            participant_button_xpath = "//div[contains(@aria-label, 'Participants') and @role='button']"
            participant_element = self.driver.find_element(By.XPATH, participant_button_xpath)
            # Le nombre est souvent dans un span à l'intérieur de ce bouton
            count_element = participant_element.find_element(By.CSS_SELECTOR, "span.axUSLb")
            return int(count_element.text)
        except (NoSuchElementException, ValueError):
            # Si l'élément n'est pas trouvé ou n'est pas un nombre, la réunion est probablement terminée ou l'interface a changé.
            return -1

    def monitor_and_record(self, audio_path):
        """Rejoint, lance l'enregistrement et surveille la fin de la réunion."""
        recording_process = None
        recorder = AudioRecorder()
        try:
            # --- Rejoindre la réunion ---
            join_button_xpath = "//button[.//span[contains(text(), 'Participer') or contains(text(), 'Demander')]]"
            print("=== [MEET] Attente du bouton pour rejoindre...")
            join_button = WebDriverWait(self.driver, 40).until(EC.element_to_be_clickable((By.XPATH, join_button_xpath)))
            self.driver.execute_script("arguments[0].click();", join_button)
            print("=== [MEET] Demande de participation envoyée.")
            time.sleep(10)

            # --- Démarrer l'enregistrement ---
            recording_process = recorder.get_audio_background(audio_path)
            if not recording_process:
                raise Exception("Le processus d'enregistrement ffmpeg n'a pas pu démarrer.")
            
            # --- Boucle de surveillance ---
            print("=== [MONITORING] Surveillance commencée. Vérification toutes les 60 secondes.")
            empty_checks = 0
            max_empty_checks = 3  # Arrêter après 3 vérifications où le bot est seul

            while True:
                time.sleep(60)
                count = self.get_participant_count()

                if count == -1:
                    print("=== [MONITORING] Compteur de participants introuvable. La réunion est considérée comme terminée.")
                    break
                
                print(f"--- [MONITORING_TICK] Participants: {count}")
                if count <= 1:
                    empty_checks += 1
                    print(f"--- [MONITORING_TICK] Le bot est seul. Vérification {empty_checks}/{max_empty_checks}.")
                    if empty_checks >= max_empty_checks:
                        print("=== [MONITORING] Le bot est seul depuis 3 minutes. Fin de la réunion.")
                        break
                else:
                    empty_checks = 0 # Réinitialiser si quelqu'un est présent

        finally:
            # --- Arrêter proprement l'enregistrement ---
            if recording_process:
                print("=== [AUDIO_STOP] Arrêt du processus d'enregistrement...")
                recorder.stop_audio_background(recording_process)
            
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 44:
                print(f"=== [FILE_OK] Fichier audio finalisé: {audio_path}")
            else:
                print(f"=== [FILE_FAIL] Le fichier audio est vide ou manquant.")


def main():
    print("=== [MAIN] Script démarré. ===")
    
    # Configuration
    recordings_dir = "/app/recordings"
    os.makedirs(recordings_dir, exist_ok=True)
    timestr = time.strftime("%Y%m%d-%H%M%S")
    audio_path = os.path.join(recordings_dir, f"recording-{timestr}.wav")
    meet_link = os.getenv('MEET_LINK')

    if not meet_link:
        print("=== [ERREUR_FATALE] MEET_LINK n'est pas défini.")
        return

    print(f"=== [INFO] Lien Meet: {meet_link}")
    
    obj = None
    try:
        obj = JoinGoogleMeet()
        obj.login_with_cookies(meet_link)
        obj.monitor_and_record(audio_path)

        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 44:
            print("=== [TRANSCRIPTION] Lancement de la transcription...")
            transcriber = SpeechToText()
            transcriber.transcribe(audio_path)
            print("=== [TRANSCRIPTION] Tâche terminée.")
        else:
            print("=== [TRANSCRIPTION] Fichier audio invalide, étape ignorée.")
        
        print("\n=== [SUCCÈS] Le bot a terminé sa mission. ===\n")

    except Exception as e:
        print(f"=== [ERREUR_FATALE] Le script principal a échoué : {e}")
    finally:
        if obj and hasattr(obj, 'driver'):
            obj.driver.quit()
        print("=== [FIN] Fin du script. ===")

if __name__ == "__main__":
    main()
