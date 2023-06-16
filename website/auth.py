from flask import Blueprint, render_template, request, flash, redirect, url_for 
from .models import User, Portfolio
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userName = request.form.get('userName')
        password = request.form.get('password')

        user = User.query.filter_by(userName=userName).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password you bozo! Try again.', category='error')
        else:
            flash('Username does not exists.', category='error')
    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.menu'))

@auth.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        userName = request.form.get('userName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(userName=userName).first()
        if user:
            flash('Username already exists. You\'re not original.', category='error')
        elif len(userName) < 3:
            flash('Username be too short.', category='error')
        elif len(password1) < 1:
            flash('Bro...Enter a password.', category='error')
        elif password1 != password2:
            flash('Passwords do not match...', category='error')
        else:
            new_user = User(userName=userName, password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()

            new_portfolio = Portfolio(cash='100000', account_value='100000', user_id=new_user.id)
            db.session.add(new_portfolio)
            db.session.commit()
            
            flash('Account created successfully!', category='success')
            login_user(new_user, remember=True)
            return redirect(url_for('views.home'))


    return render_template("sign_up.html", user=current_user)