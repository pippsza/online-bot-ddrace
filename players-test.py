#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================================================================================
Телеграм-бот для отслеживания активности друзей в игре DDNET
===================================================================================================
Описание:
  Этот бот позволяет пользователям отслеживать состояние (онлайн, AFK, оффлайн) их друзей в игре DDNET.
  Пользователь регистрирует свой никнейм, добавляет друзей, а затем нажатием кнопки "Start track"
  бот запускает процесс отслеживания. При изменении статуса друзей бот отправляет обновлённую информацию.
  
  Для каждого пользователя хранится его предыдущий кейс (состояние друзей), и новое сообщение отправляется
  только если изменился статус именно его друзей.
  
  Вывод информации оформлен в виде «таблицы»: для онлайн и AFK игроков поля (игрок, режим, сервер, карта)
  разделяются вертикальными палочками («|»). Для каждой записи над строкой с данными выводится строка разделения
  из 69 символов "-", а между группами (онлайн, AFK, оффлайн) – строка из 69 символов "=".
  
  В каждом сообщении с активностью присутствует кнопка Cancel, которая останавливает отслеживание и возвращает
  пользователя в главное меню.
  
Используемые библиотеки:
  - telebot: для работы с Telegram Bot API
  - json: для сохранения и загрузки данных пользователей
  - requests: для HTTP-запросов (при необходимости)
  - asyncio: для асинхронного выполнения периодических запросов
  - threading: для запуска event loop в отдельном потоке
  - ddapi: для получения информации о серверах DDNET (библиотека, реализующая API)

Версия: 1.1
Автор: Your Name
===================================================================================================
"""

# ===================================== Импорты =====================================
import telebot
import json
import requests
import asyncio
import threading
from telebot import types
from ddapi import DDnetApi

# ===================================== Глобальные переменные =====================================
TOKEN = '7794487649:AAErzWjY2HSwoelauu1vstH7MXYzpn_24iQ'

# Для каждого пользователя будем хранить его предыдущие состояния
user_prev_online = {}   # dict: user_id -> set((player, game_type, server, map))
user_prev_afk = {}      # dict: user_id -> set((player, game_type, server, map))
user_prev_offline = {}  # dict: user_id -> set(friend)

# Файл для хранения данных пользователей
USERS_FILE = "users.json"

# Словарь для хранения асинхронных задач отслеживания для каждого пользователя
tracking_tasks = {}

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Множество для хранения id пользователей, ожидающих ввода ника или имени друга
waiting_for_friend = set()

# ===================================== Настройка асинхронного цикла =====================================
global_loop = asyncio.new_event_loop()

def start_loop(loop):
    """Запуск asyncio event loop в отдельном потоке."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

asyncio_thread = threading.Thread(target=start_loop, args=(global_loop,), daemon=True)
asyncio_thread.start()

# ===================================== Функции для работы с пользователями =====================================
def load_users():
    """
    Загружает список пользователей из JSON-файла.
    Возвращает список пользователей или пустой список, если файл отсутствует/повреждён.
    """
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_users(users):
    """
    Сохраняет список пользователей в JSON-файл.
    Аргументы:
      users - список пользователей
    """
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4, ensure_ascii=False)

def stop_tracking(user_id):
    """
    Останавливает асинхронную задачу отслеживания для пользователя, если она запущена.
    """
    global tracking_tasks
    if user_id in tracking_tasks:
        future = tracking_tasks[user_id]
        future.cancel()  # Отменяем задачу
        del tracking_tasks[user_id]
        print(f"[DEBUG] Tracking for user {user_id} has been cancelled.")

