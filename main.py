import datetime

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


def generate_markup(items, cur_row_width=1):
    markup = types.InlineKeyboardMarkup(row_width=cur_row_width)
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
        elif section == "start_record_by_place_and_service":
            start_record_by_place_and_service(call.message, args[0])
        elif section == "start_record_by_center":
            start_record_by_center(call.message, args[0])
        elif section == "start_record_by_place":
            start_record_by_place(call.message, args[0])
        elif section == "start_record":
            start_record(call.message, args[0])
        elif section == "start_record_by_service_and_place":
            start_record_by_service_and_place(call.message, args[0])
        elif section == "start_record_with_service":
            start_record_with_service(call.message, args[0], args[1])
        elif section == "start_record_by_date":
            start_record_by_date(call.message, args[0], args[1])
        elif section == "start_record_by_time":
            start_record_by_time(call.message, args[0], args[1], args[2])
        elif section == "start_confirm_record":
            start_confirm_record(call.message, args[0], args[1], args[2])
        elif section == "confirm_record":
            confirm_record(call.message, args[0], args[1], args[2])
        elif section == "confirm_record_from_master":
            confirm_record_from_master(call.message, args[0])
        elif section == "cancel_record_from_master":
            cancel_record_from_master(call.message, args[0])
        elif section == "show_records":
            show_records(call.message)
        elif section == "show_record":
            show_record(call.message, args[0])
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
    cur_services = list()
    for cur_service in GET_SERVICES_BY_TYPE_AND_CITY(type_id, get_user(message).city):
        cur_services.append((f"{cur_service.name} ({cur_service.get_duration_str()})", f"start_record_by_place_and_service.{cur_service.id}"))
    cur_services.append((MAIN_MENU_BUTTON_TEXT, "main_menu"))
    markup = generate_markup(cur_services)

    bot.send_message(message.chat.id, f"Выберите услугу, на которую вы хотите записаться:",
                     reply_markup=markup)


def start_record_by_place_and_service(message, service_id):
    cur_places = list()
    for cur_place in GET_PLACES_BY_SERVICE_AND_CITY(service_id, get_user(message).city):
        cur_places.append((cur_place.address, f"start_record_with_service.{cur_place.id}.{service_id}"))
    cur_places.append((f"⬅️ Вернуться к выбору услуг", f"start_record_by_service.{GET_SERVICE(service_id).type_id}"))
    cur_places.append((MAIN_MENU_BUTTON_TEXT, "main_menu"))
    markup = generate_markup(cur_places)

    bot.send_message(message.chat.id, f"Выберите салон, в который вы хотите записаться на услугу {GET_SERVICE(service_id).name}:",
                     reply_markup=markup)


def start_record_by_center(message, type_id):
    cur_centers = list()
    for cur_center in GET_CENTERS_BY_TYPE_AND_CITY(type_id, get_user(message).city):
        cur_centers.append((cur_center.name, f"start_record_by_place.{cur_center.id}"))
    cur_centers.append((MAIN_MENU_BUTTON_TEXT, "main_menu"))
    markup = generate_markup(cur_centers)

    bot.send_message(message.chat.id, f"Выберите сеть салонов, в который вы хотите записаться:",
                     reply_markup=markup)


def start_record_by_place(message, center_id):
    cur_places = list()
    for cur_place in GET_PLACES_BY_CENTER_AND_CITY(center_id, get_user(message).city):
        cur_places.append((cur_place.address, f"start_record.{cur_place.id}"))
    cur_places.append((f"⬅️ Вернуться к выбору сети салонов", f"start_record_by_center.{GET_CENTER(center_id).type_id}"))
    cur_places.append((MAIN_MENU_BUTTON_TEXT, "main_menu"))
    markup = generate_markup(cur_places)

    bot.send_message(message.chat.id, f"Выберите салон сети {GET_CENTER(center_id).name}, в который вы хотите записаться:",
                     reply_markup=markup)


def start_record(message, place_id):
    place = GET_PLACE(place_id)
    markup = generate_markup([(f"🎫 Выбрать услугу", f"start_record_by_service_and_place.{place_id}"),
                              (f"⬅️ Вернуться к выбору услуг или сети салонов", f"start_record_by_type_of_service.{place.center.type_id}"),
                              (MAIN_MENU_BUTTON_TEXT, "main_menu")])

    bot.send_message(message.chat.id, f"Сейчас вы планируете запись в '{place.center.name}' по адресу: {place.address}",
                     reply_markup=markup)


