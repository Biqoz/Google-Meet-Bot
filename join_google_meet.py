import json
import os
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import time
from record_audio import AudioRecorder
from speech_to_text import SpeechToText

load_dotenv()

def load_cookies(driver, cookies_path):
    with open(cookies_path, 'r') as f:
        cookies = json.load(f)
    for cookie in cookies:
        cookie.pop('sameSite', None)
        cookie.pop('storeId', None)
        cookie.pop('hostOnly', None)
        cookie.pop('session', None)
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Erreur lors de l'ajout du cookie: {e}")

class JoinGoogleMeet:
    def __init__(self, cookies_path=None):
        self.mail_address = os.getenv('EMAIL_ID')
        self.password = os.getenv('EMAIL_PASSWORD')
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
            print(f"=== [DEBUG] Chargement des cookies depuis {cookies_path}")
            self.driver.get('https://accounts.google.com')
            load_cookies(self.driver, cookies_path)
            self.driver.get('https://mail.google.com')
            print("=== [DEBUG] Cookies chargés et session Google restaurée")

    def Glogin(self):
        # Si on utilise les cookies, on ne fait pas le login manuel
        try:
            print("=== [DEBUG] Tentative de connexion Google (manuel)...")
            self.driver.get(
                'https://accounts.google.com/ServiceLogin?hl=en&passive=true&continue=https://www.google.com/&ec=GAZAAQ')
            self.driver.find_element(By.ID, "identifierId").send_keys(self.mail_address)
            self.driver.find_element(By.ID, "identifierNext").click()
            self.driver.implicitly_wait(10)
            password_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "Passwd"))
            )
            password_input.send_keys(self.password)
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
    cookies_path = os.getenv('COOKIES_PATH')  # Variable d'environnement à définir dans Coolify

    obj = JoinGoogleMeet(cookies_path=cookies_path)

    # Si les cookies sont chargés, on saute le login manuel
    if cookies_path:
        print("=== [DEBUG] Utilisation des cookies, login manuel ignoré ===")
    else:
        obj.Glogin()

    obj.turnOffMicCam(meet_link)
    obj.AskToJoin(audio_path, duration)
    SpeechToText().transcribe(audio_path)

if __name__ == "__main__":
    print("=== [DEBUG] Script Python lancé ===")
    main()