# ===================================== Асинхронная функция отслеживания =====================================
async def fetch_server_info(user_id):
    """
    Асинхронная функция, периодически запрашивающая информацию с серверов DDNET
    и отправляющая обновлённое сообщение пользователю, если изменилось состояние его друзей.
    
    Аргументы:
      user_id: Telegram ID пользователя, для которого осуществляется отслеживание.
    """
    api = DDnetApi()

    # Загружаем список пользователей и находим текущего
    users = load_users()
    current_user = next((user for user in users if user["user_id"] == user_id), None)
    if not current_user or not current_user.get("friends"):
        print(f"[DEBUG] Пользователь {user_id} не найден или не добавлены друзья.")
        return

    players_to_find = current_user["friends"]

    # Инициализируем сохранённое состояние для пользователя, если ещё не инициализировано
    if user_id not in user_prev_online:
        user_prev_online[user_id] = set()
    if user_id not in user_prev_afk:
        user_prev_afk[user_id] = set()
    if user_id not in user_prev_offline:
        user_prev_offline[user_id] = set()

    try:
        while True:
            message_parts = []
            changed = False

            try:
                users = load_users()
                current_user = next((user for user in users if user["user_id"] == user_id), None)
                username = current_user.get("name", "Unknown") if current_user else "Unknown"
                print(f"[DEBUG] Пользователь {username} (ID: {user_id}): запущен цикл получения данных с сервера DDNET...")
                server_info = await api.master()


                online_players = set()
                afk_players = set()

                if server_info and hasattr(server_info, 'servers'):
                    for server in server_info.servers:
                        server_name = server.info.name
                        map_name = server.info.map.name
                        game_type = server.info.game_type

                        for client in server.info.clients:
                            player_name = client.name
                            afk_status = client.afk

                            if player_name in players_to_find:
                                if afk_status:
                                    afk_players.add((player_name, game_type, server_name, map_name))
                                else:
                                    online_players.add((player_name, game_type, server_name, map_name))

                online_names = {p[0] for p in online_players}
                afk_names = {p[0] for p in afk_players}
                offline_players = set(friend for friend in players_to_find if friend not in online_names and friend not in afk_names)

                # Форматирование секции онлайн игроков
                                # Обновляем состояние и формируем секцию онлайн игроков, если набор не пустой
                if online_players != user_prev_online[user_id]:
                    user_prev_online[user_id] = online_players.copy()
                    if online_players:
                        section = "🟢 Online players:\n"
                        for p in online_players:
                            player, game_type, server, map_name = p
                            line = f"❇️  {player} | {game_type} | {server} | {map_name}  ❇️"
                            section += "-" * 69 + "\n" + line + "\n"
                        section += "=" * 35 + "\n"
                        message_parts.append(section)
                        changed = True

                # Обновляем состояние и формируем секцию AFK игроков, если набор не пустой
                if afk_players != user_prev_afk[user_id]:
                    user_prev_afk[user_id] = afk_players.copy()
                    if afk_players:
                        section = "💤 AFK players:\n"
                        for p in afk_players:
                            player, game_type, server, map_name = p
                            line = f"😴  {player} | {game_type} | {server} | {map_name}  😴"
                            section += "-" * 69 + "\n" + line + "\n"
                        section += "=" * 35 + "\n"
                        message_parts.append(section)
                        changed = True

                # Обновляем состояние и формируем секцию оффлайн игроков, если набор не пустой
                if offline_players != user_prev_offline[user_id]:
                    user_prev_offline[user_id] = offline_players.copy()
                    if offline_players:
                        section = "💢 Offline players:\n"
                        for friend in offline_players:
                            line = f"⛔  {friend}  ⛔"
                            section += "-" * 69 + "\n" + line + "\n"
                        section += "=" * 35 + "\n"
                        message_parts.append(section)
                        changed = True


                if changed:
                    players_info = "\n".join(message_parts)
                    # Обновляем сохранённое состояние
                    user_prev_online[user_id] = online_players.copy()
                    user_prev_afk[user_id] = afk_players.copy()
                    user_prev_offline[user_id] = offline_players.copy()

                    markup = types.InlineKeyboardMarkup()
                    button_cancel = types.InlineKeyboardButton(text="❌ Cancel ❌", callback_data="cancel")
                    markup.add(button_cancel)
                    try:
                        bot.send_message(user_id, players_info, reply_markup=markup)
                        print(f"[DEBUG] Пользователю {user_id} отправлено сообщение об изменениях:")
                        print(players_info)
                    except Exception as send_error:
                        print(f"[DEBUG] Ошибка при отправке сообщения пользователю {user_id}: {send_error}")

            except Exception as e:
                print(f"[DEBUG] Ошибка при получении данных с сервера для пользователя {user_id}: {e}")

            await asyncio.sleep(10)
    except asyncio.CancelledError:
        print(f"[DEBUG] Отслеживание для пользователя {user_id} было отменено.")
        return

# ===================================== Обработчики команд и сообщений =====================================
@bot.message_handler(commands=['start'])
def privet(message):
    user_id_local = message.from_user.id
    stop_tracking(user_id_local)
    waiting_for_friend.add(user_id_local)
    bot.send_message(
        message.chat.id,
        "❤ Hello. This bot allows you to track your friends' activity on DDNET.\n"
        "To get started, register your nickname – just write it in the chat ❤"
    )

