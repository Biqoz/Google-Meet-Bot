FROM python:3.10-slim

# 1. Dépendances système (INCHANGÉ - C'est votre liste, elle est correcte)
RUN echo "=== [DEBUG] Installation des paquets système ===" && \
    apt-get update && apt-get install -y \
    wget unzip xvfb xauth gnupg libxi6 libgconf-2-4 libnss3 libxss1 \
    libasound2 libatk-bridge2.0-0 libgtk-3-0 fonts-liberation \
    libgbm1 libu2f-udev libvulkan1 pulseaudio portaudio19-dev \
    libportaudio2 libportaudiocpp0 ffmpeg --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 2. Installer Google Chrome stable (INCHANGÉ)
RUN echo "=== [DEBUG] Installation de Google Chrome ===" && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# 3. Installer Chromedriver 138.0.7204.92 (INCHANGÉ - C'est la bonne version)
RUN echo "=== [DEBUG] Installation de Chromedriver 138.0.7204.92 ===" && \
    rm -f /usr/local/bin/chromedriver && \
    wget -O /tmp/chromedriver-linux64.zip "https://storage.googleapis.com/chrome-for-testing-public/138.0.7204.92/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver-linux64*

WORKDIR /app

# 4. Dépendances Python (INCHANGÉ)
COPY requirements.txt .
RUN echo "=== [DEBUG] Installation des dépendances Python ===" && \
    pip install --no-cache-dir -r requirements.txt

# 5. Code de l'app (INCHANGÉ)
COPY . .

# 6. Création du dossier pour les enregistrements (pour la persistance)
# Cette ligne est utile pour s'assurer que le dossier existe bien
RUN mkdir -p /app/recordings

# 7. LA SEULE VRAIE MODIFICATION : Utiliser un script de démarrage
# Cela nous permet de lancer Python avec l'option -u pour voir les logs.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
