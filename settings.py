from random import choice

APP_NAME = "Твой Beauty Planner"
START_TEXT = f"Добро пожаловать в {APP_NAME}!"
CONTINUE_TEXT = f"На связи {APP_NAME}!"
NAME_OF_DB = "/data/test_db__v0_2.db"

MAIN_MENU_SECTION_TEXT_LIST = ["Вы прекрасны!",
                               "Рады вас здесь видеть!",
                               "Какой хороший день для записи!",
                               "Как насчёт чего-то нового в вашем и без того прекрасном образе?",
                               "А может постричься... Надо обязательно обдумать этот вариант!",
                               "Ух ты, а вот и вы здесь!"]
MAIN_MENU_BUTTON_TEXT = "⬅️ Вернуться на главную"


def MAIN_MENU_SECTION_TEXT():
    return choice(MAIN_MENU_SECTION_TEXT_LIST)
