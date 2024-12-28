from datetime import datetime, time, timedelta

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from settings import NAME_OF_DB

# Base class for ORM models
Base = declarative_base()


WEEK_DAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


# Таблица TYPE
class Type(Base):
    __tablename__ = 'types'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    centers = relationship('Center', back_populates='type')
    services = relationship('Service', back_populates='type')

    def __repr__(self):
        return f"Тип '{self.name}'"


class City(Base):
    __tablename__ = 'cities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    places = relationship('Place', back_populates='city')
    users = relationship('User', back_populates='city')

    def __repr__(self):
        return f"Город '{self.name}'"


class Service(Base):
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type_id = Column(Integer, ForeignKey('types.id'), nullable=False)

    type = relationship('Type', back_populates='services')
    places = relationship('Place', secondary='service_place', back_populates='services', lazy='dynamic')
    records = relationship('Record', back_populates='service')

    duration = Column(Integer, default=60)

    def get_duration(self):
        return time(hour=self.duration // 60, minute=self.duration % 60)

    def get_duration_str(self):
        # return self.get_duration().strftime("%H:%M (чч:мм)")
        if self.get_duration().hour > 0:
            return self.get_duration().strftime("%H ч %M минут")
        else:
            return self.get_duration().strftime("%M минут")

    def __repr__(self):
        return f"Услуга '{self.name}' длительностью ({self.get_duration_str()}) из салонов: {[place.address for place in self.places]}"


# Таблица CENTERS
class Center(Base):
    __tablename__ = 'centers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type_id = Column(Integer, ForeignKey('types.id'), nullable=False)

    type = relationship('Type', back_populates='centers')
    places = relationship('Place', back_populates='center')

    @staticmethod
    def get_current_type(_type):
        return GET_TYPE(_type)

    @staticmethod
    def get_all_centers_by_type(_type):
        return GET_CENTERS_BY_TYPE(_type)

    @staticmethod
    def get_center(_id):
        return GET_CENTER(_id)

    @staticmethod
    def get_center_with_type(_id, _type):
        return GET_CENTER(_id)

    def __repr__(self):
        return f"Сеть салонов '{self.name}'"


# Таблица PLACES
class Place(Base):
    __tablename__ = 'places'
    id = Column(Integer, primary_key=True, autoincrement=True)
    center_id = Column(Integer, ForeignKey('centers.id'), nullable=False)
    address = Column(String, nullable=False)
    graph_start = Column(Integer, default=8, nullable=False)
    graph_end = Column(Integer, default=18, nullable=False)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    center = relationship('Center', back_populates='places')
    city = relationship('City', back_populates='places')
    records = relationship('Record', back_populates='place')
    owner = relationship('User', back_populates='places')

    services = relationship('Service', secondary='service_place', back_populates='places')

    @staticmethod
    def get_current_type(_type):
        return GET_TYPE(_type)

    @staticmethod
    def get_all_places():
        return GET_PLACES()

    @staticmethod
    def get_all_places_by_center(_center_id):
        return GET_PLACES_BY_CENTER(_center_id)

    @staticmethod
    def get_place(_id):
        return GET_PLACE(_id)

    def __repr__(self):
        return f"Салон '{self.address}' центра '{self.center.name}' с услугами: {self.services}"


# Таблица USERS
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)  # ID задаётся программой
    name = Column(String, nullable=True)
    number = Column(String, nullable=True)
    role = Column(Integer, default=0)  # роли: 0-клиент, 1-мастер салона, 2-менеджер, 3-администратор
    list_of_records = Column(String, nullable=True)  # Хранение как строки ID-шников (JSON)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=True)

    records = relationship('Record', back_populates='user')
    city = relationship('City', back_populates='users')
    places = relationship('Place', back_populates='owner')

    @staticmethod
    def check_user(_id):
        return CHECK_USER(_id)

    @staticmethod
    def check_preuser(_id):
        return CHECK_PREUSER(_id)

    @staticmethod
    def check_prepreuser(_id):
        return CHECK_PREPREUSER(_id)

    @staticmethod
    def get_preuser_name(_id):
        return User.get_preuser(_id).name

    @staticmethod
    def create_prepreuser(_id):
        ADD_PREPREUSER_TO_BD(_id)

    @staticmethod
    def create_preuser(_id, name=None):
        ADD_PREUSER_TO_BD(_id, name=name)

    @staticmethod
    def create_user(_id, number):
        ADD_USER_TO_BD(_id, number)

    @staticmethod
    def get_preuser(_id):
        return GET_USER(_id)

    @staticmethod
    def get_user(_id):
        return GET_USER(_id)

    def get_records(self):
        actual_records = list()
        now = datetime.now()
        for record in self.records:
            if record.start_date > now:
                actual_records.append(record)
        return sorted(actual_records, key=lambda x: x.start_date)

    def get_master_records(self):
        actual_records = list()
        now = datetime.now()
        for cur_place in self.places:
            for record in cur_place.records:
                if record.start_date > now:
                    actual_records.append(record)
        return sorted(actual_records, key=lambda x: x.start_date)

    def __repr__(self):
        return f"Пользователь '{self.name}' с ролью {self.role} из города '{self.city.name}'"


