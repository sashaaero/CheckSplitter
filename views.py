from app import app
from flask_login import login_user, current_user, logout_user, login_required
from models import *
from forms import RegForm, LoginForm, OrderItem, CreditForm, VirtualRegForm
from pony.orm import select, commit, flush, desc, sql_debug
from flask import render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash
from flask_cors import cross_origin
from datetime import datetime
from collections import defaultdict
from math import isclose


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
        curr_session.start = datetime.now()
        UserInSession(user=current_user, session=curr_session)
        commit()
    return redirect(url_for('session_edit', sid=curr_session.id))


def debt_calc(session):
    users_dict = {}
    values = defaultdict(int)
    orders = []
    maintainers = {}
    for uis in session.users:
        users_dict.update({uis.user.nickname: uis.user.id})
        maintainers.update({uis.user.nickname: uis.value})

    for order in session.orders:
        buyers = ""
        for uis in order.user_in_sessions:
            buyers += uis.user.nickname + ' '
        orders.append((order.title, order.price, buyers))

    for title, price, users in orders:
        count = len(users.split())
        for user in users.split():
            name = users_dict[user]
            values[name] += (price / count)

    #test
    should_be = sum(o[1] for o in orders)
    counted = sum(val for val in values.values())
    maintaied = sum(v for k, v in maintainers.items())
    assert isclose(should_be, counted), (should_be, counted)
    assert should_be <= maintaied

    slaves = []
    masters = []

    for k, v in maintainers.items():
        name = users_dict[k]
        ordered = values[name]
        val = int(v - ordered)
        if val < 0:
            slaves.append((-val, name))
        else:
            masters.append((val, name))

    masters.sort(key=lambda i: i[0], reverse=True)
    slaves.sort(key=lambda i: i[0], reverse=True)

    if slaves and masters:
        log = []
        s_val, slave = slaves.pop(0)
        m_val, master = masters.pop(0)
        while slave:
            if m_val > s_val:
                log.append((slave, master, s_val))
                m_val -= s_val
                if len(slaves) > 0:
                    s_val, slave = slaves.pop(0)
                else:
                    break
            elif s_val > m_val:
                log.append((slave, master, m_val))
                s_val -= m_val
                if len(masters) > 0:
                    m_val, master = masters.pop(0)
                else:
                    break
            else:
                log.append((slave, master, s_val))
                if len(slaves) > 0:
                    s_val, slave = slaves.pop(0)
                else:
                    break
                if len(masters) > 0:
                    m_val, master = masters.pop(0)
                else:
                    break
        # TODO Checkout different variants of ending a session
        assert not masters
        assert not slaves

        for debt in log:
            m = User[debt[1]]
            s = User[debt[0]]
            c = Credit.get(master=m, slave=s)
            if c is not None:
                c.value += debt[2]
            else:
                Credit(
                    master=m,
                    slave=s,
                    value=debt[2]
                )


@app.route('/session/<int:sid>/', methods=["POST", "GET"])
@login_required
def session_edit(sid):
    session = Session.get(id=sid)
    if session is None:
        return render_template('404.html')
    title = 'Сессия %s' % (session.title if session.title is not None else str(session.id))
    users = select(u for u in session.users).order_by(lambda u: u.id)[:]
    # Code above creates list of tuples, where one tuple contains (current order оbject, users of this order).
    orders_with_users = []
    users_in_order = []
    for order in session.orders:
        for uis in order.user_in_sessions:
            users_in_order.append(uis.user)
        orders_with_users.append((order, users_in_order))
        users_in_order = []

    if request.method == "POST" and "end_session" in request.form:
        #TODO conditions when impossible to end the session
        session.end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        debt_calc(session)
        return redirect(url_for("index"))

    if request.method == "POST" and "change_session_title" in request.form:
        session.title = request.form["session_title"]
        return redirect(url_for("session_edit", sid=sid))

    return render_template('session_edit.html', title=title, session=session, users=users, orders=orders_with_users,
                           cuser=current_user)

@app.route('/session/<int:sid>/add_money', methods=["POST"])
@cross_origin(methods=["POST"])
@login_required
def add_money(sid):
    data = request.get_json()
    if "amount" in data.keys():
        session = Session[sid]
        user = User[data["uid"]]
        uis = UserInSession.get(session=session, user=user)
        uis.value = int(data["amount"])
        return redirect(url_for("session_edit", sid=sid))
    else:
        return redirect(url_for("session_edit", sid=sid))

@app.route('/session/<int:sid>/add_user', methods=['POST', 'GET'])
@login_required
def add_user(sid):
    form = VirtualRegForm(request.form)
    session = Session[sid]
    users = select(u for u in User if u not in session.users.user and not u.virtual)
    users_list = []
    for u in users:
        users_list.append({
            'id': u.id, 'fullname': u.fullname, 'login': u.nickname
        })
    if request.method == 'POST' and form.validate():
        virtual_user = User(nickname=form.nickname.data,
                             fullname=form.fullname.data,
                             password='None')
        commit()
        return redirect(url_for('add_user_', sid=session.id, uid=virtual_user.id))
    return render_template('add_user.html', cuser=current_user, users=users_list, session=session, form=form)


