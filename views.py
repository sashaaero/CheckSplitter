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


@app.route('/session/<int:sid>/delete-user/<int:uid>', methods=['DELETE'])
def delete_user_from_session(sid, uid):
    Session[sid].users.remove(User[uid])
    return redirect(url_for('session_edit'))


@app.route('/session/<int:sid>/')
def session_edit(sid):
    session = Session[sid]
    return render_template('session_edit.html', title="Создание сессии")




@app.route('/session/new')
@login_required
def session():
    s = Session()
    commit()
    return redirect(url_for('session_edit', sid=s.id))


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


@app.route('/<int:sid>/order/new', methods=["POST", "GET"])
@login_required
def order_new(sid):
    form = OrderItem(request.form)
    sess = db.Session.get(id=sid)
    if request.metod == 'POST' and form.validate():
        OrderItem(title=form.data['title'],
                  price=form.data['price'],
                  session=sess)
        return redirect(url_for('/<int:sid>/order/new'))
    return render_template('order_new.html', form=form, sess=sess)


@app.route('/history', methods=['POST', 'GET'])
@login_required
def history():
    user = current_user
    user_history = select(s for s in db.Session if s.users == user)
    return render_template('history.html', user_history=user_history, user=user)


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
