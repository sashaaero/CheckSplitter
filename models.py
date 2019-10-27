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
    mastered_credits = Set('Credit', reverse='master')
    slaved_credits = Set('Credit', reverse='slave')
    sessions = Set('UserInSession')
    credit_editions = Set('CreditEdition', reverse='user')
    affected_editions = Set('CreditEdition', reverse='affected_user')

    @property
    def virtual(self):
        return self.password is 'None'

    def is_authenticated(self):
        return True

    @property
    def current_session(self):
        return select(s.session for s in self.sessions if s.session.end is None).first()


class Session(db.Entity):
    id = PrimaryKey(int, auto=True)
    title = Optional(str)
    orders = Set('OrderedItem')
    users = Set('UserInSession')
    start = Optional(datetime)
    end = Optional(datetime)


class OrderedItem(db.Entity):
    id = PrimaryKey(int, auto=True)
    title = Required(str)
    price = Required(int)
    session = Required(Session)
    user_in_sessions = Set('UserInSession')


class Credit(db.Entity):
    id = PrimaryKey(int, auto=True)
    master = Required(User, reverse='mastered_credits')
    slave = Required(User, reverse='slaved_credits')
    value = Optional(int)
    credit_editions = Set('CreditEdition')


class UserInSession(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    value = Required(int, default=0)
    session = Required(Session)
    orders = Set(OrderedItem)


class CreditEdition(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User, reverse='credit_editions')
    credit = Required(Credit)
    old_value = Required(int)
    new_value = Required(int)
    affected_user = Required(User, reverse='affected_editions')
