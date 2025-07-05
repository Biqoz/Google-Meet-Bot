FROM python:3.10-slim

# Installer PortAudio et les dépendances audio
RUN apt-get update && apt-get install -y \
    libportaudio2 \
    portaudio19-dev \
    libasound-dev \
    libsndfile1-dev \
    ffmpeg \
    wget \
    xvfb \
    pulseaudio \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DISPLAY=:99

CMD ["bash", "-c", "pulseaudio --start; Xvfb :99 -screen 0 1280x720x24 & python join_google_meet.py"]
