from app import app
from flask_login import login_user, current_user, logout_user, login_required
from models import *
from forms import RegForm, LoginForm, OrderItem, CreditForm
from pony.orm import select, commit, flush, desc, sql_debug
from flask import render_template, request, flash, redirect, url_for
from datetime import datetime


@app.errorhandler(404)
def error_404(e):
    return render_template('404.html'), 404


@app.route('/', methods=["POST", "GET"])
@login_required
def index():
    curr_session = current_user.current_session
    if curr_session:
        return redirect(url_for('session_edit', sid=curr_session.id))
    return render_template('index.html', title='Главная')


@app.route('/session/new')
@login_required
def session_new():
    curr_session = current_user.current_session
    if curr_session is None:
        curr_session = Session()
        UserInSession(user=current_user, session=curr_session)
        commit()
    return redirect(url_for('session_edit', sid=curr_session.id))


@app.route('/session/<int:sid>/')
def session_edit(sid):
    session = Session.get(id=sid)
    if session is None:
        return render_template('404.html')
    title = 'Сессия %s' % (session.title if session.title is not None else str(session.id))
    users = select(u.user for u in session.users).order_by(lambda u: u.id)[:]
    # Code above creates list of tuples, where one tuple contains (current order оbject, users of this order).
    orders_with_users = []
    users_in_order = []
    for order in session.orders:
        for uis in order.user_in_sessions:
            users_in_order.append(uis.user)
        orders_with_users.append((order, users_in_order))
        users_in_order = []
    return render_template('session_edit.html', title=title, session=session, users=users, orders=orders_with_users)


@app.route('/session/<int:sid>/add_user')
def add_user(sid):
    session = Session[sid]
    users = select(u for u in User if u not in session.users.user and not u.virtual)
    users_list = []
    for u in users:
        users_list.append({
            'id': u.id, 'fullname': u.fullname, 'login': u.nickname
        })
    return render_template('add_user.html', cuser=current_user, users=users_list, session=session)


@app.route('/session/<int:sid>/add_user/<int:uid>')
def add_user_(sid, uid):
    session = Session.get(id=sid)
    user = User.get(id=uid)
    if user is None or session is None:
        return render_template('404.html')
    check = UserInSession(session=session, user=user)
    if check is None:  # TODO add error to logs
        UserInSession(session=session, user=user)
    return redirect(url_for('add_user', sid=sid))


@app.route('/session/<int:sid>/delete_user/<int:uid>')
def delete_user(sid, uid):
    session = Session.get(id=sid)
    user = User.get(id=uid)
    if user is None or session is None:
        return render_template('404.html')
    check = UserInSession.get(session=session, user=user)
    if check is None:
        pass  # TODO add error to logs
    check.delete()
    commit()
    num = select(u for u in session.users).count()
    if num > 0:
        return redirect(url_for('session_edit', sid=sid))
    session.delete()
    return redirect(url_for('index'))


@app.route('/reg', methods=['POST', 'GET'])
def reg():
    form = RegForm(request.form)
    if request.method == 'POST' and form.validate():
        User(nickname=form.data['nickname'],
             fullname=form.data['fullname'],
             password=form.data['pwd1'])
        return redirect(url_for('index'))
    return render_template('reg.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.get(nickname=form.data['nickname'])
        pwd = form.data['pwd']
        if user.password != pwd:
            return 'Incorrect password'
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html', form=form, title='Вход')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/<int:sid>/order/new', methods=["POST", "GET"])
@login_required
def order_new(sid):
    form = OrderItem(request.form)
    sess = Session.get(id=sid)
    if sess is None:
        return render_template('404.html')
    users = select(uis.user for uis in UserInSession if uis.session == sess)[:]
    if request.method == 'POST' and form.validate():
        fullnames = request.form.getlist('users')
        order = OrderedItem(title=form.data['title'],
                            price=form.data['price'],
                            session=sess)
        for fullname in fullnames:
            uis = UserInSession.get(user=User.get(fullname=fullname))
            order.user_in_sessions.add(uis)
        return redirect(url_for('order_new', sid=sess.id))
    return render_template('order_new.html', form=form, users=users)


