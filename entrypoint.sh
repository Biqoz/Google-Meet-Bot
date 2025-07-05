#!/bin/sh

echo "=== [ENTRYPOINT] Lancement de PulseAudio... ==="
pulseaudio --start --log-target=stderr

sleep 2 # Petite pause pour s'assurer que PulseAudio est démarré

echo "=== [ENTRYPOINT] Lancement du script Python via xvfb-run avec l'option -u ==="
# L'option -u est la clé pour avoir les logs en temps réel !
xvfb-run -a python -u join_google_meet.py

echo "=== [ENTRYPOINT] Le script Python est terminé. ==="
