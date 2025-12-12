FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos
COPY free_games_bot.py .

# Instalar dependencias de Python
RUN pip install --no-cache-dir python-telegram-bot requests

# Crear volumen para persistencia
VOLUME /app/data

# Ejecutar bot
CMD ["python", "-u", "free_games_bot.py"]