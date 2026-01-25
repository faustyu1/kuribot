# meta developer: @faustyu
# meta description: Модуль погоды (через wttr.in)

import aiohttp
from pyrogram import filters, Client
from pyrogram.types import Message
from core.config import config

STRINGS = {
    "usage": "<b>🌍 Использование:</b> <code>.weather [город]</code>\n<i>Установить город по умолчанию:</i> <code>.setcity [город]</code>",
    "wait": "<b>⏳ Получаю данные о погоде...</b>",
    "error_city": "<b>❌ Город не найден или сервис недоступен.</b>",
    "error_api": "<b>❌ Ошибка при запросе к wttr.in</b>",
    "city_set": "<b>✅ Город по умолчанию установлен:</b> <code>{}</code>"
}

@Client.on_message(filters.command("weather", prefixes=config.get("prefix", ".")) & filters.me)
async def weather_handler(client: Client, message: Message):
    """Показать погоду в указанном городе или городе по умолчанию"""
    city = None
    if len(message.command) > 1:
        city = " ".join(message.command[1:])
    else:
        city = config.get("default_city")

    if not city:
        return await message.edit(STRINGS["usage"])

    await message.edit(STRINGS["wait"])

    # headers for Met.no and Open-Meteo
    headers = {"User-Agent": "KuriBot/1.4 (https://github.com/faustyu1/kuribot)"}
    
    try:
        # Step 1: Geocoding via Open-Meteo Geocoding API (Faster and more reliable than Nominatim)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=ru&format=json"
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(geo_url) as resp:
                geo_data = await resp.json()
                if not geo_data.get("results"):
                    return await message.edit(STRINGS["error_city"])
                
                res = geo_data["results"][0]
                lat, lon = res["latitude"], res["longitude"]
                city_name = res.get("name", city)
                country = res.get("country", "")
                region = res.get("admin1", "")

        # Step 2: Try Open-Meteo (Primary)
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,surface_pressure"
            f"&daily=sunrise,sunset,uv_index_max&timezone=auto"
        )
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(weather_url) as resp:
                    data = await resp.json()
                    cur = data['current']
                    daily = data['daily']
                    
                    # WMO Codes
                    WMO_CODES = {
                        0: "☀️ Ясно", 1: "🌤 Преимущественно ясно", 2: "⛅️ Переменная облачность", 3: "☁️ Пасмурно",
                        45: "🌫 Туман", 48: "🌫 Изморозь", 51: "🌦 Легкая морось", 53: "🌦 Умеренная морось",
                        55: "🌦 Плотная морось", 61: "🌧 Небольшой дождь", 63: "🌧 Умеренный дождь", 65: "🌧 Сильный дождь",
                        71: "🌨 Небольшой снег", 73: "🌨 Умеренный снег", 75: "🌨 Сильный снег", 80: "🌦 Ливневые дожди",
                        95: "⛈ Гроза"
                    }
                    
                    text = (
                        f"📍 <i>{region}, {country}</i>\n"
                        f"<b>{WMO_CODES.get(cur['weather_code'], '🛰 Спутник')}</b>\n\n"
                        f"🌡 <b>Температура:</b> <code>{cur['temperature_2m']}°C</code>\n"
                        f"🤔 <b>Ощущается:</b> <code>{cur['apparent_temperature']}°C</code>\n\n"
                        f"📊 <b>Детали:</b>\n"
                        f"💧 <b>Влажность:</b> <code>{cur['relative_humidity_2m']}%</code>\n"
                        f"💨 <b>Ветер:</b> <code>{cur['wind_speed_10m']} км/ч</code>\n"
                        f"<b>Давление:</b> <code>{cur['surface_pressure']} hPa</code>\n"
                        f"<b>УФ-индекс:</b> <code>{daily['uv_index_max'][0]}</code>\n\n"
                        f"🌅 <b>Восход:</b> <code>{daily['sunrise'][0].split('T')[1]}</code>\n"
                        f"🌇 <b>Закат:</b> <code>{daily['sunset'][0].split('T')[1]}</code>\n\n"
                    )
                    return await message.edit(text)
        except Exception:
            # Step 3: Fallback to Met.no (Norwegian Meteorological Institute) - Highly authoritative
            met_url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(met_url) as resp:
                    data = await resp.json()
                    cur = data['properties']['timeseries'][0]['data']['instant']['details']
                    
                    text = (
                        f"<b>🌍 Погода: {city_name}</b>\n"
                        f"📍 <i>{region}, {country}</i>\n\n"
                        f"🌡 <b>Температура:</b> <code>{cur['air_temperature']}°C</code>\n"
                        f"💧 <b>Влажность:</b> <code>{cur['relative_humidity']}%</code>\n"
                        f"💨 <b>Ветер:</b> <code>{cur['wind_speed']} м/с</code>\n"
                        f"<b>Давление:</b> <code>{cur['air_pressure_at_sea_level']} hPa</code>\n\n"
                    )
                    return await message.edit(text)

    except Exception as e:
        await message.edit(f"<b>❌ Ошибка при получении данных:</b>\n<code>{str(e)}</code>")

@Client.on_message(filters.command("setcity", prefixes=config.get("prefix", ".")) & filters.me)
async def setcity_handler(client: Client, message: Message):
    """Установить город по умолчанию"""
    if len(message.command) < 2:
        return await message.edit(STRINGS["usage"])
    
    city = " ".join(message.command[1:])
    config.set("default_city", city)
    await message.edit(STRINGS["city_set"].format(city))
