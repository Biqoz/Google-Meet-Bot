import sys
import traceback
import os
import tempfile
import json
from dotenv import load_dotenv

# Gestion globale des exceptions pour tout afficher dans les logs
def global_excepthook(type, value, tb):
    print("=== [DEBUG] Exception non gérée détectée ===")
    traceback.print_exception(type, value, tb)
    sys.exit(1)

sys.excepthook = global_excepthook

print("=== [DEBUG] Script Python importé ===")

# Imports Selenium et autres modules après avoir fixé l'excepthook
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import time

# Modules du projet
from record_audio import AudioRecorder
from speech_to_text import SpeechToText

load_dotenv()

# DEBUG : Afficher toutes les variables d'environnement utiles
print("=== [DEBUG] Démarrage du bot Google Meet ===")
print(f"EMAIL_ID: {os.getenv('EMAIL_ID')}")
print(f"MEET_LINK: {os.getenv('MEET_LINK')}")
print(f"OPENAI_API_KEY présent: {'Oui' if os.getenv('OPENAI_API_KEY') else 'Non'}")
print(f"GPT_MODEL: {os.getenv('GPT_MODEL')}")
print(f"WHISPER_MODEL: {os.getenv('WHISPER_MODEL')}")
print(f"RECORDING_DURATION: {os.getenv('RECORDING_DURATION')}")
print(f"MAX_AUDIO_SIZE_BYTES: {os.getenv('MAX_AUDIO_SIZE_BYTES')}")
print(f"SAMPLE_RATE: {os.getenv('SAMPLE_RATE')}")
print(f"COOKIES_PATH: {os.getenv('COOKIES_PATH')}")

def load_cookies(driver, cookies_path):
    print(f"=== [DEBUG] Chargement des cookies depuis {cookies_path}")
    with open(cookies_path, 'r') as f:
        cookies = json.load(f)
    for cookie in cookies:
        # Nettoyage des champs non supportés par Selenium
        for key in ['sameSite', 'storeId', 'hostOnly', 'session']:
            cookie.pop(key, None)
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Erreur lors de l'ajout du cookie: {e}")

class JoinGoogleMeet:
    def __init__(self, cookies_path=None):
        opt = Options()
        user_data_dir = tempfile.mkdtemp()
        opt.add_argument(f"--user-data-dir={user_data_dir}")
        opt.add_argument('--no-sandbox')
        opt.add_argument('--disable-dev-shm-usage')
        opt.add_argument('--headless=new')
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

        # Charger les cookies si chemin fourni
        if cookies_path:
            self.driver.get('https://accounts.google.com')
            load_cookies(self.driver, cookies_path)
            self.driver.get('https://mail.google.com')
            print("=== [DEBUG] Cookies chargés et session Google restaurée")

    def Glogin(self):
        # Si on utilise les cookies, on ne fait pas le login manuel
        cookies_path = os.getenv('COOKIES_PATH')
        if cookies_path:
            print("=== [DEBUG] Utilisation des cookies, login manuel ignoré ===")
            return
        try:
            print("=== [DEBUG] Tentative de connexion Google (manuel)...")
            self.driver.get(
                'https://accounts.google.com/ServiceLogin?hl=en&passive=true&continue=https://www.google.com/&ec=GAZAAQ')
            self.driver.find_element(By.ID, "identifierId").send_keys(os.getenv('EMAIL_ID'))
            self.driver.find_element(By.ID, "identifierNext").click()
            self.driver.implicitly_wait(10)
            password_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "Passwd"))
            )
            password_input.send_keys(os.getenv('EMAIL_PASSWORD'))
            self.driver.implicitly_wait(10)
            self.driver.find_element(By.ID, "passwordNext").click()
            self.driver.implicitly_wait(10)    
            self.driver.get('https://google.com/')
            self.driver.implicitly_wait(100)
            print("=== [DEBUG] Connexion Google réussie !")
        except Exception as e:
            print("=== [DEBUG] HTML actuel ===")
            print(self.driver.page_source)
            print(f"=== [DEBUG] Connexion Google échouée ! Erreur: {e}")
            raise

    def turnOffMicCam(self, meet_link):
        try:
            print("=== [DEBUG] Navigation vers le lien Google Meet...")
            self.driver.get(meet_link)
            time.sleep(2)
            self.driver.find_element(By.CSS_SELECTOR, 'div[jscontroller="t2mBxb"][data-anchor-id="hw0c9"]').click()
            self.driver.implicitly_wait(3000)
            print("=== [DEBUG] Micro désactivé")
            time.sleep(1)
            self.driver.find_element(By.CSS_SELECTOR, 'div[jscontroller="bwqwSd"][data-anchor-id="psRWwc"]').click()
            self.driver.implicitly_wait(3000)
            print("=== [DEBUG] Caméra désactivée")
        except Exception as e:
            print(f"=== [DEBUG] Erreur lors de la désactivation micro/caméra : {e}")

    def checkIfJoined(self):
        try:
            join_button = WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.uArJ5e.UQuaGc.Y5sE8d.uyXBBb.xKiqt'))
            )
            print("=== [DEBUG] Réunion rejointe")
        except (TimeoutException, NoSuchElementException):
            print("=== [DEBUG] Réunion NON rejointe")

    def AskToJoin(self, audio_path, duration):
        try:
            time.sleep(5)
            self.driver.implicitly_wait(2000)
            self.driver.find_element(By.CSS_SELECTOR, 'button[jsname="Qx7uuf"]').click()
            print("=== [DEBUG] Demande de rejoindre la réunion envoyée")
            AudioRecorder().get_audio(audio_path, duration)
        except Exception as e:
            print(f"=== [DEBUG] Erreur lors de la demande de rejoindre : {e}")

def main():
    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "output.wav")
    meet_link = os.getenv('MEET_LINK')
    duration = int(os.getenv('RECORDING_DURATION', 60))
    cookies_path = os.getenv('COOKIES_PATH')
    obj = JoinGoogleMeet(cookies_path=cookies_path)
    obj.Glogin()
    obj.turnOffMicCam(meet_link)
    obj.AskToJoin(audio_path, duration)
    SpeechToText().transcribe(audio_path)

if __name__ == "__main__":
    print("=== [DEBUG] Script Python lancé ===")
    try:
        main()
    except Exception as e:
        print(f"=== [DEBUG] Exception au démarrage : {e}")
        traceback.print_exc()