@app.route('/session/<int:sid>/add_user/<int:uid>')
@login_required
def add_user_(sid, uid):
    session = Session.get(id=sid)
    user = User.get(id=uid)
    if user is None or session is None:
        return render_template('404.html')
    check = UserInSession.get(session=session, user=user)
    if check is None:  # TODO add error to logs
        UserInSession(session=session, user=user)
    return redirect(url_for('add_user', sid=sid))


@app.route('/session/<int:sid>/delete_user/<int:uid>')
@login_required
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
             password=generate_password_hash(form.data['pwd1']))
        return redirect(url_for('index'))
    return render_template('reg.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.get(nickname=form.data['nickname'])
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
    sorted(users, key=lambda u: u.fullname)
    if request.method == 'POST' and form.validate():
        ids = request.form.getlist('users')
        order = OrderedItem(title=form.data['title'],
                            price=form.data['price'],
                            session=sess)
        for id in ids:
            uis = UserInSession.get(user=User[id], session=sess)
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
    users_not_in_order = list(set(session.users.user).difference(users_in_order))
    if request.method == "POST":
        ids = request.form.getlist('users')
        title = request.form.get('titleInput')
        price = int(request.form.get('priceInput'))
        if title != order.title:
            order.title = title
        if price != order.price:
            order.price = price
        users_in_form = []
        for id in ids:
            # getting userInSession objects to list, via user ids from dropdown
            users_in_form.append(UserInSession.get(user=User[id]))
        for uis in order.user_in_sessions:
            if uis not in users_in_form:
                order.user_in_sessions.remove(uis)
        for uif in users_in_form:
            if uif not in order.user_in_sessions:
                order.user_in_sessions.add(uif)
        return redirect(url_for('order_edit', sid=sid, oid=oid))

    return render_template("order_edit.html", order=order, users_in_order=users_in_order,
                           users_not_in_order=users_not_in_order)


@app.route('/history', methods=['POST', 'GET'])
@login_required
def history():
    user = current_user
    user_history = select(s for s in db.Session if user in (u.user for u in s.users))
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
            if m_credit.value != 0 and s_credit.value != 0:
                if m_credit.slave.id == s_credit.master.id:
                    # m > n, соответственно долг cur_user убирается, долг cur_userУ уменьшается на s_credit.value
                    if m_credit.value > s_credit.value:
                        CreditEdition(user=m_credit.slave.id, affected_user=m_credit.master.id, credit=s_credit.id,
                                      old_value=s_credit.value, new_value=0)
                        Credit[m_credit.id].value = m_credit.value - s_credit.value
                        Credit[s_credit.id].value = 0
                    # m < n, соответственно долг cur_userУ убирается, долг cur_user уменьшается на m_credit.value
                    elif m_credit.value < s_credit.value:
                        CreditEdition(user=s_credit.slave.id, affected_user=s_credit.master.id, credit=m_credit.id,
                                      old_value=m_credit.value, new_value=0)
                        Credit[s_credit.id].value = s_credit.value - m_credit.value
                        Credit[m_credit.id].value = 0
                    # m = n, никто никому не должен
                    elif m_credit.value == s_credit.value:
                        CreditEdition(user=m_credit.master.id, affected_user=m_credit.slave.id, credit=m_credit.id,
                                      old_value=m_credit.value, new_value=0)
                        Credit[m_credit.id].value = 0
                        CreditEdition(user=s_credit.master.id, affected_user=s_credit.slave.id, credit=s_credit.id,
                                      old_value=s_credit.value, new_value=0)
                        Credit[s_credit.id].value = 0
    return render_template('credit.html', user=current_user, masters=masters, slaves=slaves)


@app.route('/edit_credit/<int:uid>', methods=['GET', 'POST'])
@login_required
def edit_credit(uid):
    form = CreditForm(request.form)
    cur_row = Credit[uid]
    if request.method == "POST" and form.validate():
        input_value = int(form.value.data)
        val = cur_row.value
        result = val - input_value
        if result > 0:
            cur_row.value = result
            CreditEdition(user=cur_row.master.id, affected_user=cur_row.slave.id, credit=uid, old_value=val,
                          new_value=result)
        elif result == 0:
            cur_row.value = 0
            CreditEdition(user=cur_row.master.id, affected_user=cur_row.slave.id, credit=uid, old_value=val,
                          new_value=result)
        else:
            flash("Возвращаемая сумма превышает размер долга. "
                  "Пожалуйста, скорректируйте данные!", "error")
            return redirect(url_for('edit_credit', uid=uid))
        return redirect(url_for('check_credit'))
    return render_template('edit_credit.html', user=cur_row, form=form)


@app.route('/credit_history', methods=['GET', 'POST'])
@login_required
def credit_history():
    return render_template(
        'credit_history.html',
        user_history=current_user.credit_editions,
        affected_history=current_user.affected_editions
        )