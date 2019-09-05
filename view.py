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
	
