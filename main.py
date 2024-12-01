import telebot
from telebot import types
from database_root import *
from settings import START_TEXT, MAIN_MENU_BUTTON_TEXT, MAIN_MENU_SECTION_TEXT

try:
    from config import API_KEY
except Exception as e:
    print("Ошибка получения ключа бота из файла config.py: {}".format(e))
    exit()

bot = telebot.TeleBot(API_KEY)


def get_place_id_from_url(message):
    message = message.text.split()
    if len(message) > 1:
        return message[1]
    return None


def get_preuser(message):
    return User.get_preuser(message.chat.id)


def get_user(message):
    return User.get_user(message.chat.id)


def check_user(message):
    return User.check_user(message.chat.id)


def check_preuser(message):
    return User.check_preuser(message.chat.id)


def check_prepreuser(message):
    return User.check_prepreuser(message.chat.id)


def check_preuser_name(message):
    return User.get_preuser_name(message.chat.id)


def edit_user(message, name=None, number=None):
    if number is None:
        if name is None:
            User.create_prepreuser(message.chat.id)
        else:
            User.create_preuser(message.chat.id, name=name)
    else:
        User.create_user(message.chat.id, number=number)


@bot.message_handler(commands=['start'])
def start(message):
    if check_user(message):
        if get_place_id_from_url(message) is None:
            main_menu(message)
        else:
            place_id = int(get_place_id_from_url(message))
            start_record(message, place_id)
    elif check_preuser(message):
        handle_message(message)
    else:
        edit_user(message)
        bot.send_message(message.chat.id, f"{START_TEXT} Отправьте, пожалуйста, ваше имя")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if check_preuser(message):
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_phone = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
        keyboard.add(button_phone)
        bot.send_message(message.chat.id, 'Теперь отправьте нам ваш номер', reply_markup=keyboard)
    elif check_prepreuser(message):
        edit_user(message, name=message.text)
        message.text = ""
        handle_message(message)
    else:
        bot.send_message(message.chat.id, f"Я вас не понимаю")


@bot.message_handler(content_types=['contact'])
def contact(message):
    if message.contact is not None:
        if check_user(message):
            bot.send_message(message.chat.id, f"Я вас не понимаю, {get_user(message).name}. ")
        elif check_preuser(message):
            edit_user(message, number=message.contact.phone_number)
            bot.send_message(message.chat.id, f"Отлично! Осталось ещё немного до конца регистрации",
                             reply_markup=types.ReplyKeyboardRemove())
            choose_city(message)
            return
        else:
            bot.send_message(message.chat.id, f"Я вас не понимаю")
        main_menu(message)


def generate_markup(items):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for (name, callback_data) in items:
        markup.add(types.InlineKeyboardButton(name, callback_data=callback_data))
    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data:
        section, *args = call.data.split(".")
        if section == "main_menu":
            main_menu(call.message)
        elif section == "start_record_by_type":
            start_record_by_type(call.message)
        elif section == "start_record_by_type_of_service":
            start_record_by_type_of_service(call.message, args[0])
        elif section == "start_record_by_service":
            start_record_by_service(call.message, args[0])
        elif section == "start_record_by_center":
            start_record_by_center(call.message, args[0])
        elif section == "start_record_by_place":
            start_record_by_place(call.message, args[0])
        elif section == "start_record":
            start_record(call.message, args[0])
        elif section == "start_record_by_date":
            start_record_by_date(call.message, args[0])
        elif section == "show_records":
            show_records(call.message)
        elif section == "choose_city":
            if len(args) == 0:
                choose_city(call.message)
            else:
                set_new_city_from_choose_city(call.message, args[0])
        else:
            print(f"Нет обработчика для '{section}' с аргументами: {str(args)}")
            i_dont_know_that_command(call.message)
        bot.delete_message(call.message.chat.id, call.message.message_id)


def main_menu(message):
    markup = generate_markup([(f"📝 Записаться", f"start_record_by_type"),
                              (f"📔 Мои записи", f"show_records"),
                              (f"🏙️ Поменять город", f"choose_city")])

    bot.send_message(message.chat.id, f"{MAIN_MENU_SECTION_TEXT()}\n\nЧем я могу вам помочь, {get_user(message).name}?",
                     reply_markup=markup)


def start_record_by_type(message):
    cur_types = list()
    for cur_type in GET_TYPES():
        cur_types.append((cur_type.name, f"start_record_by_type_of_service.{cur_type.id}"))
    cur_types.append((MAIN_MENU_BUTTON_TEXT, "main_menu"))
    markup = generate_markup(cur_types)

    bot.send_message(message.chat.id, f"Выберите вид услуги, на которую вы хотите записаться:",
                     reply_markup=markup)


def start_record_by_type_of_service(message, type_id):
    markup = generate_markup([(f"🎫 Запись по конкретной услуге", f"start_record_by_service.{type_id}"),
                              (f"🏢 Запись в конкретный салон", f"start_record_by_center.{type_id}"),
                              (f"⬅️ Вернуться к выбору вида услуги", f"start_record_by_type"),
                              (MAIN_MENU_BUTTON_TEXT, "main_menu")])

    bot.send_message(message.chat.id, f"Как именно вы хотели бы записаться?",
                     reply_markup=markup)


# TODO: добавить в БД услуги, привязать их айди к place (салоны) и records (записи в салоны) TODO: добавить
# TODO: функционал для услуг: выбор услуг, доступных в текущем городе, далее предложение сетей салонов, по этому городу
#  и этим услугам, далее салоны (тоже с этого города и этими услугами), а далее start_record с id выбранного салона
def start_record_by_service(message, type_id):
    i_dont_know_that_command(message)


