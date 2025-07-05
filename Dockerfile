# Utiliser une image Python de base
FROM python:3.10-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# 1. Installation des dépendances système et de Google Chrome
# On combine les commandes pour créer moins de "couches" dans l'image Docker, ce qui est plus efficace.
RUN apt-get update && \
    apt-get install -y wget gnupg xvfb pulseaudio --no-install-recommends && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable --no-install-recommends && \
    # Nettoyage
    rm -rf /var/lib/apt/lists/*

# 2. Installation de la version de Chromedriver correspondante à Chrome stable
# Cette méthode est plus robuste que de fixer une version manuelle
RUN CHROME_VERSION=$(google-chrome-stable --version | awk '{print $3}' | cut -d'.' -f1-3) && \
    echo "=== [DEBUG] Version de Chrome détectée : $CHROME_VERSION ===" && \
    wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip && rm -rf /usr/local/bin/chromedriver-linux64


# 3. Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# 4. Copie du code de l'application
COPY . .


# 5. Création du dossier pour les enregistrements (pour la persistance avec Coolify)
RUN mkdir -p /app/recordings


# 6. Commande de démarrage
# On utilise un script de démarrage pour lancer PulseAudio puis le script Python.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
