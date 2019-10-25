from wtforms import *
from wtforms.validators import *
from models import *
from werkzeug.security import check_password_hash


def nickname_free(form, field):
    nickname = field.data
    check = User.get(nickname=nickname)
    if check is not None:
        raise ValidationError('Никнейм %r занят' % nickname)


def len_check(form, field):
    pwd = field.data
    if len(pwd) < 5:
        raise ValidationError('Пароль слишком короткий, используйте 5 или более символов')


def pwd_check(form, field):
    pwd2 = field.data
    pwd1 = form.pwd1.data
    if pwd1 != pwd2:
        raise ValidationError('Пароли должны совпадать')


def nickname_check(form, field):
    nickname = field.data
    check = User.get(nickname=nickname)
    if check is None:
        raise ValidationError('Пользователь с никнеймом %r не найден' % nickname)


def pwd_match_check(form, field):
    nickname = form.nickname.data
    pwd = field.data
    user = User.get(nickname=nickname)
    if user:
        if not check_password_hash(user.password, pwd):
            raise ValidationError('Неверный пароль')


def check_credit_form(form, field):
    from re import search
    number = field.data
    if search('^[0-9]{1,5}$', number) is None:
        raise ValidationError('Введите корректную сумму.')

class RegForm(Form):
    nickname = StringField('Никнейм', [InputRequired(), nickname_free])
    fullname = StringField('Полное имя', [InputRequired()])
    pwd1 = PasswordField('Пароль', [InputRequired(), len_check])
    pwd2 = PasswordField('Повторите пароль', [InputRequired(), pwd_check])


class VirtualRegForm(Form):
    nickname = StringField('Никнейм', [InputRequired(), nickname_free])
    fullname = StringField('Полное имя', [InputRequired()])


class LoginForm(Form):
    nickname = StringField('Никнейм', [InputRequired(), nickname_check])
    pwd = PasswordField('Пароль', [InputRequired(), pwd_match_check])


class OrderItem(Form):
    title = StringField('Название блюда', [InputRequired()])
    price = StringField('Цена', [InputRequired()])
    users = StringField('Кто заказал')
    session = StringField('Ресторан')


class CreditForm(Form):
    value = StringField('Сумма', [InputRequired(), check_credit_form])
