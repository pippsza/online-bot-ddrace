import telebot
import json
import requests
from telebot import types
# import ddapi

TOKEN = '7794487649:AAErzWjY2HSwoelauu1vstH7MXYzpn_24iQ'
url = 'https://ddnet.org/releases/maps.json'
re = requests.get(url)

USERS_FILE = "users.json"

bot = telebot.TeleBot(TOKEN)

user_id = None
# Добаление друзей
waiting_for_friend = set()  # Храним пользователей, которые вводят имя друга

# Функция для загрузки данных из JSON файла


def load_users():
    try:
        with open(USERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []  # Если файл не найден, возвращаем пустой список
    except json.JSONDecodeError:
        return []  # Если файл пуст или поврежден

# Функция для сохранения данных в JSON файл


def save_users(users):
    with open(USERS_FILE, "w") as file:
        json.dump(users, file, indent=4)

# Обработчик команды /start


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def privet(message):
    user_id = message.from_user.id
    # Добавляем пользователя в очередь на ввод имени
    waiting_for_friend.add(user_id)
    bot.send_message(
        message.chat.id, '''
       ❤ Hello. This bot allows you to track your
    friends' activity on DDNET. To get started, register your nickname - just write it in the chat ❤'''
    )

# Обработчик ввода ника


@bot.message_handler(func=lambda message: message.from_user.id in waiting_for_friend)
def handle_text(message):
    user_id = message.from_user.id  # ID пользователя
    player_name = message.text.strip()  # Ник игрока

    if player_name:  # Если имя не пустое
        waiting_for_friend.remove(user_id)  # Убираем пользователя из ожидания

        # Кнопки для подтверждения ника
        keyboard = types.InlineKeyboardMarkup()
        confirm_button = types.InlineKeyboardButton(
            text="✅ Yes ✅", callback_data=f"confirm_{player_name}")
        cancel_button = types.InlineKeyboardButton(
            text="❌ Change ❌", callback_data="cancel_name")
        keyboard.add(confirm_button, cancel_button)

        bot.send_message(
            message.chat.id, f"Is your in-game name correct?: '{player_name}'", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "❌ Please enter a valid nickname.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_nick(call):
    player_name = call.data.split("_")[1]  # Извлекаем ник из callback_data
    global user_id
    user_id = call.from_user.id  # ID пользователя

    # Загружаем пользователей из базы
    users = load_users()

    # Проверка, есть ли пользователь в базе
    existing_user = next(
        (user for user in users if user['user_id'] == user_id), None)

    if not existing_user:  # Если пользователя нет в базе
        new_user = {
            'user_id': user_id,
            'name': player_name,
            'friends': []  # Изначально у пользователя нет друзей
        }
        users.append(new_user)  # Добавляем нового пользователя в список
        save_users(users)  # Сохраняем обновленный список в файл
        bot.send_message(call.message.chat.id,
                         f"You were added to the database, {player_name}!")
    else:
        bot.send_message(call.message.chat.id,
                         f"You are already in the database, {player_name}!")

    # Кнопки меню
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🧩 Menu 🧩")
    bot.send_message(call.message.chat.id,
                     "Thank you for using my bot!", reply_markup=keyboard)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    main_menu(call.message)

# Главное меню


def main_menu(context):
    markup = types.InlineKeyboardMarkup()
    button_friends = types.InlineKeyboardButton(
        text="👥 Friends 👥", callback_data='friend_list')
    button_start_track = types.InlineKeyboardButton(
        text="💢 Start track 💢", callback_data='start_track')
    button_developers = types.InlineKeyboardButton(
        text="💻 Developers 💻", callback_data='button_devs')
    markup.row(button_start_track)
    markup.add(button_friends, button_developers)

    # Проверяем тип объекта (message или call)
    if isinstance(context, types.Message):  # Если это message
        bot.send_message(
            context.chat.id,
            text="""💌 Welcome to my bot!
            Here you can track your friends online in DDNET.""",
            reply_markup=markup
        )
    elif isinstance(context, types.CallbackQuery):  # Если это call
        bot.edit_message_text(
            chat_id=context.message.chat.id,
            message_id=context.message.message_id,
            text="""💌 Welcome to my bot!
            Here you can track your friends online in DDNET.""",
            reply_markup=markup
        )
        bot.answer_callback_query(context.id, "Returning to main menu.")


@bot.callback_query_handler(func=lambda call: call.data == 'button_devs')
def button_devs(call):
    markup = telebot.types.InlineKeyboardMarkup()
    button_devs = telebot.types.InlineKeyboardButton(
        text="💻 Devs 💻", callback_data="devs")
    button_designers = telebot.types.InlineKeyboardButton(
        text="🖌 Designers 🎨", callback_data="designers")
    button_cancel = telebot.types.InlineKeyboardButton(
        text="❌ Cancel ❌", callback_data='cancel')
    markup.row(button_devs, button_designers)
    markup.add(button_cancel)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="""  🔹 Here you can support developers and designers! 
         🔹 Or just ask something them :D """,
        reply_markup=markup
    )
# Обработчик отслеживания игроков


@bot.callback_query_handler(func=lambda call: call.data == 'start_track')
def start_track(call):
    markup = telebot.types.InlineKeyboardMarkup()
    button_cancel = telebot.types.InlineKeyboardButton(
        text="❌Cancel❌", callback_data='cancel')
    markup.row(button_cancel)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="""Players tracking has started...""",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id, "Players tracking has started.")