@app.route("/<int:sid>/order/<int:oid>/delete")
@login_required
def order_delete(sid, oid):
    item = OrderedItem.get(id=oid)
    if item is None:
        return render_template('404.html')
    OrderedItem[oid].delete()
    return redirect(url_for("session_edit", sid=sid))


@app.route("/<int:sid>/order/<int:oid>/edit", methods=['GET','POST'])
@login_required
def order_edit(sid, oid):
    session = Session.get(id=sid)
    order = OrderedItem.get(id=oid)
    if None in (session, order):
        return render_template('404.html')
    users_in_order = list(order.user_in_sessions.user)
    if request.method == "POST":
        fullnames = request.form.getlist('users')  # хуета, сделай айдишниками
        title = request.form.get('titleInput')
        price = int(request.form.get('priceInput'))
        if title != order.title:
            order.title = title
        if price != order.price:
            order.price = price
        users_in_form = []
        for fullname in fullnames:
            # getting userInSession objects to list, via nicknames from form
            users_in_form.append(UserInSession.get(user=User.get(fullname=fullname)))
        for uis in order.user_in_sessions:
            if uis not in users_in_form:
                order.user_in_sessions.remove(uis)
        for uif in users_in_form:
            if uif not in order.user_in_sessions:
                order.user_in_sessions.add(uif)
        return redirect(url_for('order_edit', sid=sid, oid=oid))

    return render_template("order_edit.html", order=order, usersInOrder=users_in_order)


@app.route('/history', methods=['POST', 'GET'])
@login_required
def history():
    user = current_user
    user_history = select(s for s in db.Session if s.users == user)
    return render_template('history.html', user_history=user_history, user=user)


@app.route('/credit')
@login_required
def check_credit():
    masters = current_user.mastered_credits
    slaves = current_user.slaved_credits
    '''
    Проверка случаев, когда:
    1)ты должен пользователю n, он тебе n;
    2)Пользователь должен тебе m, ты ему n, m > n
    3)Пользователь должен тебе m, ты ему n, m < n
    '''
    for m_credit in masters:
        for s_credit in slaves:
            # поиск строк, где current_user является мастером и слэйвом
            if m_credit.slave.id == s_credit.master.id:
                # m > n, соответственно долг cur_user убирается, долг cur_userУ уменьшается на s_credit.value
                if m_credit.value > s_credit.value:
                    Credit[s_credit.id].delete()
                    Credit[m_credit.id].value = m_credit.value - s_credit.value
                # m < n, соответственно долг cur_userУ убирается, долг cur_user уменьшается на m_credit.value
                elif m_credit.value < s_credit.value:
                    Credit[m_credit.id].delete()
                    Credit[s_credit.id].value = s_credit.value - m_credit.value
                # m = n, никто никому не должен
                elif m_credit.value == s_credit.value:
                    Credit[m_credit.id].delete()
                    Credit[s_credit.id].delete()
    return render_template(
        'credit.html', user=current_user, masters=masters, slaves=slaves
    )


@app.route('/edit_credit/<int:uid>', methods=['GET', 'POST'])
@login_required
def edit_credit(uid):
    form = CreditForm(request.form)
    user = Credit[uid]
    if request.method == "POST" and form.validate():
        input_value = int(form.value.data)
        val = Credit[uid].value
        result = val - input_value
        if result > 0:
            Credit[uid].value = result
        elif result == 0:
            Credit[uid].delete()
        else:
            flash('Возвращаемая сумма превышает размер долга. Пожалуйста, скорректируйте данные!', 'error')
            return redirect(url_for('edit_credit', uid=uid))
        return redirect(url_for('check_credit'))
    return render_template('edit_credit.html', user=user, form=form)