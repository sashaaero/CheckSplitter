from datetime import datetime
from pony.orm import *
from config import settings
from flask_login import UserMixin


db = Database(**settings['db_params'])

class User(db.Entity, UserMixin):
    id = PrimaryKey(int, auto=True)
    fullname = Optional(str)
    password = Required(str)
    nickname = Optional(str)
    sessions = Set('Session')
    orders = Set('OrderedItem')
    mastered_credits = Set('Credit', reverse='master')
    slaved_credits = Set('Credit', reverse='slave')
    session_maintains = Set('SessionMaintain')


    @property
    def virtual(self):
        return self.password is None

    def is_authenticated(self):
        return True


class Session(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    users = Set(User)
    orders = Set('OrderedItem')
    session_maintains = Set('SessionMaintain')
    start = Optional(datetime)
    end = Optional(datetime)


class OrderedItem(db.Entity):
    id = PrimaryKey(int, auto=True)
    title = Required(str)
    price = Required(int)
    session = Required(Session)
    users = Set(User)


class Credit(db.Entity):
    id = PrimaryKey(int, auto=True)
    master = Required(User, reverse='mastered_credits')
    slave = Required(User, reverse='slaved_credits')
    value = Optional(int)


class SessionMaintain(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    value = Required(int,default=0)
    session = Required(Session)