# Кнопка друзей
@bot.callback_query_handler(func=lambda call: call.data == 'friend_list')
def friend_list(call):
    markup = telebot.types.InlineKeyboardMarkup()
    button_add_friend = telebot.types.InlineKeyboardButton(
        text="🔸 Add a new friend 🔸", callback_data='add_new_friend')
    button_delete_friend = telebot.types.InlineKeyboardButton(
        text="🔹 Delete some friend 🔹", callback_data='delete_friend')
    button_cancel = telebot.types.InlineKeyboardButton(
        text="❌Cancel❌", callback_data='cancel')
    markup.row(button_add_friend)
    markup.add(button_delete_friend)
    markup.add(button_cancel)
    user_id = call.from_user.id  # ID пользователя, нажавшего кнопку

    # Загружаем список пользователей из JSON
    users = load_users()

    # Находим текущего пользователя
    current_user = next(
        (user for user in users if user["user_id"] == user_id), None)

    # Инициализация переменной для друзей
    friends_string = "No friends yet."  # Изначально нет друзей

    if current_user and current_user["friends"]:
        # Преобразуем список друзей в строку
        friends_string = ", ".join(current_user["friends"])

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"""Your friends:
         {friends_string}
        """,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id, "Here is your friends list.")


@bot.callback_query_handler(func=lambda call: call.data == 'add_new_friend')
def add_new_friend(call):
    user_id = call.from_user.id  # ID пользователя
    waiting_for_friend.add(user_id)  # Помечаем, что пользователь вводит друга

    markup = types.InlineKeyboardMarkup()
    button_cancel = types.InlineKeyboardButton(
        text="❌ Cancel ❌", callback_data='cancel_friend_input')
    markup.row(button_cancel)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="✅ Please write your friend's name in the chat.",
        reply_markup=markup
    )

    bot.register_next_step_handler(call.message, process_friend_name)


@bot.callback_query_handler(func=lambda call: call.data == 'cancel_friend_input')
def cancel_friend_input(call):
    user_id = call.from_user.id
    waiting_for_friend.discard(user_id)  # Убираем из списка ожидающих ввода
    bot.send_message(call.message.chat.id, "❌ Friend adding was canceled.")
    main_menu(call.message)  # Возвращаем в главное меню

# Обработчик вводы ника друга


def process_friend_name(message):
    user_id = message.from_user.id

    # Проверяем, отменил ли пользователь ввод
    if user_id not in waiting_for_friend:
        return  # Если пользователь отменил, не обрабатываем ввод

    waiting_for_friend.discard(user_id)  # Убираем из списка ожидающих

    friend_name = message.text.strip()  # Имя друга, введённое пользователем
    users = load_users()
    current_user = next(
        (user for user in users if user["user_id"] == user_id), None)

    if current_user:
        if friend_name in current_user["friends"]:
            bot.send_message(
                message.chat.id, f"'{friend_name}' is already in your friends list!")
        else:
            current_user["friends"].append(friend_name)
            save_users(users)
            bot.send_message(
                message.chat.id, f"✅ Friend '{friend_name}' added successfully!")
    else:
        bot.send_message(
            message.chat.id, "❌ You are not registered yet. Use /start to register.")

    main_menu(message)  # Возвращаем в главное меню