def start_record_by_service_and_place(message, place_id):
    cur_services = list()
    for cur_service in GET_SERVICES_BY_PLACE(place_id):
        cur_services.append((f"{cur_service.name} ({cur_service.get_duration_str()})", f"start_record_with_service.{place_id}.{cur_service.id}"))
    cur_services.append((MAIN_MENU_BUTTON_TEXT, "main_menu"))
    markup = generate_markup(cur_services)

    bot.send_message(message.chat.id, f"Выберите услугу, на которую вы хотите записаться:",
                     reply_markup=markup)


def start_record_with_service(message, place_id, service_id):
    place = GET_PLACE(place_id)
    service = GET_SERVICE(service_id)
    markup = generate_markup([(f"📅 Выбрать дату и время записи", f"start_record_by_date.{place_id}.{service_id}"),
                              (f"⬅️ Вернуться к выбору услуг или сети салонов", f"start_record_by_type_of_service.{place.center.type_id}"),
                              (MAIN_MENU_BUTTON_TEXT, "main_menu")])

    bot.send_message(message.chat.id, f"Сейчас вы планируете запись на услугу '{service.name}' "
                                      f"в '{place.center.name}' по адресу: {place.address}",
                     reply_markup=markup)


# TODO: доделать запись по дате и времени через datetime, запись в БД, отсылку салону о новой записи
def start_record_by_date(message, place_id, service_id):
    cur_days = list()
    for cur_day_button, cur_day_tag in GET_SERVICE_PLACE(place_id, service_id).get_next_days():
        cur_days.append((cur_day_button, f"start_record_by_time.{place_id}.{service_id}.{cur_day_tag}"))
    cur_days.append(
        (f"⬅️ Вернуться к выбору услуг или сети салонов", f"start_record_by_type_of_service.{GET_SERVICE(service_id).type_id}"))
    cur_days.append((MAIN_MENU_BUTTON_TEXT, "main_menu"))
    markup = generate_markup(cur_days)

    bot.send_message(message.chat.id,
                     f"Выберите дату, на которую вы хотите записаться:",
                     reply_markup=markup)


def start_record_by_time(message, place_id, service_id, date):
    cur_date = datetime.strptime(date, "%d/%m/%Y")
    cur_times = list()
    for cur_time_button, cur_time_tag in GET_SERVICE_PLACE(place_id, service_id).get_next_times(cur_date):
        cur_times.append((cur_time_button, f"start_confirm_record.{place_id}.{service_id}.{cur_time_tag}"))
    cur_times.append(
        (f"⬅️ Вернуться к выбору даты", f"start_record_by_date.{place_id}.{service_id}"))
    cur_times.append((MAIN_MENU_BUTTON_TEXT, "main_menu"))
    markup = generate_markup(cur_times)

    bot.send_message(message.chat.id,
                     f"Выберите время, на которое вы хотите записаться:",
                     reply_markup=markup)


def start_confirm_record(message, place_id, service_id, date_and_time):
    cur_date_and_time = datetime.strptime(date_and_time, "%d/%m/%Y/%H/%M")
    cur_times = [
        (f"✅ Подтвердить запись", f"confirm_record.{place_id}.{service_id}.{date_and_time}"),
        (f"⬅️ Вернуться к выбору времени", f"start_record_by_time.{place_id}.{service_id}.{cur_date_and_time.strftime('%d/%m/%Y')}"),
        (f"⬅️ Вернуться к выбору даты", f"start_record_by_date.{place_id}.{service_id}"),
        (MAIN_MENU_BUTTON_TEXT, "main_menu")
    ]
    markup = generate_markup(cur_times)

    service = GET_SERVICE(service_id)
    place = GET_PLACE(place_id)
    cur_end_date_and_time = cur_date_and_time + timedelta(minutes=service.duration)
    bot.send_message(message.chat.id,
                     f"Сейчас вы планируете запись на {cur_date_and_time.strftime('%d.%m.%Y')} "
                     f"с {cur_date_and_time.strftime('%H:%M')} до {cur_end_date_and_time.strftime('%H:%M')} "
                     f"на услугу '{service.name}' "
                     f"в '{place.center.name}' "
                     f"по адресу: {place.address}",
                     reply_markup=markup)


def confirm_record(message, place_id, service_id, date_and_time):
    cur_date_and_time = datetime.strptime(date_and_time, "%d/%m/%Y/%H/%M")

    cur_record_id = ADD_RECORD(get_user(message).id, place_id, service_id, _start_date=cur_date_and_time)
    send_record_to_master(cur_record_id)

    show_record(message, cur_record_id)


