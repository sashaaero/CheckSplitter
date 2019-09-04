from wtforms import *
from wtforms.validators import *
from models import *


class OrderItem(Form):
    title = StringField('Название блюда', [InputRequired()])
    price = StringField('Цена', [InputRequired()])
    users = StringField('Кто заказад', [InputRequired()])