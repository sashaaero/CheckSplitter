from flask import Flask
from flask_login import LoginManager
from pony.flask import Pony


from models import db

app = Flask(__name__)
Pony(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return db.User.get(user_id)
