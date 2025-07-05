# Fichier : record_audio.py
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

class AudioRecorder:
    def __init__(self):
        self.sample_rate = int(os.getenv('SAMPLE_RATE', 44100))
        print("=== [AUDIO_RECORDER] Classe AudioRecorder initialisée.")

    def get_audio_background(self, filename):
        """
        Lance l'enregistrement en arrière-plan et retourne le processus pour pouvoir le gérer plus tard.
        """
        print(f"=== [AUDIO] Préparation de l'enregistrement en arrière-plan...")
        print(f"=== [AUDIO] Fichier de sortie prévu : {filename}")

        # La commande ffmpeg pour capturer le son du "moniteur" PulseAudio.
        # Note : On n'utilise plus '-t' (durée) car on arrêtera le processus manuellement.
        command = [
            'ffmpeg',
            '-y',                     # Écraser le fichier de sortie s'il existe
            '-f', 'pulse',            # Format d'entrée : PulseAudio
            '-i', 'auto_null.monitor',# Source : le moniteur de sortie virtuel
            '-ac', '2',               # Canaux : stéréo
            '-ar', str(self.sample_rate), # Taux d'échantillonnage
            '-loglevel', 'info',      # Niveau de log de ffmpeg
            filename
        ]
        
        try:
            # On utilise Popen pour lancer le processus sans bloquer le script
            print(f"=== [AUDIO] Lancement de la commande ffmpeg: {' '.join(command)}")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,  # On capture la sortie standard...
                stderr=subprocess.PIPE   # ...et la sortie d'erreur pour le débogage.
            )
            print(f"=== [AUDIO] Enregistrement démarré en arrière-plan. PID du processus ffmpeg : {process.pid}")
            return process

        except FileNotFoundError:
            print("=== [ERREUR FATALE] Commande 'ffmpeg' introuvable. Vérifiez son installation dans le Dockerfile.")
            return None
        except Exception as e:
            print(f"=== [ERREUR FATALE] Impossible de lancer le processus d'enregistrement ffmpeg : {e}")
            return None

    def stop_audio_background(self, process):
        """
        Arrête proprement un processus d'enregistrement ffmpeg lancé en arrière-plan.
        """
        if not process:
            print("=== [AUDIO] Aucun processus d'enregistrement à arrêter.")
            return

        print(f"=== [AUDIO] Envoi du signal d'arrêt (SIGTERM) au processus ffmpeg (PID: {process.pid})...")
        process.terminate() # Envoie le signal SIGTERM, ffmpeg va finaliser le fichier proprement.

        try:
            # On attend un peu pour laisser le temps à ffmpeg de fermer le fichier.
            # On récupère aussi les dernières sorties de log.
            stdout, stderr = process.communicate(timeout=15)
            print("=== [AUDIO] Processus ffmpeg terminé proprement.")
            
            # Afficher les logs de ffmpeg pour le débogage
            if stdout:
                print(f"--- FFMPEG STDOUT ---\n{stdout.decode('utf-8', errors='ignore')}")
            if stderr:
                print(f"--- FFMPEG STDERR ---\n{stderr.decode('utf-8', errors='ignore')}")

        except subprocess.TimeoutExpired:
            print(f"=== [AVERTISSEMENT] Le processus ffmpeg (PID: {process.pid}) n'a pas terminé à temps. Forçage de l'arrêt (kill).")
            process.kill()
            print("=== [AUDIO] Processus ffmpeg tué.")
