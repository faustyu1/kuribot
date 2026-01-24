from pyrogram import filters, Client
from pyrogram.types import Message
import aiohttp
import json
import logging
import os
import importlib
import asyncio
from core.auth_manager import auth_manager

logger = logging.getLogger("kuribot.summarize")
API_URL = "https://api.onlysq.ru/ai/openai"

# Queue for summarization requests
summary_queue = asyncio.Queue()

# Rate limiting and status tracking
user_cooldowns = {} # {user_id: timestamp}
active_users = set() # {user_id} - users who have a request in queue or being processed

async def ai_request(prompt: str):
    api_key = os.getenv("AI_API_KEY", "")
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            async with session.post(f"{API_URL}/chat/completions", json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['choices'][0]['message']['content']
                else:
                    error_body = await resp.text()
                    logger.error(f"AI API Error {resp.status}: {error_body}")
                    return f"Error: {resp.status}"
        except Exception as e:
            logger.exception("AI Request failed")
            return f"Error: {str(e)}"

async def process_summary(client: Client, message: Message, limit: int, target_user, direction_down: bool, anchor_id: int, user_id: int):
    # Delete queue message if exists
    if hasattr(message, "_queue_msg"):
        try:
            await message._queue_msg.delete()
        except:
            pass

    try:
        # Function to update status (edit for self, reply for others)
        async def update_status(text):
            try:
                if message.from_user and message.from_user.is_self:
                    await message.edit(text)
                else:
                    if hasattr(message, "_resp") and message._resp:
                        await message._resp.edit(text)
                    else:
                        message._resp = await message.reply(text)
            except Exception as e:
                logger.warning(f"Failed to update status: {e}")

        dir_str = "вниз ⬇️" if direction_down else "вверх ⬆️"
        user_info_str = f"по <b>{target_user.first_name}</b>" if target_user else "всего чата"
        
        # Strict limit enforcement
        final_limit = min(limit, 2000)
        
        await update_status(f"<b>⌛ Собираю {final_limit} сообщений {user_info_str} {dir_str}...</b>")
        
        messages = []
        from pyrogram import raw
        
        try:
            peer = await client.resolve_peer(message.chat.id)
            from_id = None
            if target_user:
                from_id = await client.resolve_peer(target_user.id)
                
            offset_id = anchor_id
            users_map = {}
            
            while len(messages) < final_limit:
                current_batch_limit = min(final_limit - len(messages), 100)
                
                if direction_down:
                    if from_id:
                        res = await client.invoke(raw.functions.messages.GetHistory(
                            peer=peer, offset_id=offset_id, add_offset=-current_batch_limit,
                            limit=current_batch_limit, max_id=0, min_id=2**31 - 1, hash=0
                        ))
                    else:
                        res = await client.invoke(raw.functions.messages.GetHistory(
                            peer=peer, offset_id=offset_id, add_offset=-current_batch_limit,
                            limit=current_batch_limit, max_id=0, min_id=0, hash=0
                        ))
                else:
                    if from_id:
                        res = await client.invoke(raw.functions.messages.Search(
                            peer=peer, q="", from_id=from_id, filter=raw.types.InputMessagesFilterEmpty(),
                            min_date=0, max_date=0, offset_id=offset_id, add_offset=0,
                            limit=current_batch_limit, max_id=0, min_id=0, hash=0
                        ))
                    else:
                        res = await client.invoke(raw.functions.messages.GetHistory(
                            peer=peer, offset_id=offset_id, offset_date=0, add_offset=0,
                            limit=current_batch_limit, max_id=0, min_id=0, hash=0
                        ))

                if not getattr(res, "messages", None):
                    break
                
                users_map.update({u.id: u for u in res.users})
                
                batch = []
                for msg in res.messages:
                    if isinstance(msg, raw.types.Message) and msg.message:
                        if from_id:
                            msg_user_id = msg.from_id.user_id if isinstance(msg.from_id, raw.types.PeerUser) else 0
                            if msg_user_id != target_user.id: continue
                        name = users_map.get(msg.from_id.user_id).first_name if msg.from_id and isinstance(msg.from_id, raw.types.PeerUser) and users_map.get(msg.from_id.user_id) else "User"
                        batch.append(f"{name}: {msg.message}")
                
                if direction_down:
                    messages.extend(batch)
                    if not res.messages: break
                    offset_id = res.messages[0].id
                else:
                    messages.extend(batch)
                    if not res.messages: break
                    offset_id = res.messages[-1].id
                
                if len(res.messages) < current_batch_limit and not from_id:
                    break
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.exception("Raw API collection failed")
            return await update_status(f"<b>❌ Ошибка при сборе:</b> <code>{e}</code>")

        if not messages:
            return await update_status(f"<b>❌ Сообщений не найдено.</b>")

        messages = messages[:final_limit]
        actual_count = len(messages)
        await update_status(f"<b>🧠 Анализирую {actual_count} сообщений...</b>")
        
        chat_history = "\n".join(messages if direction_down else messages[::-1])
        context_prefix = f"Это сообщения от пользователя {target_user.first_name} (ID: {target_user.id}).\n" if target_user else ""
        prompt = (
            f"{context_prefix}История переписки ниже. Сделай краткую выжимку (summary).\n"
            f"Укажи общее количество проанализированных сообщений ({actual_count}).\n"
            f"Опиши основные темы, интересы или характер общения.\n"
            f"Используй русский язык и форматирование Telegram.\n\n"
            f"История:\n{chat_history}"
        )

        summary = await ai_request(prompt)
        title = f"анализ <b>{target_user.first_name}</b>" if target_user else "суммаризация чата"
        final_text = f"<b>📊 {title.capitalize()} ({actual_count} сообщений):</b>\n\n{summary}"
        
        if len(final_text) > 4096:
            await update_status(summary[:4090] + "...")
        else:
            await update_status(final_text)
    finally:
        active_users.discard(user_id)

async def worker(client):
    while True:
        try:
            message, limit, target_user, direction_down, anchor_id, user_id = await summary_queue.get()
            await process_summary(client, message, limit, target_user, direction_down, anchor_id, user_id)
        except Exception as e:
            logger.error(f"Worker error: {e}")
        finally:
            summary_queue.task_done()

# Start background worker when bot starts
_worker_task = None

@Client.on_message(filters.command(["summarize", "sum"], prefixes=[".", "/"]))
async def summarize_handler(client: Client, message: Message):
    # Check permissions
    user_id = message.from_user.id if message.from_user else 0
    is_owner = message.from_user and message.from_user.is_self
    is_auth = auth_manager.is_authorized(user_id, message.chat.id)
    
    if not (is_owner or is_auth):
        return # Ignore unauthorized people

    # Owner bypasses rate limits
    if not is_owner:
        # Check if user already has a pending or active request
        if user_id in active_users:
            return await message.reply("<b>⚠️ У вас уже есть активный запрос в очереди. Дождитесь завершения.</b>")

        # Check cooldown (60 seconds)
        now = asyncio.get_event_loop().time()
        last_run = user_cooldowns.get(user_id, 0)
        if now - last_run < 60:
            retry_after = int(60 - (now - last_run))
            return await message.reply(f"<b>⏳ Подождите {retry_after} сек. перед следующим запросом.</b>")
        
        user_cooldowns[user_id] = now
        active_users.add(user_id)

    global _worker_task
    if _worker_task is None:
        _worker_task = asyncio.create_task(worker(client))

    if len(message.command) < 2 and not message.reply_to_message and is_owner:
        return await message.edit(
            "<b>Использование .summarize:</b>\n"
            "• <code>.summarize [N]</code> — анализ последних N сообщений.\n"
            "• <code>.summarize [N] -d</code> (в ответе) — анализ N сообщений от этого места вниз.\n"
            "• <code>.summarize [N] [@user/ID]</code> — анализ сообщений конкретного юзера.\n"
        )
    
    limit = 50
    target_user = message.reply_to_message.from_user if message.reply_to_message else None
    direction_down = "-d" in message.command
    
    args = [a for a in message.command[1:] if not a.startswith("-")]
    for arg in args:
        if arg.isdigit() and int(arg) > 0:
            limit = int(arg)
        else:
            try:
                target_user = await client.get_users(arg)
            except:
                pass

    anchor_id = message.reply_to_message_id if message.reply_to_message else 0
    
    if not is_owner:
        pos = summary_queue.qsize() + 1
        message._queue_msg = await message.reply(f"<b>⏳ Запрос добавлен в очередь (позиция: {pos})</b>")
    
    await summary_queue.put((message, limit, target_user, direction_down, anchor_id, user_id))
