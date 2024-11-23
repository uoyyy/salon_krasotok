import telebot
from telebot import types

try:
    from config import API_KEY
except Exception:
    print("Ошибка получения ключа бота из файла config.py")
    exit()

bot = telebot.TeleBot(API_KEY)

masters = ["Антон()", "Валерий()", "Костя()"]
services = ["стрижка","Оформдение бороды и мужская стрижка","","()"]
dates = ["01.01.2024", "02.01.2024", "03.01.2024"]
times = ["09:00", "11:00", "13:00","15:00","17:00",
         "10:00", "12:00", "14:00","16:00","18:00" ]


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    itembtn1 = types.KeyboardButton('Запишитесь на приём')
    markup.add(itembtn1)
    bot.send_message(message.chat.id, "Добро пожаловать в наш ( barber shop ) ! Чем я могу вам помочь?", reply_markup=markup)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == 'Запишитесь на приём':
        msg = bot.reply_to(message, "Пожалуйста, выберите мастера:", reply_markup=generate_markup(masters))
        bot.register_next_step_handler(msg, process_master_choice)


def generate_markup(items):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for item in items:
        markup.add(types.KeyboardButton(item))
    return markup


def process_master_choice(message):
    global chosen_master
    chosen_master = message.text
    msg = bot.reply_to(message, "Пожалуйста, выберите услугу:", reply_markup=generate_markup(services))
    bot.register_next_step_handler(msg, process_service_choice)


def process_service_choice(message):
    global chosen_service
    chosen_service = message.text
    msg = bot.reply_to(message, "Пожалуйста, выберите дату приёма: ", reply_markup=generate_markup(dates))
    bot.register_next_step_handler(msg, process_date_choice)


def process_date_choice(message):
    global chosen_date
    chosen_date = message.text
    msg = bot.reply_to(message, "Пожалуйста, выберите время приёма:", reply_markup=generate_markup(times))
    bot.register_next_step_handler(msg, process_time_choice)


def process_time_choice(message):
    global chosen_time
    chosen_time = message.text
    confirmation_message = f"Вы записались на прием к {chosen_master} for {chosen_service} on {chosen_date} at {chosen_time}. Правильно ли это? (Да/нет)"
    msg = bot.reply_to(message, confirmation_message)
    bot.register_next_step_handler(msg, process_confirmation)


def process_confirmation(message):
    if message.text.lower() == 'Да'or'да':
        bot.send_message(message.chat.id, "Назначение подтверждено. Спасибо!")

    else:
        bot.send_message(message.chat.id, "Запись отменена. Пожалуйста, начните сначала, если хотите записаться еще раз.")


bot.polling()