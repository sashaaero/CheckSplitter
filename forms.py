from wtforms import *
from wtforms.validators import *
from models import *


def nickname_free(form, field):
	nickname = field.data
	check = User.get(nickname=nickname)
	if check is not None:
		raise ValidationError('Nickname %r is already taken' % nickname)


def len_check(form, field):
	pwd = field.data
	if len(pwd) < 5:
		raise ValidationError('Your password is too short, use 5 or more characters')

		
def pwd_check(form, field):
	pwd2 = field.data
	pwd1 = form.pwd1.data
	if pwd1 != pwd2:
		raise ValidationError('Passwords should match')

		
def nickname_check(form, field):
	nickname = field.data
	check = User.get(nickname=nickname)
	if check is None:
		raise ValidationError('User with nickname %r not found' % nickname)

		
def pwd_match_check(form, field):
	nickname = form.nickname.data
	pwd = field.data
	check = User.get(nickname=nickname, password=pwd)
	user = User.get(nickname=form.data['nickname'])
	if check is None:	
		raise ValidationError('Wrong password. Try again. password')
		

class RegForm(Form):
	nickname = StringField('Nickname', [InputRequired(), nickname_free])
	fullname = StringField('Fullname', [InputRequired()])
	pwd1 = PasswordField('Password', [InputRequired(), len_check])
	pwd2 = PasswordField('Password again', [InputRequired(), pwd_check])


class LoginForm(Form):
	nickname = StringField('Nickname', [InputRequired(), nickname_check])
	pwd = PasswordField('Password', [InputRequired(), pwd_match_check])

	
class OrderItem(Form):
	title = StringField('Название блюда', [InputRequired()])
	price = StringField('Цена', [InputRequired()])
	users = StringField('Кто заказал')
	session = StringField('Ресторан')