def show_records(message):
    cur_records = list()
    cur_records_str = list()
    for i, cur_record in enumerate(sorted(get_user(message).get_records(), key=lambda x: x.start_date)):
        cur_records_str.append(cur_record.get_text_for_str(i))
        cur_records.append((cur_record.get_text_for_button(i), f"show_record.{cur_record.id}"))
    cur_records.append((MAIN_MENU_BUTTON_TEXT, "main_menu"))
    markup = generate_markup(cur_records)

    cur_records_str = '\n\n'.join(cur_records_str)
    bot.send_message(message.chat.id, f"Выберите запись, которую вы хотите посмотреть:\n\n"
                                      f"{cur_records_str}\n\n"
                                      f"❓ (неподтвержденные записи)\n"
                                      f"⚪️ (подтвержденные записи)\n"
                                      f"🟢 (до записи осталось меньше часа)\n"
                                      f"🔴 (до записи осталось меньше суток)\n\n"
                                      f"Нажмите нужную кнопку снизу, чтобы выбрать запись",
                     reply_markup=markup)


# TODO: добавить кнопки для удаления записи,
#  для подтверждения записи (за сутки до начала записи появляется возможность нажать кнопку, которая подтверждает, что пользователь придет)
def show_record(message, record_id):
    record = GET_RECORD(record_id)

    if record is None:
        markup = generate_markup([(f"📔 Остальные мои записи", f"show_records"),
                                  (MAIN_MENU_BUTTON_TEXT, "main_menu")])

        bot.send_message(message.chat.id, f"Салон отклонил данную запись, но вы можете посмотреть остальные",
                         reply_markup=markup)
        return

    if record.get_remaining_time() > timedelta():
        markup = generate_markup([(f"🔄 Обновить информацию", f"show_record.{record_id}"),
                                  (f"⬅️ Вернуться к списку моих записей", f"show_records"),
                                  (MAIN_MENU_BUTTON_TEXT, "main_menu")])

        if record.active:
            is_active = "уже подтверждена салоном"
        else:
            is_active = "ещё не подтверждена салоном"
        bot.send_message(message.chat.id, f"Ваша запись {is_active}:\n\n"
                                          f"Салон: {record.service.name}\n"
                                          f"Адрес: {record.place.address}\n"
                                          f"Начало: {record.start_date.strftime('%d.%m.%Y %H:%M')}\n"
                                          f"Конец: {record.end_date.strftime('%d.%m.%Y %H:%M')}\n"
                                          f"До начала записи осталось {record.get_text_of_remaining_time()}",
                         reply_markup=markup)
    else:
        markup = generate_markup([(f"📔 Остальные мои записи", f"show_records"),
                                  (MAIN_MENU_BUTTON_TEXT, "main_menu")])

        bot.send_message(message.chat.id, f"Эта запись уже не актуальна, но вы можете посмотреть остальные",
                         reply_markup=markup)


def send_record_to_master(record_id, first=True):
    record = GET_RECORD(record_id)

    if record.active:
        is_active = "уже подтверждена салоном"
        markup = generate_markup([(f"📔 Показать остальные записи в салон", f"show_master_records"),
                                  (MAIN_MENU_BUTTON_TEXT, "main_menu")])
    else:
        is_active = "ещё не подтверждена салоном"
        markup = generate_markup([(f"✅ Подтвердить запись", f"confirm_record_from_master.{record_id}"),
                                  (f"❌ Отклонить запись", f"cancel_record_from_master.{record_id}"),
                                  (f"📔 Показать остальные записи в салон", f"show_master_records"),
                                  (MAIN_MENU_BUTTON_TEXT, "main_menu")])
    if first:
        start_text = "К вам записались"
    else:
        start_text = "Напоминаем о записи"
    bot.send_message(record.place.owner_id, f"{start_text}\n\n"
                                      f"Запись {is_active}\n"
                                      f"Клиент: {record.user.name} (номер: {record.user.number})\n"
                                      f"Салон: {record.service.name}\n"
                                      f"Адрес: {record.place.address}\n"
                                      f"Начало: {record.start_date.strftime('%d.%m.%Y %H:%M')}\n"
                                      f"Конец: {record.end_date.strftime('%d.%m.%Y %H:%M')}\n"
                                      f"До начала записи осталось {record.get_text_of_remaining_time()}",
                     reply_markup=markup)


def confirm_record_from_master(message, record_id):
    ACTIVATE_RECORD(record_id)
    main_menu(message)


def cancel_record_from_master(message, record_id):
    DELETE_RECORD(record_id)
    main_menu(message)


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


if __name__ == "__main__":
    bot.polling(none_stop=True)