@bot.message_handler(func=lambda message: message.from_user.id in waiting_for_friend)
def handle_text(message):
    user_id_local = message.from_user.id
    player_name = message.text.strip()

    if player_name:
        waiting_for_friend.discard(user_id_local)
        keyboard = types.InlineKeyboardMarkup()
        confirm_button = types.InlineKeyboardButton(text="✅ Yes ✅", callback_data=f"confirm_{player_name}")
        cancel_button = types.InlineKeyboardButton(text="❌ Change ❌", callback_data="cancel_name")
        keyboard.add(confirm_button, cancel_button)
        bot.send_message(message.chat.id, f"Is your in-game name correct?: '{player_name}'", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "❌ Please enter a valid nickname.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_nick(call):
    parts = call.data.split("_", 1)
    if len(parts) < 2:
        bot.send_message(call.message.chat.id, "❌ Incorrect data received.")
        return
    player_name = parts[1]
    global_user = call.from_user.id

    users = load_users()
    existing_user = next((user for user in users if user['user_id'] == global_user), None)

    if not existing_user:
        new_user = {
            'user_id': global_user,
            'name': player_name,
            'friends': []
        }
        users.append(new_user)
        save_users(users)
        bot.send_message(call.message.chat.id, f"You were added to the database, {player_name}!")
    else:
        bot.send_message(call.message.chat.id, f"You are already in the database, {player_name}!")

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🧩 Menu 🧩")
    bot.send_message(call.message.chat.id, "Thank you for using my bot!", reply_markup=keyboard)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    main_menu(call.message)

@bot.message_handler(func=lambda message: message.text == "🧩 Menu 🧩")
def menu_handler(message):
    main_menu(message)

def main_menu(context):
    user_id_local = None
    if isinstance(context, types.Message):
        user_id_local = context.from_user.id
    elif isinstance(context, types.CallbackQuery):
        user_id_local = context.from_user.id

    if user_id_local:
        stop_tracking(user_id_local)

    markup = types.InlineKeyboardMarkup()
    button_friends = types.InlineKeyboardButton(text="👥 Friends 👥", callback_data='friend_list')
    button_start_track = types.InlineKeyboardButton(text="💢 Start track 💢", callback_data='start_track')
    button_developers = types.InlineKeyboardButton(text="💻 Developers 💻", callback_data='button_devs')
    markup.row(button_start_track)
    markup.add(button_friends, button_developers)

    if isinstance(context, types.Message):
        bot.send_message(context.chat.id,
                         "💌 Welcome to my bot!\nHere you can track your friends online in DDNET.",
                         reply_markup=markup)
    elif isinstance(context, types.CallbackQuery):
        bot.edit_message_text(chat_id=context.message.chat.id,
                              message_id=context.message.message_id,
                              text="💌 Welcome to my bot!\nHere you can track your friends online in DDNET.",
                              reply_markup=markup)
        bot.answer_callback_query(context.id, "Returning to main menu.")

@bot.callback_query_handler(func=lambda call: call.data == 'start_track')
def start_track(call):
    user_id_local = call.from_user.id
    stop_tracking(user_id_local)
    markup = types.InlineKeyboardMarkup()
    button_cancel = types.InlineKeyboardButton(text="❌ Cancel ❌", callback_data="cancel")
    markup.row(button_cancel)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="Players tracking has started...",
                          reply_markup=markup)
    bot.answer_callback_query(call.id, "Players tracking has started.")
    future = asyncio.run_coroutine_threadsafe(fetch_server_info(user_id_local), global_loop)
    tracking_tasks[user_id_local] = future

@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel_action(call):
    user_id_local = call.from_user.id
    stop_tracking(user_id_local)
    main_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == 'friend_list')
def friend_list(call):
    markup = types.InlineKeyboardMarkup()
    button_add_friend = types.InlineKeyboardButton(text="🔸 Add a new friend 🔸", callback_data='add_new_friend')
    button_delete_friend = types.InlineKeyboardButton(text="🔹 Delete some friend 🔹", callback_data='delete_friend')
    button_cancel = types.InlineKeyboardButton(text="❌ Cancel ❌", callback_data='cancel')
    markup.row(button_add_friend)
    markup.add(button_delete_friend)
    markup.add(button_cancel)
    user_id_local = call.from_user.id

    users = load_users()
    current_user = next((user for user in users if user["user_id"] == user_id_local), None)
    friends_string = "No friends yet."
    if current_user and current_user.get("friends"):
        friends_string = ", ".join(current_user["friends"])

    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=f"Your friends:\n{friends_string}",
                          reply_markup=markup)
    bot.answer_callback_query(call.id, "Here is your friends list.")

@bot.callback_query_handler(func=lambda call: call.data == 'add_new_friend')
def add_new_friend(call):
    user_id_local = call.from_user.id
    waiting_for_friend.add(user_id_local)
    markup = types.InlineKeyboardMarkup()
    button_cancel = types.InlineKeyboardButton(text="❌ Cancel ❌", callback_data='cancel_friend_input')
    markup.row(button_cancel)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="✅ Please write your friend's name in the chat.",
                          reply_markup=markup)
    bot.register_next_step_handler(call.message, process_friend_name)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_friend_input')
