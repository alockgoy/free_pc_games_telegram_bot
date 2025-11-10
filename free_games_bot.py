# Ejecutar este comando previamente en el S.O: pip install python-telegram-bot --upgrade

import os
import time
import requests
from datetime import datetime
import json
import asyncio
import signal
import sys
import re
from telegram import Bot
from telegram.error import TelegramError

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
TELEGRAM_BOT_TOKEN = "Token"  # Obtener de @BotFather
TELEGRAM_CHAT_ID = "ID"  # Tu ID de chat o ID del canal

# Archivo para guardar juegos ya notificados (en el directorio del script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NOTIFIED_GAMES_FILE = os.path.join(SCRIPT_DIR, "notified_games.json")

# Intervalo de verificación (en segundos)
CHECK_INTERVAL = 3600  # 1 hora

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def load_notified_games():
    """Carga los juegos ya notificados desde archivo"""
    if os.path.exists(NOTIFIED_GAMES_FILE):
        with open(NOTIFIED_GAMES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"steam": {}, "epic": {}}

def save_notified_games(games_dict):
    """Guarda los juegos notificados en archivo"""
    with open(NOTIFIED_GAMES_FILE, 'w', encoding='utf-8') as f:
        json.dump(games_dict, f, ensure_ascii=False, indent=2)

def clean_old_games(games_dict, days=7):
    """Elimina juegos notificados hace más de X días"""
    current_time = time.time()
    max_age = days * 24 * 60 * 60  # Convertir días a segundos
    
    cleaned = {"steam": {}, "epic": {}}
    removed_count = {"steam": 0, "epic": 0}
    
    for platform in ["steam", "epic"]:
        for game_id, notified_at in games_dict.get(platform, {}).items():
            age = current_time - notified_at
            if age < max_age:
                cleaned[platform][game_id] = notified_at
            else:
                removed_count[platform] += 1
    
    total_removed = removed_count["steam"] + removed_count["epic"]
    if total_removed > 0:
        print(f"🧹 Limpieza: {removed_count['steam']} juegos de Steam y {removed_count['epic']} de Epic eliminados (más de {days} días)")
    
    return cleaned

# =============================================================================
# STEAM
# =============================================================================

