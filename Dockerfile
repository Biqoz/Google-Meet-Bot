FROM python:3.10-slim

# Dépendances système
RUN echo "=== [DEBUG] Installation des paquets système ===" && \
    apt-get update && apt-get install -y \
    wget unzip xvfb xauth gnupg libxi6 libgconf-2-4 libnss3 libxss1 \
    libasound2 libatk-bridge2.0-0 libgtk-3-0 fonts-liberation \
    libgbm1 libu2f-udev libvulkan1 pulseaudio portaudio19-dev \
    libportaudio2 libportaudiocpp0 ffmpeg --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Installer Google Chrome stable
RUN echo "=== [DEBUG] Installation de Google Chrome ===" && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Installer Chromedriver 138.0.7204.92 (Chrome for Testing)
RUN echo "=== [DEBUG] Installation de Chromedriver 138.0.7204.92 ===" && \
    rm -f /usr/local/bin/chromedriver && \
    wget -O /tmp/chromedriver-linux64.zip "https://storage.googleapis.com/chrome-for-testing-public/138.0.7204.92/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver-linux64*

WORKDIR /app

# Dépendances Python
COPY requirements.txt .
RUN echo "=== [DEBUG] Installation des dépendances Python ===" && \
    pip install --no-cache-dir -r requirements.txt

# Code de l'app
COPY . .

# Ajout d'un print de debug dans le script Python (si pas déjà présent)
RUN sed -i '1i\print("=== [DEBUG] Script Python lancé ===")' join_google_meet.py

# Commande de démarrage avec logs et temporisation pour debug
CMD echo "=== [DEBUG] Lancement PulseAudio et Xvfb ===" && \
    pulseaudio --start && \
    echo "=== [DEBUG] PulseAudio lancé ===" && \
    xvfb-run -a python join_google_meet.py && \
    echo "=== [DEBUG] Script Python terminé ===" && \
    sleep 120
