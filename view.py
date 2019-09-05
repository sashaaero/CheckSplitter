from app import app
from flask_login import login_user, current_user, logout_user, login_required
from models import db
from form_request import *
from pony.orm import select, commit, flush, desc, sql_debug
from flask import render_template, request, flash, redirect, url_for
from datetime import datetime


@app.route('/session/order/new', methods=["POST", "GET"])
def order_new():
    user = current_user
    form = OrderItem(request.form)
    sessions_ = request.form['session']


@app.route('/', methods=["POST", "GET"] )
def index():
    return render_template('base.html', title='Base template')


@app.route('/reg', methods=['POST', 'GET'])
def reg:
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
@login_required()
def logout:
	logout_user()
	return redirect(url_for('index')) 