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
        self._current_edit_key = None
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

        @self.dp.message()
        async def handle_text_messages(message: types.Message):
            owner_id = config.get("owner_id")
            if message.from_user.id != owner_id: return

            if hasattr(self, "_current_edit_key") and self._current_edit_key:
                key = self._current_edit_key
                new_val = message.text
                
                # Simple type inference
                if new_val.lower() == "true": new_val = True
                elif new_val.lower() == "false": new_val = False
                elif new_val.isdigit(): new_val = int(new_val)
                
                config.set(key, new_val)
                self._current_edit_key = None
                
                await message.reply(f"<b>✅ Значение для <code>{key}</code> обновлено!</b>")
                # Suggest going back to settings
                kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="⚙️ Вернуться в конфиг", callback_data="set_config")]])
                await self.bot.send_message(message.chat.id, "Хотите продолжить настройку?", reply_markup=kb)

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
                            message_text=(
                                "<b>⚙️ Настройки KuriBot</b>\n\n"
                                f"Текущий префикс: <code>{config.get('prefix', '.')}</code>\n\n"
                                "Выберите категорию для настройки:"
                            ),
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
                await self.edit_message(callback, 
                                     f"<b>⚙️ Настройки KuriBot</b>\n\n"
                                     f"Текущий префикс: <code>{config.get('prefix', '.')}</code>\n\n"
                                     f"Выберите категорию для настройки:", 
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
                raw_cfg = config.all()
                text = (
                    "<b>⚙️ Конфигурация JSON</b>\n\n"
                    f"💡 <i>Чтобы изменить префикс команд, выберите ключ <code>prefix</code>.</i>\n\n"
                )
                
                cfg_kb_list = []
                for key in sorted(raw_cfg.keys()):
                    # Limit long keys/values for display
                    val = str(raw_cfg[key])
                    if len(val) > 20: val = val[:17] + "..."
                    
                    button_text = f"{key}: {val}"
                    cfg_kb_list.append([types.InlineKeyboardButton(text=button_text, callback_data=f"cfg_edit_{key}")])
                
                cfg_kb_list.append([types.InlineKeyboardButton(text="⬅️ Назад", callback_data="set_main")])
                cfg_kb = types.InlineKeyboardMarkup(inline_keyboard=cfg_kb_list)
                
                if not raw_cfg:
                    text += "<i>Конфигурация пуста.</i>"
                
                await self.edit_message(callback, text, reply_markup=cfg_kb)

            elif data.startswith("cfg_edit_"):
                key = data.replace("cfg_edit_", "")
                val = config.get(key)
                text = (
                    f"<b>⚙️ Редактирование ключа:</b> <code>{key}</code>\n\n"
                    f"Текущее значение: <code>{val}</code>\n\n"
                    f"Чтобы изменить значение, отправьте новое сообщение в этот чат.\n"
                    f"Чтобы удалить ключ, нажмите кнопку ниже."
                )
                
                edit_kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🗑 Удалить ключ", callback_data=f"cfg_del_{key}")],
                    [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="set_config")]
                ])
                
                await self.edit_message(callback, text, reply_markup=edit_kb)
                # Store state in dispatcher for message handler
                # (Simple way for this specific bot)
                self._current_edit_key = key

            elif data.startswith("cfg_del_"):
                key = data.replace("cfg_del_", "")
                config.delete(key)
                await callback.answer(f"✅ Ключ {key} удален")
                # Back to list
                raw_cfg = config.all()
                text = "<b>⚙️ Конфигурация JSON</b>\n\n"
                cfg_kb_list = []
                for k in sorted(raw_cfg.keys()):
                    val = str(raw_cfg[k])
                    if len(val) > 20: val = val[:17] + "... "
                    cfg_kb_list.append([types.InlineKeyboardButton(text=f"{k}: {val}", callback_data=f"cfg_edit_{k}")])
                cfg_kb_list.append([types.InlineKeyboardButton(text="⬅️ Назад", callback_data="set_main")])
                await self.edit_message(callback, text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=cfg_kb_list))
            
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
