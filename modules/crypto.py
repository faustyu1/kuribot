from core.config import config
# meta developer: @faustyu
# meta description: Модуль криптовалют и валют с графиками

import aiohttp
import io
from pyrogram import filters, Client
from pyrogram.types import Message

@Client.on_message(filters.command(["crypto", "p", "price"], prefixes=config.get("prefix", ".")) & filters.me)
async def crypto_handler(client: Client, message: Message):
    """Показать цену криптовалюты и график"""
    if len(message.command) < 2:
        return await message.edit("<b>⚠️ Введите тикер монеты (например, .p btc)</b>")

    symbol = message.command[1].upper()
    await message.edit(f"<b>🔍 Ищу данные для {symbol}...</b>")

    # Используем CryptoCompare для данных и графиков
    # Они предоставляют отличные статические графики без API ключей для простых запросов
    api_url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={symbol}&tsyms=USD,RUB"
    chart_url = f"https://images.cryptocompare.com/sparkline/{symbol}/usd/day.png"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                data = await resp.json()
                
                if data.get("Response") == "Error" or symbol not in data.get("RAW", {}):
                    return await message.edit(f"<b>❌ Монета <code>{symbol}</code> не найдена.</b>")

                raw = data["RAW"][symbol]["USD"]
                display = data["DISPLAY"][symbol]["USD"]

                price = display["PRICE"]
                change_24h = display["CHANGEPCT24HOUR"]
                high = display["HIGHDAY"]
                low = display["LOWDAY"]
                mcap = display["MKTCAP"]
                
                price_rub = data["DISPLAY"][symbol]["RUB"]["PRICE"]

                # Определяем эмодзи тренда
                trend = "📈" if float(raw["CHANGEPCT24HOUR"]) >= 0 else "📉"
                color = "🟢" if float(raw["CHANGEPCT24HOUR"]) >= 0 else "🔴"

                caption = (
                    f"<b>{trend} {symbol} / USD</b>\n\n"
                    f"💰 <b>Цена:</b> <code>{price}</code>\n"
                    f"🇷🇺 <b>В рублях:</b> <code>{price_rub}</code>\n"
                    f"📊 <b>Изменение:</b> {color} <code>{change_24h}%</code>\n\n"
                    f"⬆️ <b>Макс (24ч):</b> <code>{high}</code>\n"
                    f"⬇️ <b>Мин (24ч):</b> <code>{low}</code>\n"
                    f"💎 <b>Капитализация:</b> <code>{mcap}</code>\n"
                )

                # Пытаемся отправить с графиком
                try:
                    await client.send_photo(
                        chat_id=message.chat.id,
                        photo=chart_url,
                        caption=caption
                    )
                    await message.delete()
                except:
                    # Если фото не отправилось, шлем текстом
                    await message.edit(caption)

    except Exception as e:
        await message.edit(f"<b>❌ Ошибка:</b> <code>{str(e)}</code>")

@Client.on_message(filters.command(["curr", "val"], prefixes=config.get("prefix", ".")) & filters.me)
async def currency_handler(client: Client, message: Message):
    """Показать курс валют (USD, EUR)"""
    await message.edit("<b>💵 Получаю курсы валют...</b>")
    
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                
                usd = data["Valute"]["USD"]
                eur = data["Valute"]["EUR"]
                cny = data["Valute"]["CNY"]

                def get_trend(v):
                    return "🔼" if v["Value"] > v["Previous"] else "🔽"

                text = (
                    f"<b>🏦 Курсы ЦБ РФ</b>\n\n"
                    f"🇺🇸 <b>USD:</b> <code>{usd['Value']:.2f}₽</code> {get_trend(usd)}\n"
                    f"🇪🇺 <b>EUR:</b> <code>{eur['Value']:.2f}₽</code> {get_trend(eur)}\n"
                    f"🇨🇳 <b>CNY:</b> <code>{cny['Value']:.2f}₽</code> {get_trend(cny)}\n"
                )
                await message.edit(text)
    except Exception as e:
        await message.edit(f"<b>❌ Ошибка:</b> <code>{str(e)}</code>")