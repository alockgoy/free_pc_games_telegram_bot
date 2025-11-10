# 🎮 Bot de Telegram - Juegos Gratis

Bot de Telegram que monitorea **Steam** y **Epic Games Store** buscando juegos de pago con descuento del 100% (ofertas temporales gratuitas) y envía notificaciones automáticas.

## 📋 Características

- ✅ Monitoreo automático de Steam y Epic Games
- ✅ Detecta juegos de pago temporalmente gratis (no free-to-play)
- ✅ Notificaciones por Telegram
- ✅ Evita notificaciones duplicadas durante la promoción
- ✅ **Limpieza automática: elimina juegos después de 7 días**
- ✅ Permite re-notificar si un juego vuelve a estar gratis en el futuro
- ✅ Registro persistente con timestamps
- ✅ Verificación configurable (por defecto cada hora)

---

## 🚀 Instalación y Configuración

### 1️⃣ Crear el Bot de Telegram

1. Abre Telegram y busca [@BotFather](https://t.me/BotFather)
2. Envía el comando `/newbot`
3. Sigue las instrucciones (elige un nombre y username)
4. **Guarda el token** que te proporciona (ejemplo: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2️⃣ Obtener tu Chat ID

**Opción A - Para uso personal:**
1. Busca [@userinfobot](https://t.me/userinfobot) en Telegram
2. Envíale cualquier mensaje
3. Te responderá con tu **Chat ID** (ejemplo: `123456789`)

**Opción B - Para grupos:**
1. Añade tu bot al grupo
2. Envía un mensaje cualquiera en el grupo
3. Visita: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
   - Reemplaza `<TU_TOKEN>` con el token de tu bot
4. Busca `"chat":{"id":` en la respuesta JSON
5. El número que aparece ahí es tu **Chat ID del grupo** (ejemplo: `-987654321`)
   - **Nota:** Los IDs de grupos son negativos

### 3️⃣ Configurar el Bot

Edita el archivo `free_games_bot.py` y modifica estas líneas:

```python
TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"  # Tu token aquí
TELEGRAM_CHAT_ID = "123456789"  # Tu Chat ID aquí (o ID del grupo)
```

**Opcional - Cambiar intervalo de verificación:**
```python
CHECK_INTERVAL = 3600  # Segundos (3600 = 1 hora)
```

### 4️⃣ Permisos para Grupos

Si vas a usar el bot en un grupo:
1. Añade el bot como administrador del grupo
2. Asegúrate de que el bot tenga permiso para enviar mensajes
3. Usa el **Chat ID negativo** del grupo en la configuración

---

## 💻 Despliegue en Windows

### Instalación

1. **Instala Python 3.8 o superior** desde [python.org](https://www.python.org/downloads/)
   - ✅ Durante la instalación, marca "Add Python to PATH"

2. **Instala las dependencias:**
   ```cmd
   pip install python-telegram-bot requests
   ```

3. **Ejecuta el bot:**
   ```cmd
   python free_games_bot.py
   ```

### Ejecutar en segundo plano

**Opción A - Crear un archivo .bat:**

Crea un archivo `ejecutar_bot.bat`:
```batch
@echo off
cd /d "%~dp0"
python free_games_bot.py
pause
```

**Opción B - Ejecutar al inicio (Task Scheduler):**

1. Abre "Programador de tareas" (Task Scheduler)
2. Crear tarea básica
3. Nombre: "Bot Juegos Gratis"
4. Desencadenador: "Al iniciar"
5. Acción: "Iniciar un programa"
6. Programa: `python`
7. Argumentos: `C:\ruta\completa\free_games_bot.py`
8. Directorio: `C:\ruta\completa\`

---

## 🐧 Despliegue en Linux

### Ubuntu/Debian

```bash
# Instalar Python y pip
sudo apt update
sudo apt install python3 python3-pip -y

# Instalar dependencias
pip3 install python-telegram-bot requests

# Ejecutar el bot
python3 free_games_bot.py
```

### Ejecutar en segundo plano con systemd

1. **Crea un servicio:**
   ```bash
   sudo nano /etc/systemd/system/free-games-bot.service
   ```

2. **Añade este contenido:**
   ```ini
   [Unit]
   Description=Bot de Telegram - Juegos Gratis
   After=network.target

   [Service]
   Type=simple
   User=tu_usuario
   WorkingDirectory=/ruta/completa/al/bot
   ExecStart=/usr/bin/python3 /ruta/completa/al/bot/free_games_bot.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Activa y arranca el servicio:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable free-games-bot.service
   sudo systemctl start free-games-bot.service
   ```

4. **Comandos útiles:**
   ```bash
   # Ver estado
   sudo systemctl status free-games-bot.service
   
   # Ver logs
   sudo journalctl -u free-games-bot.service -f
   
   # Reiniciar
   sudo systemctl restart free-games-bot.service
   
   # Detener
   sudo systemctl stop free-games-bot.service
   ```

---

## 🐳 Despliegue con Docker (Recomendado)

### Crear Dockerfile

Crea un archivo `Dockerfile` en la misma carpeta que el bot:

```dockerfile
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
```

### Crear docker-compose.yml

```yaml
version: '3.8'

services:
  free-games-bot:
    build: .
    container_name: free-games-bot
    restart: unless-stopped
    environment:
      - TZ=Europe/Madrid
    volumes:
      - ./data:/app/data
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
```

### Construir y ejecutar

```bash
# Construir imagen
docker build -t free-games-bot .

# Ejecutar con docker-compose
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down

# Reiniciar
docker-compose restart
```

### Comandos Docker directos

```bash
# Construir
docker build -t free-games-bot .

# Ejecutar
docker run -d \
  --name free-games-bot \
  --restart unless-stopped \
  -v $(pwd)/data:/app/data \
  free-games-bot

# Ver logs
docker logs -f free-games-bot

# Detener
docker stop free-games-bot

# Eliminar contenedor
docker rm free-games-bot
```

---

## 🗄️ Despliegue en Synology NAS

### Opción 1: Docker (Recomendado)

1. **Instala Docker en Synology:**
   - Abre "Package Center"
   - Busca e instala "Container Manager" (antes "Docker")

2. **Sube los archivos al NAS:**
   - Usa File Station para crear una carpeta: `/docker/free-games-bot`
   - Sube `free_games_bot.py`, `Dockerfile` y `docker-compose.yml`

3. **Construye la imagen:**
   - Abre "Container Manager"
   - Ve a "Proyecto" > "Crear"
   - Selecciona la ruta `/docker/free-games-bot`
   - Configuración del proyecto: usa `docker-compose.yml`
   - Haz clic en "Crear"

4. **Gestiona el contenedor:**
   - En "Contenedor" verás `free-games-bot`
   - Botones: Iniciar, Detener, Reiniciar
   - Ver logs: Doble clic > Registro

### Opción 2: Python Task (sin Docker)

1. **Instala Python3 en Synology:**
   - Package Center > Python 3

2. **Conéctate por SSH:**
   ```bash
   ssh admin@tu-nas.local
   ```

3. **Instala dependencias:**
   ```bash
   sudo python3 -m pip install python-telegram-bot requests
   ```

4. **Sube el script:**
   - Coloca `free_games_bot.py` en `/volume1/scripts/`

5. **Crea una tarea programada:**
   - Panel de control > Programador de tareas
   - Crear > Tarea programada > Script definido por usuario
   - Nombre: "Bot Juegos Gratis"
   - Usuario: root
   - Programa: Al iniciar
   - Script:
     ```bash
     python3 /volume1/scripts/free_games_bot.py
     ```

---

## 📁 Estructura de Archivos

```
free-games-bot/
├── free_games_bot.py       # Script principal
├── notified_games.json     # Base de datos de juegos notificados (auto-generado)
├── Dockerfile              # Para despliegue con Docker
├── docker-compose.yml      # Configuración Docker Compose
└── README.md               # Este archivo
```

---

## 🔧 Solución de Problemas

### El bot no envía mensajes

1. **Verifica el token:** Debe ser correcto y sin espacios
2. **Verifica el Chat ID:** Debe ser correcto
3. **Envía un mensaje al bot primero:** El bot no puede enviarte mensajes hasta que tú le escribas primero
4. **Para grupos:** Asegúrate de usar el Chat ID negativo del grupo

### Error "Module not found"

```bash
# Instala las dependencias
pip install python-telegram-bot requests
```

### El bot se cierra inesperadamente

- **En Docker:** Los logs se guardan, revísalos con `docker logs`
- **En systemd:** Revisa con `journalctl -u free-games-bot.service`
- El bot se reiniciará automáticamente si configuraste `restart: unless-stopped` (Docker) o `Restart=always` (systemd)

### No detecta juegos gratis de Steam

- La API de Steam tiene delays, puede tardar horas en actualizar
- Algunas promociones regionales no aparecen en las APIs públicas
- El bot verifica cada hora (configurable)

### Consumo de recursos

- **RAM:** ~50-100 MB
- **CPU:** Mínimo (solo al verificar cada hora)
- **Red:** ~1-5 MB/hora

---

## 🛠️ Personalización

### Cambiar intervalo de verificación

```python
CHECK_INTERVAL = 1800  # 30 minutos
CHECK_INTERVAL = 7200  # 2 horas
```

### Modificar mensaje de notificación

Edita la función `send_telegram_message()`:

```python
message = (
    f"🎮 <b>¡NUEVO JUEGO GRATIS!</b> 🎮\n\n"
    f"📌 <b>{game_info['title']}</b>\n"
    f"🏪 {game_info['platform']}\n"
    f"🔗 {game_info['url']}\n\n"
    f"⏰ ¡Consíguelo antes de que termine!"
)
```

### Filtrar por plataforma

Si solo quieres notificaciones de Epic Games, comenta las líneas de Steam:

```python
# Verificar Steam
# print("🔍 Verificando Steam...")
# steam_games = check_steam_via_steamdb()
```

---

## 📝 Notas Importantes

- ⚠️ **Rate Limits:** Steam limita peticiones. El bot hace pausas automáticas
- 🔄 **Actualizaciones:** La API de Steam puede tener delays de hasta 24h
- 💾 **Persistencia:** `notified_games.json` guarda los juegos ya notificados. Puedes borrarlo para reiniciar
- 🐳 **Docker:** Recomendado para facilitar migraciones entre dispositivos
- 📊 **Logs:** El bot muestra información detallada en consola

---

## 📜 Licencia

Este proyecto es de código abierto. Siéntete libre de modificarlo y compartirlo.

---

## 🤝 Contribuciones

¿Mejoras o sugerencias? ¡Son bienvenidas!

---

## 📧 Soporte

Si tienes problemas:
1. Revisa la sección "Solución de Problemas"
2. Verifica los logs del bot
3. Asegúrate de tener las últimas versiones de las dependencias

---

**¡Disfruta de tus juegos gratis!** 🎮🎉
