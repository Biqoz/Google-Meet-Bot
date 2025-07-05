# Fichier : record_audio.py
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

class AudioRecorder:
    def __init__(self):
        self.sample_rate = int(os.getenv('SAMPLE_RATE', 44100))

    def get_audio(self, filename, duration):
        print(f"=== [AUDIO] Démarrage de l'enregistrement système pour {duration} secondes...")
        print(f"=== [AUDIO] Fichier de sortie : {filename}")

        command = [
            'ffmpeg',
            '-y',                 # Écraser le fichier de sortie s'il existe
            '-f', 'pulse',        # Format d'entrée : PulseAudio
            '-i', 'auto_null.monitor', # Source : le moniteur de sortie virtuel
            '-t', str(duration),  # Durée de l'enregistrement
            '-ac', '2',           # 2 canaux (stéréo)
            '-ar', str(self.sample_rate), # Taux d'échantillonnage
            filename
        ]
        
        try:
            print(f"=== [AUDIO] Lancement de la commande ffmpeg: {' '.join(command)}")
            process = subprocess.run(
                command,
                check=True,  # Lève une erreur si ffmpeg échoue
                capture_output=True, # Capture la sortie standard et l'erreur
                text=True # Encode la sortie en texte
            )
            print(f"=== [SUCCÈS] Enregistrement ffmpeg terminé.")
            print(f"--- FFMPEG Stdout ---\n{process.stdout}\n---------------------")
        except subprocess.CalledProcessError as e:
            print("=== [ERREUR AUDIO] Le processus ffmpeg a échoué.")
            print(f"--- FFMPEG Return Code: {e.returncode} ---")
            print(f"--- FFMPEG Stdout ---\n{e.stdout}\n---------------------")
            print(f"--- FFMPEG Stderr ---\n{e.stderr}\n---------------------")
        except FileNotFoundError:
            print("=== [ERREUR AUDIO] Commande 'ffmpeg' introuvable. Est-elle bien installée dans le Dockerfile ?")
        except Exception as e:
            print(f"=== [ERREUR AUDIO] Une erreur inattendue est survenue pendant l'enregistrement : {e}")
