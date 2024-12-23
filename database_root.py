from datetime import datetime, time

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from settings import NAME_OF_DB

# Base class for ORM models
Base = declarative_base()


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
    places = relationship('Place', secondary='service_place', back_populates='services')
    records = relationship('Record', back_populates='service')

    duration = Column(Integer, default=60)

    def get_duration(self):
        return time(hour=self.duration // 60, minute=self.duration % 60)

    def get_duration_str(self):
        return self.get_duration().strftime("%H:%M (чч:мм)")
        # if self.get_duration().hour > 0:
        #     return self.get_duration().strftime("%Hч %Mмин")
        # else:
        #     return self.get_duration().strftime("%Mм")

    def __repr__(self):
        return f"Услуга '{self.name}' длительностью {self.get_duration_str()} из салонов: {[place.address for place in self.places]}"


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
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    center = relationship('Center', back_populates='places')
    city = relationship('City', back_populates='places')
    records = relationship('Record', back_populates='place')
    owner = relationship('User', back_populates='place')

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
    list_of_records = Column(String, nullable=True)  # Хранение как строки ID-шников (JSON)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=True)

    records = relationship('Record', back_populates='user')
    city = relationship('City', back_populates='users')
    place = relationship('Place', back_populates='owner')

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

    def __repr__(self):
        return f"Пользователь '{self.name}' из города '{self.city.name}'"


# Таблица RECORDS
class Record(Base):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    place_id = Column(Integer, ForeignKey('places.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    user = relationship('User', back_populates='records')
    place = relationship('Place', back_populates='records')
    service = relationship('Service', back_populates='records')

    def __repr__(self):
        return f"Запись пользователя '{self.user.name}' в салон по адресу '{self.place.address}' на {self.start_date}"


class ServicePlace(Base):
    __tablename__ = 'service_place'

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    place_id = Column(Integer, ForeignKey('places.id'), nullable=False)


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


def GET_PLACES():
    return db_service.list(Place)


def GET_PLACE(_id):
    return db_service.get(Place, _id)


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

    user = User(id=955999723, name='Арслан', number='79999999999', city_id=city1.id, list_of_records='[]')
    db_service.add(user)

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

    place1 = Place(center_id=1, address='ул. Чистопольская, дом 72', city_id=city1.id, owner_id=user.id, services=[service1, service2])
    place2 = Place(center_id=2, address='ул. Кремлёвская, дом 13', city_id=city1.id, owner_id=user.id, services=[service2])
    place3 = Place(center_id=2, address='ул. Кремлёвская, дом 102', city_id=city2.id, owner_id=user.id, services=[service1, service2, service3])
    place4 = Place(center_id=2, address='ул. Баумана, дом 25', city_id=city1.id, owner_id=user.id, services=[service1])
    db_service.add(place1)
    db_service.add(place2)
    db_service.add(place3)
    db_service.add(place4)

    # Пример добавления центра с типом
    center1 = Center(name='УФФ МАРИЯ', type_id=2)
    center2 = Center(name='Парикмахерская', type_id=2)
    db_service.add(center1)
    db_service.add(center2)

    service1 = Service(name='Красивая стрижка', type=type2, duration=90)
    service2 = Service(name='Короткая стрижка', type=type2, duration=25)
    service3 = Service(name='Под нолик "Пора в армию"', type=type2, duration=15)
    db_service.add(service1)
    db_service.add(service2)
    db_service.add(service3)

    place1 = Place(center_id=center1.id, address='ул. Петровская, дом 14', city_id=city1.id, owner_id=user.id, services=[service1, service2, service3])
    place2 = Place(center_id=center1.id, address='ул. Сексуальная, дом 69', city_id=city1.id, owner_id=user.id, services=[service1, service2, service3])
    place3 = Place(center_id=center2.id, address='ул. Обычная, дом 33', city_id=city1.id, owner_id=user.id, services=[service3])
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

    place1 = Place(center_id=center1.id, address='ул. Суперская, дом 3/В', city_id=city1.id, owner_id=user.id, services=[service1, service2])
    place2 = Place(center_id=center1.id, address='ул. Запрещённая, дом 228', city_id=city1.id, owner_id=user.id, services=[service1])
    place3 = Place(center_id=center1.id, address='ул. Сколько лет КФУ, дом 220', city_id=city1.id, owner_id=user.id, services=[service2])
    place4 = Place(center_id=center2.id, address='ул. Декабристов, дом 47', city_id=city1.id, owner_id=user.id, services=[service1])
    db_service.add(place1)
    db_service.add(place2)
    db_service.add(place3)
    db_service.add(place4)

    record = Record(user_id=user.id, place_id=place3.id, service=service2, start_date=datetime(2024, 11, 29, 12),
                    end_date=datetime(2024, 11, 29, 13))
    db_service.add(record)

    print('All Types:', db_service.list(Type))
    print('All Services:', db_service.list(Service))
    print('All Centers:', db_service.list(Center))
    print('All Places:', db_service.list(Place))
    print('All Users:', db_service.list(User))
    print('All Records:', db_service.list(Record))