def check_steam_via_steamdb():
    """
    Busca juegos con 100% de descuento en Steam usando múltiples métodos
    """
    free_games = []
    found_ids = set()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"   🔍 Método 1: Featured API")
        # Método 1: Steam Featured
        url = "https://store.steampowered.com/api/featured/"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            for category in ['large_capsules', 'featured_win', 'featured_mac', 'featured_linux']:
                if category in data:
                    print(f"      - Categoría {category}: {len(data[category])} juegos")
                    for game in data[category]:
                        discount = game.get('discount_percent', 0)
                        if discount > 0:
                            print(f"        · {game.get('name')}: {discount}% descuento")
                        
                        if discount == 100:
                            app_id = game.get('id')
                            if app_id and str(app_id) not in found_ids:
                                is_f2p = is_game_free_to_play(app_id)
                                print(f"        ✓ 100% descuento! F2P: {is_f2p}")
                                
                                if not is_f2p:
                                    found_ids.add(str(app_id))
                                    free_games.append({
                                        'title': game.get('name', 'Desconocido'),
                                        'url': f"https://store.steampowered.com/app/{app_id}",
                                        'id': str(app_id),
                                        'platform': 'Steam'
                                    })
        else:
            print(f"      ❌ Error HTTP {response.status_code}")
        
        print(f"   🔍 Método 2: Búsqueda de especiales (HTML)")
        # Método 2: Búsqueda directa parseando HTML
        search_url = "https://store.steampowered.com/search/results/"
        params = {
            'query': '',
            'start': 0,
            'count': 50,
            'maxprice': 'free',
            'specials': 1,
            'ndl': 1
        }
        
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            app_ids = re.findall(r'data-ds-appid="(\d+)"', html)
            
            print(f"      - App IDs encontrados: {len(app_ids)}")
            
            if app_ids:
                for app_id in app_ids[:10]:
                    if str(app_id) not in found_ids:
                        details = get_game_details(app_id)
                        if details:
                            name = details.get('name', 'Desconocido')
                            original_price = details.get('original_price', 0)
                            final_price = details.get('final_price', 0)
                            is_f2p = details.get('is_free', False)
                            
                            print(f"        · {name}: Final={final_price}, Original={original_price}, F2P={is_f2p}")
                            
                            # Si aparece en búsqueda "maxprice=free" con precio original > 0
                            # O si final_price = 0 y original_price > 0
                            # Entonces es una promoción temporal gratuita
                            if original_price > 0:
                                # Tiene precio original, así que no es F2P permanente
                                found_ids.add(str(app_id))
                                free_games.append({
                                    'title': name,
                                    'url': f"https://store.steampowered.com/app/{app_id}",
                                    'id': str(app_id),
                                    'platform': 'Steam'
                                })
                                print(f"          ✅ GRATIS TEMPORAL (aparece en búsqueda de gratis)!")
                        else:
                            print(f"        · ID {app_id}: Sin detalles")
            else:
                print(f"      ℹ️ No se encontraron IDs en HTML")
        else:
            print(f"      ❌ Error HTTP {response.status_code}")
        
        print(f"   🔍 Método 3: Featured Categories")
        search_url = "https://store.steampowered.com/api/featuredcategories/"
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            categories = ['specials', 'coming_soon', 'top_sellers', 'new_releases']
            for category in categories:
                if category in data:
                    items = data[category].get('items', []) if isinstance(data[category], dict) else data[category]
                    if items:
                        print(f"      - Categoría {category}: {len(items)} juegos")
                        for game in items:
                            discount = game.get('discount_percent', 0)
                            if discount == 100:
                                app_id = game.get('id')
                                if app_id and str(app_id) not in found_ids:
                                    is_f2p = is_game_free_to_play(app_id)
                                    print(f"        ✓ {game.get('name')}: 100% descuento! F2P: {is_f2p}")
                                    
                                    if not is_f2p:
                                        found_ids.add(str(app_id))
                                        free_games.append({
                                            'title': game.get('name', 'Desconocido'),
                                            'url': f"https://store.steampowered.com/app/{app_id}",
                                            'id': str(app_id),
                                            'platform': 'Steam'
                                        })
        else:
            print(f"      ❌ Error HTTP {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error al verificar Steam: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"   📊 Total juegos gratis encontrados en Steam: {len(free_games)}")
    return free_games

def is_game_free_to_play(app_id):
    """Verifica si un juego es Free-to-Play en Steam"""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if str(app_id) in data and data[str(app_id)]['success']:
                game_data = data[str(app_id)]['data']
                return game_data.get('is_free', False)
    except:
        pass
    
    return False

def get_game_details(app_id):
    """Obtiene detalles completos de un juego de Steam incluyendo precio"""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=es&l=spanish"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if str(app_id) in data and data[str(app_id)]['success']:
                game_data = data[str(app_id)]['data']
                
                # Obtener información de precio
                price_overview = game_data.get('price_overview', {})
                
                return {
                    'name': game_data.get('name', 'Desconocido'),
                    'is_free': game_data.get('is_free', False),
                    'final_price': price_overview.get('final', 0),
                    'original_price': price_overview.get('initial', 0),
                    'discount_percent': price_overview.get('discount_percent', 0)
                }
    except:
        pass
    
    return None

# =============================================================================
# EPIC GAMES
# =============================================================================

def check_epic_free_games():
    """
    Busca juegos gratuitos en Epic Games Store
    """
    free_games = []
    
    try:
        url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        params = {
            'locale': 'es-ES',
            'country': 'ES',
            'allowCountries': 'ES'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and 'Catalog' in data['data']:
                games = data['data']['Catalog']['searchStore']['elements']
                print(f"   📊 Epic: {len(games)} juegos encontrados en total")
                
                for game in games:
                    # Verificar si está gratis actualmente
                    promotions = game.get('promotions')
                    if promotions:
                        promo_offers = promotions.get('promotionalOffers')
                        
                        if promo_offers and len(promo_offers) > 0:
                            offers = promo_offers[0].get('promotionalOffers', [])
                            
                            if len(offers) > 0:
                                # Verificar precio
                                price_info = game.get('price', {}).get('totalPrice', {})
                                original_price = price_info.get('originalPrice', 0)
                                current_price = price_info.get('discountPrice', 0)
                                
                                title = game.get('title', 'Desconocido')
                                print(f"   🔍 {title}: Original={original_price}, Actual={current_price}")
                                
                                # Gratis temporalmente (precio original > 0, actual = 0)
                                if original_price > 0 and current_price == 0:
                                    game_id = game.get('id')
                                    
                                    free_games.append({
                                        'title': title,
                                        'url': f"https://store.epicgames.com/es-ES/free-games",
                                        'id': game_id,
                                        'platform': 'Epic Games'
                                    })
                                    print(f"   ✅ Juego gratis detectado: {title}")
    
    except Exception as e:
        print(f"   ❌ Error al verificar Epic Games: {e}")
        import traceback
        traceback.print_exc()
    
    return free_games

# =============================================================================
# TELEGRAM
# =============================================================================

async def test_telegram_connection(bot):
    """Prueba la conexión con Telegram y envía un mensaje de prueba"""
    try:
        print("\n🔧 Probando conexión con Telegram...")
        
        # Obtener info del bot
        bot_info = await bot.get_me()
        print(f"✓ Bot conectado: @{bot_info.username}")
        
        # Intentar enviar mensaje de prueba
        test_message = "🤖 Bot de juegos gratis iniciado correctamente.\n\n✅ Las notificaciones llegarán aquí."
        
        result = await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=test_message,
            parse_mode='HTML'
        )
        
        print(f"✓ Mensaje de prueba enviado correctamente (ID: {result.message_id})")
        print(f"✓ Chat ID verificado: {TELEGRAM_CHAT_ID}")
        return True
        
    except TelegramError as e:
        print(f"❌ Error de Telegram: {e}")
        
        if "Unauthorized" in str(e):
            print("   → El token del bot es inválido. Verifica con @BotFather")
        elif "chat not found" in str(e) or "Bad Request" in str(e):
            print("   → El Chat ID es incorrecto o el bot no puede enviarte mensajes")
            print("   → SOLUCIÓN: Envía un mensaje a tu bot primero (cualquier mensaje)")
            print("   → O usa @userinfobot para verificar tu Chat ID")
        
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

async def send_telegram_message(bot, game_info):
    """Envía un mensaje de Telegram con la info del juego"""
    try:
        message = (
            f"🎮 <b>¡JUEGO GRATIS!</b> 🎮\n\n"
            f"<b>Título:</b> {game_info['title']}\n"
            f"<b>Plataforma:</b> {game_info['platform']}\n"
            f"<b>Enlace:</b> {game_info['url']}\n\n"
            f"⏰ <i>¡Aprovecha antes de que termine la oferta!</i>"
        )
        
        result = await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='HTML',
            disable_web_page_preview=False
        )
        
        print(f"✓ Notificación enviada: {game_info['title']} (Message ID: {result.message_id})")
        return True
        
    except TelegramError as e:
        print(f"❌ Error al enviar mensaje de Telegram: {e}")
        return False