# TODO: выдача сетей, которые есть в городе пользователя
def start_record_by_center(message, type_id):
    cur_centers = list()
    for cur_center in GET_CENTERS_BY_TYPE(type_id):
        cur_centers.append((cur_center.name, f"start_record_by_place.{cur_center.id}"))
    cur_centers.append((MAIN_MENU_BUTTON_TEXT, "main_menu"))
    markup = generate_markup(cur_centers)

    bot.send_message(message.chat.id, f"Выберите сеть салонов, в который вы хотите записаться:",
                     reply_markup=markup)


# TODO: выдача салонов, которые есть в городе пользователя
def start_record_by_place(message, center_id):
    cur_places = list()
    for cur_place in GET_PLACES_BY_CENTER(center_id):
        cur_places.append((cur_place.address, f"start_record.{cur_place.id}"))
    cur_places.append((f"⬅️ Вернуться к выбору сети салонов", f"start_record_by_center.{GET_CENTER(center_id).type_id}"))
    cur_places.append((MAIN_MENU_BUTTON_TEXT, "main_menu"))
    markup = generate_markup(cur_places)

    bot.send_message(message.chat.id, f"Выберите салон сети {GET_CENTER(center_id).name}, в который вы хотите записаться:",
                     reply_markup=markup)


def start_record(message, place_id):
    place = GET_PLACE(place_id)
    markup = generate_markup([(f"📅 Выбрать дату и время записи", f"start_record_by_date.{place_id}"),
                              (f"⬅️ Вернуться к выбору салонов {place.center.name}", f"start_record_by_place.{place.center.type_id}"),
                              (MAIN_MENU_BUTTON_TEXT, "main_menu")])

    bot.send_message(message.chat.id, f"Сейчас вы планируете запись в '{place.center.name}' по адресу: {place.address}",
                     reply_markup=markup)


# TODO: доделать запись по дате и времени через datetime, запись в БД, отсылку салону о новой записи
def start_record_by_date(message, place_id):
    i_dont_know_that_command(message)


# TODO: добавить показ всех актуальных записей пользователя, отстортированных от самого ближайшего
#  к самому позднему, а также добавить возможность отменять запись
def show_records(message):
    i_dont_know_that_command(message)


def choose_city(message):
    cities = list()
    for city in GET_CITIES():
        cities.append((city.name, f"choose_city.{city.id}"))
    markup = generate_markup(cities)

    bot.send_message(message.chat.id, f"Выберите город, в котором хотите записаться:",
                     reply_markup=markup)


def set_new_city_from_choose_city(message, city_id):
    if GET_USER(message.chat.id).city:
        bot.send_message(message.chat.id, f"Отлично! Вы выбрали город: {GET_CITY_OBJECT(city_id).name}")
    else:
        bot.send_message(message.chat.id, f"Поздравляем с успешной регистрацией, {GET_USER(message.chat.id).name}! Вы выбрали город: {GET_CITY_OBJECT(city_id).name}")
    SET_USER_CITY(message.chat.id, city_id)
    main_menu(message)


def i_dont_know_that_command(message):
    markup = generate_markup([(MAIN_MENU_BUTTON_TEXT, "main_menu")])

    bot.send_message(message.chat.id, f"Пока что я такого не умею. Прости, {get_user(message).name}, я глупый 😞",
                     reply_markup=markup)


# остальное


# masters = ["Антон()", "Валерий()", "Вася()"]
# services = ["стрижка", "Оформление бороды и мужская стрижка", "", "()"]
# dates = ["01.01.2024", "02.01.2024", "03.01.2024"]
# times = ["09:00", "11:00", "13:00", "15:00", "17:00",
#          "10:00", "12:00", "14:00", "16:00", "18:00"]
# chosen_master = None
# chosen_service = None
# chosen_date = None
# chosen_time = None
#
#
# def process_master_choice(message):
#     global chosen_master
#     chosen_master = message.text
#     msg = bot.reply_to(message, "Пожалуйста, выберите услугу:", reply_markup=generate_markup(services))
#     bot.register_next_step_handler(msg, process_service_choice)
#
#
# def process_service_choice(message):
#     global chosen_service
#     chosen_service = message.text
#     msg = bot.reply_to(message, "Пожалуйста, выберите дату приёма: ", reply_markup=generate_markup(dates))
#     bot.register_next_step_handler(msg, process_date_choice)
#
#
# def process_date_choice(message):
#     global chosen_date
#     chosen_date = message.text
#     msg = bot.reply_to(message, "Пожалуйста, выберите время приёма:", reply_markup=generate_markup(times))
#     bot.register_next_step_handler(msg, process_time_choice)
#
#
# def process_time_choice(message):
#     global chosen_time
#     chosen_time = message.text
#     confirmation_message = f"Вы записались на прием к {chosen_master} for {chosen_service} on {chosen_date} at {chosen_time}. Правильно ли это? (Да/нет)"
#     msg = bot.reply_to(message, confirmation_message)
#     bot.register_next_step_handler(msg, process_confirmation)
#
#
# def process_confirmation(message):
#     if message.text.lower() == 'Да'or'да':
#         bot.send_message(message.chat.id, "Назначение подтверждено. Спасибо!")
#
#     else:
#         bot.send_message(message.chat.id, "Запись отменена. Пожалуйста, начните сначала, если хотите записаться еще раз.")


if __name__ == "__main__":
    bot.polling(none_stop=True)