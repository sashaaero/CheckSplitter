from flask import Flask
from flask_login import LoginManager
from pony.flask import Pony
from config import settings
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS

from models import db

app = Flask(__name__)
app.secret_key = settings['secret_key']
Pony(app)
CORS(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect(app)
csrf.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.User.get(id=user_id)
