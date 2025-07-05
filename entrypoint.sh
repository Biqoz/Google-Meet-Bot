#!/bin/sh

# Lancer PulseAudio en arrière-plan
echo "=== [ENTRYPOINT] Lancement de PulseAudio... ==="
pulseaudio --start --log-target=stderr

# Attendre un court instant que PulseAudio soit prêt
sleep 2

# Lancer le script Python avec Xvfb
# L'option -u est la clé pour avoir les logs en temps réel !
echo "=== [ENTRYPOINT] Lancement du script Python via xvfb-run... ==="
xvfb-run -a python -u join_google_meet.py

echo "=== [ENTRYPOINT] Le script Python est terminé. ==="
