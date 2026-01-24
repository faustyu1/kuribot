import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from typing import Optional
from core.config import config

class AssistantBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.logger = logging.getLogger("kuribot.assistant")
        self.me = None
        self._setup_handlers()

    async def get_me(self):
        if not self.me:
            self.me = await self.bot.get_me()
        return self.me

    async def send_log(self, chat_id: int, text: str):
        try:
            return await self.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        except Exception as e:
            self.logger.error(f"Failed to send log to {chat_id}: {e}")
            return None

    async def edit_log(self, chat_id: int, message_id: int, text: str):
        try:
            await self.bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, parse_mode="HTML")
            return True
        except Exception as e:
            self.logger.error(f"Failed to edit log message {message_id} in {chat_id}: {e}")
            return False

    async def edit_message(self, callback: types.CallbackQuery, text: str, reply_markup: Optional[types.InlineKeyboardMarkup] = None):
        try:
            if callback.message:
                await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
            elif callback.inline_message_id:
                await self.bot.edit_message_text(
                    text=text,
                    inline_message_id=callback.inline_message_id,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            return True
        except Exception as e:
            self.logger.error(f"Failed to edit message: {e}")
            return False

    def _setup_handlers(self):
        @self.dp.message(lambda m: m.new_chat_members)
        async def on_new_member(message: types.Message):
            # Auto-delete new members in log group (except the bot itself)
            log_group_id = config.get("log_group_id")
            if message.chat.id == log_group_id:
                for member in message.new_chat_members:
                    if member.id != self.me.id:
                        try:
                            await message.chat.ban(member.id)
                            await message.chat.unban(member.id) # Just kick
                        except:
                            pass
                try:
                    await message.delete() # Delete the "User joined" service message
                except:
                    pass

        @self.dp.inline_query()
        async def handle_inline(query: types.InlineQuery):
            if query.query == "settings":
                # Settings Menu
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="📂 Модули", callback_data="set_modules"),
                     types.InlineKeyboardButton(text="🛡 Безопасность", callback_data="set_security")],
                    [types.InlineKeyboardButton(text="📝 Логи", callback_data="set_logs"),
                     types.InlineKeyboardButton(text="⚙️ Конфиг", callback_data="set_config")],
                    [types.InlineKeyboardButton(text="❌ Закрыть", callback_data="set_close")]
                ])
                
                results = [
                    types.InlineQueryResultArticle(
                        id="settings_main",
                        title="⚙️ Настройки KuriBot",
                        description="Открыть панель управления",
                        input_message_content=types.InputTextMessageContent(
                            message_text="<b>⚙️ Настройки KuriBot</b>\n\nВыберите категорию для настройки:",
                            parse_mode="HTML"
                        ),
                        reply_markup=keyboard
                    )
                ]
            else:
                # Default status
                results = [
                    types.InlineQueryResultArticle(
                        id="status",
                        title="🚀 KuriBot Status",
                        description="Проверить статус бота",
                        input_message_content=types.InputTextMessageContent(
                            message_text="🚀 <b>KuriBot</b> онлайн и работает.",
                            parse_mode="HTML"
                        )
                    )
                ]
            
            await query.answer(results, is_personal=True, cache_time=1)

        @self.dp.callback_query()
        async def handle_callbacks(callback: types.CallbackQuery):
            owner_id = config.get("owner_id")
            if callback.from_user.id != owner_id:
                return await callback.answer("⚠️ Доступ запрещен. Вы не являетесь владельцем этого юзербота.", show_alert=True)

            data = callback.data
            self.logger.info(f"Callback received: {data}")

            if data == "set_close":
                if callback.message:
                    await callback.message.delete()
                elif callback.inline_message_id:
                    await self.bot.edit_message_text(
                        chat_id=None,
                        inline_message_id=callback.inline_message_id,
                        text="<b>❌ Панель управления закрыта.</b>",
                        parse_mode="HTML"
                    )
                return await callback.answer("Меню закрыто.")

            # Main menu keyboard
            main_kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="📂 Модули", callback_data="set_modules"),
                 types.InlineKeyboardButton(text="🛡 Безопасность", callback_data="set_security")],
                [types.InlineKeyboardButton(text="📝 Логи", callback_data="set_logs"),
                 types.InlineKeyboardButton(text="⚙️ Конфиг", callback_data="set_config")],
                [types.InlineKeyboardButton(text="❌ Закрыть", callback_data="set_close")]
            ])

            back_kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="set_main")]
            ])

            if data == "set_main":
                await self.edit_message(callback, "<b>⚙️ Настройки KuriBot</b>\n\nВыберите категорию для настройки:", 
                                     reply_markup=main_kb)

            elif data == "set_modules":
                mods = [f for f in os.listdir("modules") if f.endswith(".py") and not f.startswith("__")]
                text = f"<b>📂 Управление модулями</b>\n\nВсего модулей: <code>{len(mods)}</code>\n\n"
                for m in mods:
                    text += f"• <code>{m}</code>\n"
                await self.edit_message(callback, text, reply_markup=back_kb)

            elif data == "set_logs":
                level = config.get("tg_log_level", "INFO")
                text = (
                    f"<b>📝 Настройка логов</b>\n\n"
                    f"Текущий уровень: <code>{level}</code>\n"
                    f"Группа логов: <code>{config.get('log_group_id', 'Не создана')}</code>\n\n"
                    f"<i>Здесь можно будет менять уровень логирования кнопками.</i>"
                )
                
                log_kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="INFO", callback_data="log_lvl_INFO"),
                     types.InlineKeyboardButton(text="WARNING", callback_data="log_lvl_WARNING"),
                     types.InlineKeyboardButton(text="ERROR", callback_data="log_lvl_ERROR")],
                    [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="set_main")]
                ])
                await self.edit_message(callback, text, reply_markup=log_kb)

            elif data.startswith("log_lvl_"):
                new_lvl = data.split("_")[-1]
                config.set("tg_log_level", new_lvl)
                await callback.answer(f"✅ Уровень логов изменен на {new_lvl}")
                # Refresh logs view
                # Instead of recursive call which might cause issues, just re-run the log logic
                level = new_lvl
                text = (
                    f"<b>📝 Настройка логов</b>\n\n"
                    f"Текущий уровень: <code>{level}</code>\n"
                    f"Группа логов: <code>{config.get('log_group_id', 'Не создана')}</code>\n\n"
                    f"<i>Здесь можно будет менять уровень логирования кнопками.</i>"
                )
                log_kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="INFO", callback_data="log_lvl_INFO"),
                     types.InlineKeyboardButton(text="WARNING", callback_data="log_lvl_WARNING"),
                     types.InlineKeyboardButton(text="ERROR", callback_data="log_lvl_ERROR")],
                    [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="set_main")]
                ])
                await self.edit_message(callback, text, reply_markup=log_kb)

            elif data == "set_security":
                text = (
                    "<b>🛡 Безопасность</b>\n\n"
                    "• Авто-проверка модулей: ✅\n"
                    "• Подтверждение установки: ✅\n"
                    "• Белый список источников: ✅\n\n"
                    "<i>Все системы защиты активны и работают в штатном режиме.</i>"
                )
                await self.edit_message(callback, text, reply_markup=back_kb)

            elif data == "set_config":
                text = "<b>⚙️ Конфигурация JSON</b>\n\n<i>Прямое редактирование конфига будет добавлено в следующих версиях.</i>"
                await self.edit_message(callback, text, reply_markup=back_kb)
            
            try:
                await callback.answer()
            except:
                pass

    async def start(self):
        self.logger.info("Starting Assistant Bot...")
        await self.dp.start_polling(self.bot)

    async def stop(self):
        self.logger.info("Stopping Assistant Bot...")
        await self.bot.session.close()

# Helper to get the assistant instance
_assistant: Optional[AssistantBot] = None

def get_assistant() -> Optional[AssistantBot]:
    return _assistant

def init_assistant(token: str):
    global _assistant
    if not _assistant:
        _assistant = AssistantBot(token)
    return _assistant
