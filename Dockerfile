FROM python:3.10-slim

# 1. Dépendances système
RUN echo "=== [DEBUG] Installation des paquets système ===" && \
    apt-get update && apt-get install -y \
    wget unzip xvfb xauth gnupg libxi6 libgconf-2-4 libnss3 libxss1 \
    libasound2 libatk-bridge2.0-0 libgtk-3-0 fonts-liberation \
    libgbm1 libu2f-udev libvulkan1 pulseaudio portaudio19-dev \
    libportaudio2 libportaudiocpp0 ffmpeg --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 2. Chrome
RUN echo "=== [DEBUG] Installation de Google Chrome ===" && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# 3. Chromedriver
RUN echo "=== [DEBUG] Installation de Chromedriver ===" && \
    CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') && \
    CHROMEDRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}" || wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE") && \
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

WORKDIR /app

# 4. Dépendances Python
COPY requirements.txt .
RUN echo "=== [DEBUG] Installation des dépendances Python ===" && \
    pip install --no-cache-dir -r requirements.txt

# 5. Code de l'app
COPY . .

# 6. Ajout d'un print de debug dans le script Python (si pas déjà présent)
RUN sed -i '1i\print("=== [DEBUG] Script Python lancé ===")' join_google_meet.py

# 7. Commande de démarrage avec logs et temporisation pour debug
CMD echo "=== [DEBUG] Lancement PulseAudio et Xvfb ===" && \
    pulseaudio --start && \
    echo "=== [DEBUG] PulseAudio lancé ===" && \
    xvfb-run -a python join_google_meet.py && \
    echo "=== [DEBUG] Script Python terminé ===" && \
    sleep 120
