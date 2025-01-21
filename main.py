import telebot
import json
import requests
from telebot import types

TOKEN = '7794487649:AAErzWjY2HSwoelauu1vstH7MXYzpn_24iQ'
url = 'https://ddnet.org/releases/maps.json'
re = requests.get(url)

USERS_FILE = "users.json"

bot = telebot.TeleBot(TOKEN)

user_id = None

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


@bot.message_handler(commands=['start'])
def privet(message):
    bot.send_message(
        message.chat.id, '''
       ❤ Hello. This bot allows you to track your
    friends' activity on DDNET. To get started, register your nickname - just write it in the chat ❤''')

# Обработчик ввода ника и сохранения его в базу данных


@bot.message_handler(content_types=['text'])
def handle_text(message):
    global user_id
    user_id = message.from_user.id  # ID пользователя
    player_name = message.text  # Ник игрока
    if message.text == '🧩 Menu 🧩':
        main_menu(message)
        return
    # Кнопки для подтверждения ника
    keyboard = types.InlineKeyboardMarkup()
    confirm_button = types.InlineKeyboardButton(
        text="✅ Yes ✅", callback_data=f"confirm_{player_name}")
    cancel_button = types.InlineKeyboardButton(
        text="❌ Change ❌", callback_data="cancel_name")
    keyboard.add(confirm_button, cancel_button)

    bot.send_message(
        message.chat.id, f"Is your ingame name correct?: '{player_name}'", reply_markup=keyboard)


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


@bot.callback_query_handler(func=lambda call: call.data == 'cancel_name')
def cancel_action(call):
    bot.send_message(call.message.chat.id,
                     "Operation was canceled. Please enter your name again!")
    bot.delete_message(call.message.chat.id, call.message.message_id)


if __name__ == '__main__':
    bot.polling(none_stop=True)