# Обработка удаления друзей


@bot.callback_query_handler(func=lambda call: call.data == 'delete_friend')
def delete_friend(call):
    user_id = call.from_user.id  # ID пользователя, нажавшего кнопку

    # Загружаем список пользователей из JSON
    users = load_users()

    # Находим текущего пользователя
    current_user = next(
        (user for user in users if user["user_id"] == user_id), None)

    if current_user and current_user["friends"]:
        # Генерируем кнопки с именами друзей
        markup = types.InlineKeyboardMarkup()
        for friend in current_user["friends"]:
            button = types.InlineKeyboardButton(
                text=friend, callback_data=f"remove_friend_{friend}")
            markup.add(button)

        # Добавляем кнопку "Отмена"
        button_cancel = types.InlineKeyboardButton(
            text="❌ Cancel ❌", callback_data='cancel')
        markup.add(button_cancel)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🗑 Select a friend to remove:",
            reply_markup=markup
        )
    else:
        bot.send_message(call.message.chat.id,
                         "❌ You don't have any friends to remove.")

# Обработка выбора друга для удаления


@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_friend_"))
def remove_friend(call):
    user_id = call.from_user.id  # ID пользователя, нажавшего кнопку
    friend_name = call.data.split("remove_friend_")[
        1]  # Имя друга из callback_data

    # Загружаем список пользователей из JSON
    users = load_users()

    # Находим текущего пользователя
    current_user = next(
        (user for user in users if user["user_id"] == user_id), None)

    if current_user and friend_name in current_user["friends"]:
        # Удаляем друга из списка
        current_user["friends"].remove(friend_name)
        save_users(users)  # Сохраняем изменения в JSON

        bot.send_message(call.message.chat.id, f"✅ Friend '{
                         friend_name}' was removed successfully!")
    else:
        bot.send_message(call.message.chat.id, f"❌ Friend '{
                         friend_name}' not found in your list.")

    # Возвращаем пользователя в главное меню
    main_menu(call.message)


# Кнопка дизайнеров
@bot.callback_query_handler(func=lambda call: call.data == 'designers')
def artist(call):
    markup = telebot.types.InlineKeyboardMarkup()
    button_cancel = telebot.types.InlineKeyboardButton(
        text="❌Cancel❌", callback_data='cancel')
    markup.row(button_cancel)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="""   
       Monik will be very happy if you subscribe to his YouTube channel!
         He tries very hard for his subscribers 😉
    💠 https://youtube.com/@monikddnet?si=p9UebRpPbE1ptVhk 💠""",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id, "Subscribe on Mónik !")


# возврат в главное меню
@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def return_to_main_menu(call):
    main_menu(call)
# Кнопка разработчиков


@bot.callback_query_handler(func=lambda call: call.data == 'devs')
def devs(call):
    markup = telebot.types.InlineKeyboardMarkup()
    button_cancel = telebot.types.InlineKeyboardButton(
        text="❌Cancel❌", callback_data='cancel')
    markup.row(button_cancel)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="""Pipsha will be very happy if you follow him on TikTok!
    💠 https://www.tiktok.com/@pippsza.ddnet?_t=ZM-8t9I3DDMaHN&_r=1 💠""",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id, "Subscribe on1 pippsza!.")
# Отменить имя


# Обработчик отмены ввода ника
@bot.callback_query_handler(func=lambda call: call.data == 'cancel_name')
def cancel_action(call):
    user_id = call.from_user.id  # Получаем ID пользователя

    # Убираем пользователя из списка ожидания
    waiting_for_friend.discard(user_id)

    # Предлагаем пользователю ввести имя заново
    bot.send_message(call.message.chat.id,
                     "Operation was canceled. Please enter your name again!")

    # Убираем сообщение с кнопками подтверждения
    bot.delete_message(call.message.chat.id, call.message.message_id)

    # Запрашиваем имя снова
    waiting_for_friend.add(user_id)  # Добавляем в список ожидающих
    # Перенаправляем в функцию ввода текста
    bot.register_next_step_handler(call.message, handle_text)


if __name__ == '__main__':
    bot.polling(none_stop=True)
