from app import app
from flask_login import login_user, current_user, logout_user, login_required
from models import *
from forms import RegForm, LoginForm, OrderItem, CreditForm
from pony.orm import select, commit, flush, desc, sql_debug
from flask import render_template, request, flash, redirect, url_for
from datetime import datetime


@app.route('/', methods=["POST", "GET"])
@login_required
def index():
    return render_template('index.html', title='Главная')


@app.route('/session/new', methods=["POST", "GET"])
@login_required
def session():
    users = list(select(u for u in User))
    users.remove(current_user)

    form = request.form
    if request.method == 'POST' and 'create' in request.form:
        maintainers = request.form.getlist('maintainer[]')
        invited_users = request.form.getlist('user[]')
        try:
            maintainers.remove('Мэйнтейнер')
        except ValueError:
            pass

        try:
            invited_users.remove('Пользователь')
        except ValueError:
            pass

        start_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_session = Session()

        for user_id in maintainers:
            u = User[user_id]
            s = SessionMaintain(
                user=u,
                session=new_session
            )
            new_session.session_maintains.add(s)

        for user_id in invited_users:
            u = User[user_id]
            new_session.users.add(u)
        new_session.start = start_dt

        return redirect(url_for('index'))

    return render_template('session.html', title='Session template', users=users)


@app.route('/reg', methods=['POST', 'GET'])
def reg():
    form = RegForm(request.form)
    if request.method == 'POST' and form.validate():
        User(nickname=form.data['nickname'], fullname=form.data['fullname'], password=form.data['pwd1'])
        return redirect(url_for('index'))
    return render_template('reg.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.get(nickname=form.data['nickname'])
        pwd = form.data['pwd']
        if user.password != pwd:
            return 'Incorrect password'
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html', form=form, title='Вход')


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


@app.route('/credit', methods=['POST','GET'])
@login_required
def check_credit():
    user = current_user
    masters = select(c for c in Credit if c.master.nickname == user.nickname).order_by(Credit.value)[:]
    slaves = select(c for c in Credit if c.slave.nickname == user.nickname).order_by(Credit.value)[:]
    return render_template('credit.html', user=user, masters=masters, slaves=slaves)


@app.route('/edit_credit', methods=['POST'])
@login_required
def edit_credit():
    form = CreditForm()
    credit_line_id = request.form['id']
    user = Credit.get(id=credit_line_id)
    return render_template('edit_credit.html', user=user, form=form)


@app.route('/calculate', methods=['POST'])
@login_required
def calculate():
    form = CreditForm(request.form)
    if request.method == 'POST':
        input_value = int(form.data['value'])
        cur_user_id = request.form['id']
        val = Credit[cur_user_id].value
        result = val - input_value
        if result > 0:
            Credit[cur_user_id].value = result
        elif result == 0:
            Credit[cur_user_id].delete()
        else:
            flash('Возвращаемая сумма превышает размер долга. Пожалуйста, скорректируйте данные!', 'warning')
            return redirect(url_for('check_credit'))
        return redirect(url_for('check_credit'))