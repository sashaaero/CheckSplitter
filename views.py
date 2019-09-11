from app import app
from flask_login import login_user, current_user, logout_user, login_required
from models import db
from forms import *
from pony.orm import select, commit, flush, desc, sql_debug
from flask import render_template, request, flash, redirect, url_for
from datetime import datetime

def authorized():
    if not current_user:
        return False
    auth = current_user.is_authenticated
    if callable(auth):
        return auth()
    return auth

@app.route('/', methods=["POST", "GET"])
@login_required
def index():
    return render_template('index.html', title='Главная')


@app.route('/create_session', methods=["POST", "GET"])
def session():
    if not authorized():
        return redirect(url_for('login'))
    user = User[current_user.id]

    users = select(user in User)[:]
    users.remove(user)
    current_dt = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

    form = request.form
    if request.method == 'POST' and 'create' in request.form:
        invited_users = request.form.getlist('user[]')
        try:
            invited_users.remove('Пользователь')
        except ValueError:
            pass

        start_dt = request.form.get('datetimeInput')
        new_session = Session()
        new_session.session_maintains.add(user)
        for user_id in invited_users:
            u = User[user_id]
            new_session.users.add(u)
        new_session.start = start_dt

        return redirect(url_for('index'))

    return render_template('session.html', title='Session template', users=users, current_dt=current_dt)


@app.route('/reg', methods=['POST', 'GET'])
def reg():
    form = RegForm(request.form)
    if request.method == 'POST' and form.validate():
        User(nickname=form.data['nickname'], fullname=form.data['fullname'], pwd=form.data['pwd1'])
        return redirect(url_for('nickname'))
    return render_template('reg.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.get(nickname=form.data['nickname'])
        pwd = form.data['pwd']
        if user.pwd != pwd:
            return 'Incorrect password'
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html', form=form)


@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/session/order/new', methods=["POST", "GET"])
def order_new():
    user = current_user
    form = OrderItem(request.form)
    sessions_ = request.form['session']
