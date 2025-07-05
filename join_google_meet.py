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

# Assurez-vous que ces fichiers existent et sont dans le même dossier
from record_audio import AudioRecorder
from speech_to_text import SpeechToText

# Charger les variables d'environnement (depuis Coolify ou .env)
load_dotenv()

class JoinGoogleMeet:
    def __init__(self):
        print("=== [BOT_INIT] Initialisation de la classe JoinGoogleMeet ===")
        opt = Options()
        opt.add_argument('--no-sandbox')
        opt.add_argument('--disable-dev-shm-usage')
        opt.add_argument('--headless=new')
        opt.add_argument('--start-maximized')
        opt.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
        opt.add_argument('--disable-blink-features=AutomationControlled')
        
        # Bloquer les périphériques au niveau du navigateur pour éviter les pop-ups
        opt.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.notifications": 2
        })
        
        print("=== [DRIVER_INIT] Lancement du driver Chrome en mode headless...")
        self.driver = webdriver.Chrome(options=opt)
        self.driver.set_window_size(1920, 1080)
        print("=== [DRIVER_INIT] Driver initialisé et fenetre configurée.")

    def login_with_cookies(self, meet_link):
        """Charge les cookies de session pour se connecter sans formulaire."""
        try:
            print(f"=== [LOGIN] Navigation vers le lien Google Meet : {meet_link}")
            self.driver.get(meet_link)
            print("=== [LOGIN] Page atteinte, attente de 2 secondes...")
            time.sleep(2)

            cookies_path = "cookies.json"
            if not os.path.exists(cookies_path):
                raise FileNotFoundError(f"Le fichier de cookies '{cookies_path}' est introuvable.")

            with open(cookies_path, 'r') as f:
                cookies = json.load(f)
            
            print(f"=== [LOGIN] Nettoyage et chargement de {len(cookies)} cookies...")
            for cookie in cookies:
                if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                    del cookie['sameSite']
                self.driver.add_cookie(cookie)

            print("=== [LOGIN] Cookies injectés. Rafraîchissement de la page pour activer la session...")
            self.driver.refresh()
            print("=== [LOGIN] Attente de 5 secondes post-rafraîchissement...")
            time.sleep(5)
            print("=== [LOGIN] Connexion par cookies terminée avec succès.")

        except Exception as e:
            print(f"=== [ERREUR_FATALE] Échec de la connexion par cookies : {e}")
            self.driver.quit()
            raise

    def monitor_and_record(self, audio_path):
        """Rejoint, lance l'enregistrement et surveille la réunion jusqu'à ce qu'elle soit vide."""
        recording_process = None
        recorder = AudioRecorder()
        try:
            # --- Rejoindre la réunion ---
            join_button_xpath = "//button[.//span[contains(text(), 'Participer') or contains(text(), 'Demander')]]"
            print("=== [MEET_JOIN] Attente du bouton pour rejoindre (max 40s)...")
            join_button = WebDriverWait(self.driver, 40).until(
                EC.element_to_be_clickable((By.XPATH, join_button_xpath))
            )
            print("=== [MEET_JOIN] Bouton trouvé. Clic pour rejoindre...")
            self.driver.execute_script("arguments[0].click();", join_button)
            print("=== [MEET_JOIN] Demande de participation envoyée.")
            
            print("=== [MEET_STABILIZE] Attente de 10s pour la stabilisation de la connexion...")
            time.sleep(10)

            # --- Lancer l'enregistrement en tâche de fond ---
            recording_process = recorder.get_audio_background(audio_path)
            if not recording_process:
                raise Exception("Le processus d'enregistrement n'a pas pu démarrer.")
            
            # --- Boucle de surveillance ---
            print("=== [MONITORING] Surveillance de la réunion commencée. Vérification toutes les 60 secondes.")
            empty_meeting_counter = 0
            while True:
                time.sleep(60)
                try:
                    participant_count_xpath = "//div[@role='button' and @aria-label[contains(.,'Participants')]]//span[contains(@class, 'axUSLb')]"
                    participant_element = self.driver.find_element(By.XPATH, participant_count_xpath)
                    count = int(participant_element.text)
                    print(f"--- [MONITORING_TICK] Participants actuels : {count}")
                    
                    if count <= 1: # Si le bot est seul
                        empty_meeting_counter += 1
                        print(f"--- [MONITORING_TICK] Le bot est seul. Compteur de vérification : {empty_meeting_counter}/3.")
                        if empty_meeting_counter >= 3:
                            print("=== [MONITORING] Le bot est seul depuis 3 minutes. Fin de la réunion.")
                            break
                    else:
                        empty_meeting_counter = 0 # On réinitialise le compteur s'il y a du monde

                except NoSuchElementException:
                    print("=== [MONITORING_END] Impossible de trouver le compteur de participants. La réunion semble terminée.")
                    break
                except Exception as e:
                    print(f"--- [AVERTISSEMENT] Erreur de surveillance non critique : {e}. La surveillance continue...")

        finally:
            # --- Arrêter proprement l'enregistrement ---
            if recording_process:
                print("=== [RECORD_STOP] Arrêt du processus d'enregistrement...")
                recorder.stop_audio_background(recording_process)
            
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 44:
                print(f"=== [FILE_SUCCESS] Fichier audio finalisé avec succès : {audio_path}")
            else:
                print(f"=== [FILE_FAILURE] Le fichier audio final est vide ou n'a pas été créé.")


def main():
    print("=== [MAIN] Démarrage de la fonction main() ===")
    
    # --- Configuration ---
    recordings_dir = "/app/recordings"
    os.makedirs(recordings_dir, exist_ok=True)
    timestr = time.strftime("%Y%m%d-%H%M%S")
    audio_path = os.path.join(recordings_dir, f"recording-{timestr}.wav")
    
    meet_link = os.getenv('MEET_LINK')
    duration_str = os.getenv('RECORDING_DURATION', '18000') # Durée maximale, la surveillance l'arrêtera avant
    duration = int(duration_str)

    if not meet_link:
        print("=== [ERREUR_FATALE] Variable d'environnement MEET_LINK manquante.")
        return

    print("=== [INFO] Lancement du bot Google Meet ===")
    print(f"=== [INFO] Lien de la réunion : {meet_link}")
    print(f"=== [INFO] Durée maximale d'enregistrement : {duration} secondes")
    print(f"=== [INFO] Chemin de sauvegarde du fichier : {audio_path}")
    
    obj = None
    try:
        # --- Étape 1 : Connexion et Enregistrement ---
        obj = JoinGoogleMeet()
        obj.login_with_cookies(meet_link)
        obj.monitor_and_record(audio_path)

        # --- Étape 2 : Transcription et Résumé ---
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 44:
            print("=== [TRANSCRIPTION_START] Lancement de la transcription avec Whisper...")
            transcriber = SpeechToText()
            transcriber.transcribe(audio_path) 
            print("=== [TRANSCRIPTION_END] Transcription et résumé terminés.")
        else:
            print("=== [TRANSCRIPTION_SKIP] Fichier audio vide ou manquant, transcription ignorée.")
        
        print("\n=== [SUCCÈS] Le bot a terminé toutes ses tâches. ===\n")

    except Exception as e:
        print(f"=== [ERREUR_MAIN] Une erreur non gérée a arrêté le processus principal : {e}")
    finally:
        if obj and hasattr(obj, 'driver'):
            obj.driver.quit()
            print("=== [DEBUG] Driver Chrome fermé.")
        print("=== [INFO] Fin du script. ===")

if __name__ == "__main__":
    main()