# Таблица RECORDS
class Record(Base):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    place_id = Column(Integer, ForeignKey('places.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    active = Column(Boolean, default=False, nullable=False)

    user = relationship('User', back_populates='records')
    place = relationship('Place', back_populates='records')
    service = relationship('Service', back_populates='records')

    def get_range_of_date(self):
        if self.start_date.date() == self.end_date.date():
            return f"{self.start_date.strftime('%d.%m.%Y %H:%M')}-{self.end_date.strftime('%H:%M')}"
        else:
            return f"{self.start_date.strftime('%d.%m.%Y %H:%M')}-{self.end_date.strftime('%d.%m.%Y %H:%M')}"

    def get_remaining_time(self):
        return self.start_date - datetime.now()

    def get_text_of_remaining_time(self):
        cur_timedelta = self.get_remaining_time()
        if cur_timedelta >= timedelta(days=1):
            return f"{cur_timedelta.days} д {cur_timedelta.seconds // 3600} ч {(cur_timedelta.seconds // 60) % 60} мин"
        elif cur_timedelta >= timedelta(hours=1):
            return f"{cur_timedelta.seconds // 3600} ч {(cur_timedelta.seconds // 60) % 60} мин"
        else:
            return f"{(cur_timedelta.seconds // 60) % 60} мин"

    def is_actual(self):
        return self.start_date < datetime.now()

    def is_soon(self):
        return self.get_remaining_time() < timedelta(days=1)

    def is_very_soon(self):
        return self.get_remaining_time() < timedelta(hours=1)

    def get_text_for_str(self, i):
        if not self.active:
            cur_emoji = "❓"
        elif self.is_very_soon():
            cur_emoji = "🟢"
        elif self.is_soon():
            cur_emoji = "🔴"
        else:
            cur_emoji = "⚪️"
        return f"{cur_emoji} {i + 1}) {self.get_range_of_date()} в салон '{self.service.name}' по адресу: {self.place.address}"

    # TODO: подправить вывод даты в кнопку
    def get_text_for_button(self, i):
        return f"{i + 1}) {self.get_range_of_date()} в '{self.service.name}'"

    def __repr__(self):
        return f"Запись пользователя '{self.user.name}' в салон по адресу '{self.place.address}' на {self.start_date}"


class ServicePlace(Base):
    __tablename__ = 'service_place'

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    place_id = Column(Integer, ForeignKey('places.id'), nullable=False)

    def get_next_days(self, days=9):
        now = datetime.now()
        if now.hour >= GET_PLACE(self.place_id).graph_end:
            now += timedelta(days=1)
        today = now.date()
        next_days = list()
        for i in range(days):
            cur_day = today + timedelta(days=i)
            cur_week = WEEK_DAYS[int(cur_day.strftime("%w"))]
            next_days.append((f"{cur_day.strftime('%d.%m')} | {cur_week}",
                              f"{cur_day.strftime('%d/%m/%Y')}"))
        return next_days

    def get_next_times(self, date):
        cur_time = datetime(date.year, date.month, date.day, GET_PLACE(self.place_id).graph_start)
        service_duration = timedelta(minutes=GET_SERVICE(self.service_id).duration)
        end_time = datetime(date.year, date.month, date.day, GET_PLACE(self.place_id).graph_end, 1) - service_duration
        now = datetime.now()
        next_times = list()
        while cur_time < end_time:
            if cur_time > now and GET_RECORD_IS_ARMORED(self.place_id, self.service_id, cur_time):
                cur_end_time = cur_time + service_duration
                next_times.append((f"{cur_time.strftime('%H:%M')} - {cur_end_time.strftime('%H:%M')}",
                                  f"{cur_time.strftime('%d/%m/%Y/%H/%M')}"))
            cur_time += service_duration
        return next_times


# Инициализация базы данных
def init_db(database_url=f'sqlite:///{NAME_OF_DB}'):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


# CRUD методы
class DatabaseService:
    def __init__(self, session):
        self.session = session

    def commit(self):
        self.session.commit()

    def add(self, obj):
        self.session.add(obj)
        self.session.commit()

    def get(self, model, obj_id):
        return self.session.query(model).filter_by(id=obj_id).first()

    def get_by_key(self, model, key, value):
        return self.session.query(model).filter(key==value).first()

    def update(self, model, obj_id, **kwargs):
        obj = self.session.query(model).filter_by(id=obj_id).first()
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            self.session.commit()
        return obj

    def delete(self, model, obj_id):
        obj = self.session.query(model).filter_by(id=obj_id).first()
        if obj:
            self.session.delete(obj)
            self.session.commit()
        return obj

    def list(self, model):
        return self.session.query(model).all()

    def list_with_filter(self, model, key, value):
        return self.session.query(model).filter(key==value).all()

    def only_filter(self, key, value, model=None, query=None):
        if model:
            return self.session.query(model).filter(key==value)
        if query:
            return query.filter(key==value)


# Инициализация базы данных
Session = init_db()
cur_session = Session()
db_service = DatabaseService(cur_session)


def SET_USER_CITY(_id, city_id):
    user = db_service.get(User, _id)
    if user:
        db_service.update(User, _id, city_id=city_id)


def ADD_USER_TO_BD(_id, number):
    user = db_service.get(User, _id)
    if user:
        db_service.update(User, _id, number=number)


def ADD_PREUSER_TO_BD(_id, name=None):
    user = db_service.get(User, _id)
    if user:
        db_service.update(User, _id, name=name, number=None)


def ADD_PREPREUSER_TO_BD(_id):
    user = db_service.get(User, _id)
    if not user:
        user = User(id=_id, name=None, number=None, list_of_records='[]')
        db_service.add(user)


def GET_USER(_id):
    return db_service.get(User, _id)


def CHECK_PREPREUSER(_id):
    now_user = db_service.get(User, _id)
    if now_user:
        if now_user.name is None and now_user.number is None:
            return True
    return False


def CHECK_PREUSER(_id):
    now_user = db_service.get(User, _id)
    if now_user:
        if now_user.name is not None and now_user.number is None:
            return True
    return False


def CHECK_USER(_id):
    now_user = db_service.get(User, _id)
    if now_user:
        if now_user.name is not None and now_user.number is not None:
            return True
    return False


def GET_TYPE(type_name):
    return db_service.get_by_key(Type, Type.name, type_name).id


def GET_TYPES():
    return db_service.list(Type)


def GET_CITY(city_name):
    return db_service.get_by_key(City, City.name, city_name).id


def GET_CITY_OBJECT(_id):
    return db_service.get(City, _id)


def GET_CITIES():
    return db_service.list(City)


def GET_SERVICES_BY_TYPE(_type):
    # return db_service.list_with_filter(Center, Center.type_id, GET_TYPE(_type))
    return db_service.get(Type, _type).services


def GET_SERVICES_BY_PLACE(_place_id):
    # return db_service.list_with_filter(Center, Center.type_id, GET_TYPE(_type))
    return db_service.get(Place, _place_id).services


def GET_SERVICES_BY_TYPE_AND_CITY(_type, city):
    result = list()
    for cur_service in GET_SERVICES_BY_TYPE(_type):
        for place_of_cur_center in cur_service.places:
            if place_of_cur_center.city == city:
                break
        else:
            continue
        result.append(cur_service)
    return result


def GET_SERVICE(_id):
    return db_service.get(Service, _id)


def GET_CENTERS_BY_TYPE(_type):
    # return db_service.list_with_filter(Center, Center.type_id, GET_TYPE(_type))
    return db_service.get(Type, _type).centers


def GET_CENTERS_BY_TYPE_AND_CITY(_type, city):
    result = list()
    for cur_center in GET_CENTERS_BY_TYPE(_type):
        for place_of_cur_center in cur_center.places:
            if place_of_cur_center.city == city:
                break
        else:
            continue
        result.append(cur_center)
    return result


def GET_CENTER(_id):
    return db_service.get(Center, _id)


def GET_PLACES_BY_CENTER(_center_id):
    return db_service.list_with_filter(Place, Place.center_id, _center_id)


def GET_PLACES_BY_CENTER_AND_CITY(_center_id, city):
    return db_service.only_filter(Place.city, city,
                                  query=db_service.only_filter(Place.center_id, _center_id, model=Place))


def GET_PLACES_BY_SERVICE_AND_CITY(_service_id, city):
    return db_service.only_filter(Place.city, city,
                                  query=GET_SERVICE(_service_id).places)


def GET_PLACES():
    return db_service.list(Place)


def GET_PLACE(_id):
    return db_service.get(Place, _id)


def GET_SERVICE_PLACE(_place_id, _service_id):
    return db_service.only_filter(ServicePlace.service_id, _service_id,
                                  query=db_service.only_filter(ServicePlace.place_id, _place_id, model=ServicePlace)).one()


def ADD_RECORD(_user_id, _place_id, _service_id, _start_date):
    cur_record = Record(user_id=_user_id, place_id=_place_id, service_id=_service_id,
                        start_date=_start_date,
                        end_date=_start_date + timedelta(minutes=GET_SERVICE(_service_id).duration))
    db_service.add(cur_record)
    return cur_record.id


def ACTIVATE_RECORD(_record_id):
    db_service.update(Record, _record_id, active=True)


def DELETE_RECORD(_record_id):
    db_service.delete(Record, _record_id)


def GET_RECORD(_id):
    return db_service.get(Record, _id)


def GET_RECORD_IS_ARMORED(_place_id, _service_id, _start_date):
    return db_service.only_filter(Record.service_id, _service_id,
                                  query=db_service.only_filter(Record.place_id, _place_id,
                                                               query=db_service.only_filter(Record.start_date, _start_date,
                                                                                            model=Record))).count() > 0


# Пример использования
if __name__ == '__main__':
    # Пример добавления типов
    type1 = Type(name='🧔 Барбершоп')
    type2 = Type(name='💇 Парикмахерская')
    type3 = Type(name='💅 Маникюр')
    db_service.add(type1)
    db_service.add(type2)
    db_service.add(type3)

    # Пример добавления городов
    city1 = City(name='Казань')
    city2 = City(name='Москва')
    city3 = City(name='Санкт-Петербург')
    db_service.add(city1)
    db_service.add(city2)
    db_service.add(city3)

    user2 = User(id=955999723, name='Арслан', number='79999999999', role=3, city_id=city1.id, list_of_records='[]')
    user1 = User(id=5112141963, name='Фархад', number='79999999998', role=3, city_id=city2.id, list_of_records='[]')
    db_service.add(user1)
    db_service.add(user2)

    # Пример добавления центра с типом
    center1 = Center(name='Бороды по колено', type_id=1)
    center2 = Center(name='Бритый пупочек', type_id=1)
    center3 = Center(name='Электромагнит у дома', type_id=1)
    db_service.add(center1)
    db_service.add(center2)
    db_service.add(center3)

    service1 = Service(name='Особенные усы', type=type1, duration=40)
    service2 = Service(name='Мощнейшие бакенбарды', type=type1, duration=30)
    service3 = Service(name='Дизайнерская борода', type=type1)
    db_service.add(service1)
    db_service.add(service2)
    db_service.add(service3)

    place1 = Place(center_id=1, address='ул. Чистопольская, дом 72', city_id=city1.id, owner_id=user1.id, services=[service1, service2])
    place2 = Place(center_id=2, address='ул. Кремлёвская, дом 13', city_id=city1.id, owner_id=user1.id, services=[service2])
    place3 = Place(center_id=2, address='ул. Кремлёвская, дом 102', city_id=city2.id, owner_id=user1.id, services=[service1, service2, service3])
    place4 = Place(center_id=2, address='ул. Баумана, дом 25', city_id=city1.id, owner_id=user1.id, services=[service1])
    db_service.add(place1)
    db_service.add(place2)
    db_service.add(place3)
    db_service.add(place4)

    # Пример добавления центра с типом
    center1 = Center(name='МАРИЯ', type_id=2)
    center2 = Center(name='Парикмахерская', type_id=2)
    db_service.add(center1)
    db_service.add(center2)

    service1 = Service(name='Красивая стрижка', type=type2, duration=90)
    service2 = Service(name='Короткая стрижка', type=type2, duration=25)
    service3 = Service(name='Под нолик "Пора в армию"', type=type2, duration=15)
    db_service.add(service1)
    db_service.add(service2)
    db_service.add(service3)

    place1 = Place(center_id=center1.id, address='ул. Детройтовская, дом 14', city_id=city1.id, owner_id=user1.id, services=[service1, service2, service3])
    place2 = Place(center_id=center1.id, address='ул. Великолепная, дом 69', city_id=city1.id, owner_id=user1.id, services=[service1, service2, service3])
    place3 = Place(center_id=center2.id, address='ул. Обычная, дом 33', city_id=city1.id, owner_id=user1.id, services=[service3])
    db_service.add(place1)
    db_service.add(place2)
    db_service.add(place3)


    # Пример добавления центра с типом
    center1 = Center(name='Маник и педик быстро и недорого', type_id=3)
    center2 = Center(name='Иванова Ивана Ивановна', type_id=3)
    db_service.add(center1)
    db_service.add(center2)

    service1 = Service(name='Нюд', type=type3, duration=120)
    service2 = Service(name='Красный маник', type=type3)
    db_service.add(service1)
    db_service.add(service2)

    place1 = Place(center_id=center1.id, address='ул. Суперская, дом 3/В', city_id=city1.id, owner_id=user1.id, services=[service1, service2])
    place2 = Place(center_id=center1.id, address='ул. Запрещённая, дом 228', city_id=city1.id, owner_id=user1.id, services=[service1])
    place3 = Place(center_id=center1.id, address='ул. Сколько лет КФУ, дом 220', city_id=city1.id, owner_id=user1.id, services=[service2])
    place4 = Place(center_id=center2.id, address='ул. Декабристов, дом 47', city_id=city1.id, owner_id=user1.id, services=[service1])
    db_service.add(place1)
    db_service.add(place2)
    db_service.add(place3)
    db_service.add(place4)

    # record0 = Record(user_id=user2.id, place_id=place3.id, service=service2, start_date=datetime(2024, 12, 26, 23),
    #                  end_date=datetime(2024, 12, 27, 0))
    # record1 = Record(user_id=user2.id, place_id=place3.id, service=service2, start_date=datetime(2025, 1, 6, 14),
    #                  end_date=datetime(2025, 1, 6, 15))
    # record2 = Record(user_id=user2.id, place_id=place1.id, service=service1, start_date=datetime(2024, 11, 29, 12),
    #                  end_date=datetime(2024, 11, 29, 14))
    # record3 = Record(user_id=user2.id, place_id=place4.id, service=service1, start_date=datetime(2024, 12, 31, 23, 50),
    #                  end_date=datetime(2025, 1, 1, 1, 50))
    # record4 = Record(user_id=user2.id, place_id=place2.id, service=service1, start_date=datetime(2024, 12, 26, 15, 50),
    #                  end_date=datetime(2024, 12, 26, 17, 50))
    # db_service.add(record0)
    # db_service.add(record1)
    # db_service.add(record2)
    # db_service.add(record3)
    # db_service.add(record4)

    print('All Types:', db_service.list(Type))
    print('All Services:', db_service.list(Service))
    print('All Centers:', db_service.list(Center))
    print('All Places:', db_service.list(Place))
    print('All Users:', db_service.list(User))
    print('All Records:', db_service.list(Record))