# =============================================================================
# SEÑALES Y CIERRE LIMPIO
# =============================================================================

shutdown_flag = False

def signal_handler(sig, frame):
    """Manejador para cierre limpio del bot"""
    global shutdown_flag
    print("\n\n⚠️  Bot detenido por el usuario")
    print("🔄 Cerrando conexiones...")
    shutdown_flag = True
    sys.exit(0)

# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Función principal del bot"""
    
    # Configurar manejador de señales para cierre limpio
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Validar configuración
    if TELEGRAM_BOT_TOKEN == "TU_TOKEN_DE_BOT":
        print("❌ ERROR: Configura tu TELEGRAM_BOT_TOKEN")
        return
    
    if TELEGRAM_CHAT_ID == "TU_CHAT_ID":
        print("❌ ERROR: Configura tu TELEGRAM_CHAT_ID")
        return
    
    print("=" * 60)
    print("🤖 BOT DE JUEGOS GRATIS - Iniciando...")
    print("=" * 60)
    
    # Inicializar bot
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
    except Exception as e:
        print(f"❌ Error al crear el bot: {e}")
        return
    
    # Probar conexión con Telegram
    if not await test_telegram_connection(bot):
        print("\n⚠️  No se pudo establecer conexión con Telegram.")
        print("⚠️  Verifica tu configuración y vuelve a intentar.\n")
        return
    
    print(f"\n⏱️  Intervalo de verificación: {CHECK_INTERVAL} segundos")
    print(f"📁 Archivo de registro: {NOTIFIED_GAMES_FILE}\n")
    
    # Cargar juegos ya notificados
    notified_games = load_notified_games()
    
    # Limpiar juegos antiguos (más de 7 días)
    notified_games = clean_old_games(notified_games, days=7)
    save_notified_games(notified_games)
    
    print(f"📊 Juegos registrados: Steam={len(notified_games['steam'])}, Epic={len(notified_games['epic'])}\n")
    print("💡 Presiona Ctrl+C para detener el bot de forma segura\n")
    
    while not shutdown_flag:
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verificando ofertas...")
            
            # Verificar Steam
            print("🔍 Verificando Steam...")
            steam_games = check_steam_via_steamdb()
            
            new_steam = 0
            for game in steam_games:
                if game['id'] not in notified_games['steam']:
                    if await send_telegram_message(bot, game):
                        notified_games['steam'][game['id']] = time.time()
                        save_notified_games(notified_games)
                        new_steam += 1
            
            if new_steam > 0:
                print(f"   ✓ {new_steam} nuevo(s) juego(s) de Steam notificado(s)")
            
            # Verificar Epic Games
            print("🔍 Verificando Epic Games...")
            epic_games = check_epic_free_games()
            
            new_epic = 0
            for game in epic_games:
                if game['id'] not in notified_games['epic']:
                    if await send_telegram_message(bot, game):
                        notified_games['epic'][game['id']] = time.time()
                        save_notified_games(notified_games)
                        new_epic += 1
            
            if new_epic > 0:
                print(f"   ✓ {new_epic} nuevo(s) juego(s) de Epic Games notificado(s)")
            
            if not steam_games and not epic_games:
                print("   ℹ️  No se encontraron nuevas ofertas")
            
            # Limpiar juegos antiguos después de cada verificación
            notified_games = clean_old_games(notified_games, days=7)
            save_notified_games(notified_games)
            
            # Esperar hasta la próxima verificación
            print(f"⏳ Próxima verificación en {CHECK_INTERVAL} segundos...\n")
            
            # Usar sleep con verificación de shutdown
            try:
                for i in range(CHECK_INTERVAL):
                    if shutdown_flag:
                        break
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                print("\n⚠️  Operación cancelada, cerrando...")
                break
            
        except KeyboardInterrupt:
            print("\n⚠️  Bot detenido por el usuario")
            break
        except asyncio.CancelledError:
            print("\n⚠️  Bot detenido")
            break
        except Exception as e:
            print(f"❌ Error en el bucle principal: {e}")
            try:
                await asyncio.sleep(60)
            except (asyncio.CancelledError, KeyboardInterrupt):
                print("\n⚠️  Bot detenido durante recuperación de error")
                break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Bot detenido correctamente")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")