def cancel_friend_input(call):
    user_id_local = call.from_user.id
    waiting_for_friend.discard(user_id_local)
    bot.send_message(call.message.chat.id, "❌ Friend adding was canceled.")
    main_menu(call.message)

def process_friend_name(message):
    user_id_local = message.from_user.id
    if user_id_local not in waiting_for_friend:
        return
    waiting_for_friend.discard(user_id_local)
    friend_name = message.text.strip()
    users = load_users()
    current_user = next((user for user in users if user["user_id"] == user_id_local), None)
    if current_user:
        if friend_name in current_user.get("friends", []):
            bot.send_message(message.chat.id, f"'{friend_name}' is already in your friends list!")
        else:
            current_user.setdefault("friends", []).append(friend_name)
            save_users(users)
            bot.send_message(message.chat.id, f"✅ Friend '{friend_name}' added successfully!")
    else:
        bot.send_message(message.chat.id, "❌ You are not registered yet. Use /start to register.")
    main_menu(message)

@bot.callback_query_handler(func=lambda call: call.data == 'delete_friend')
def delete_friend(call):
    user_id_local = call.from_user.id
    users = load_users()
    current_user = next((user for user in users if user["user_id"] == user_id_local), None)
    if current_user and current_user.get("friends"):
        markup = types.InlineKeyboardMarkup()
        for friend in current_user["friends"]:
            button = types.InlineKeyboardButton(text=friend, callback_data=f"remove_friend_{friend}")
            markup.add(button)
        button_cancel = types.InlineKeyboardButton(text="❌ Cancel ❌", callback_data='cancel')
        markup.add(button_cancel)
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="🗑 Select a friend to remove:",
                              reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "❌ You don't have any friends to remove.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_friend_"))
def remove_friend(call):
    user_id_local = call.from_user.id
    friend_name = call.data.split("remove_friend_")[1]
    users = load_users()
    current_user = next((user for user in users if user["user_id"] == user_id_local), None)
    if current_user and friend_name in current_user.get("friends", []):
        current_user["friends"].remove(friend_name)
        save_users(users)
        bot.send_message(call.message.chat.id, f"✅ Friend '{friend_name}' was removed successfully!")
    else:
        bot.send_message(call.message.chat.id, f"❌ Friend '{friend_name}' not found in your list.")
    main_menu(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'button_devs')
def button_devs(call):
    markup = types.InlineKeyboardMarkup()
    button_devs = types.InlineKeyboardButton(text="💻 Devs 💻", callback_data="devs")
    button_designers = types.InlineKeyboardButton(text="🖌 Designers 🎨", callback_data="designers")
    button_cancel = types.InlineKeyboardButton(text="❌ Cancel ❌", callback_data='cancel')
    markup.row(button_devs, button_designers)
    markup.add(button_cancel)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="🔹 Here you can support developers and designers!\n🔹 Or just ask them something :D",
                          reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'designers')
def artist(call):
    markup = types.InlineKeyboardMarkup()
    button_cancel = types.InlineKeyboardButton(text="❌ Cancel ❌", callback_data='cancel')
    markup.row(button_cancel)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=("""   
Monik will be very happy if you subscribe to his YouTube channel!
He works very hard for his subscribers 😉
💠 https://youtube.com/@monikddnet?si=p9UebRpPbE1ptVhk 💠
                          """),
                          reply_markup=markup)
    bot.answer_callback_query(call.id, "Subscribe on Mónik!")

@bot.callback_query_handler(func=lambda call: call.data == 'devs')
def devs(call):
    markup = types.InlineKeyboardMarkup()
    button_cancel = types.InlineKeyboardButton(text="❌ Cancel ❌", callback_data='cancel')
    markup.row(button_cancel)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=("""Pipsha will be very happy if you follow him on TikTok!
💠 https://www.tiktok.com/@pippsza.ddnet?_t=ZM-8t9I3DDMaHN&_r=1 💠
                          """),
                          reply_markup=markup)
    bot.answer_callback_query(call.id, "Subscribe on pippsza!")

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_name')
def cancel_action(call):
    user_id_local = call.from_user.id
    waiting_for_friend.discard(user_id_local)
    bot.send_message(call.message.chat.id, "Operation was canceled. Please enter your name again!")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    waiting_for_friend.add(user_id_local)
    bot.register_next_step_handler(call.message, handle_text)

def debug_print(message):
    from datetime import datetime
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

if __name__ == '__main__':
    debug_print("Бот запускается...")
    try:
        bot.polling(none_stop=True)
    except Exception as main_e:
        debug_print(f"Ошибка в основном цикле polling: {main_e}")
