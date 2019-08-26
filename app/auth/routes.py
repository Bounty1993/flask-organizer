import logging

from flask import flash, redirect, url_for, render_template, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required

from app import app, db
from app.models import User, Task
from .forms import (
    LoginForm, RegistrationForm,
    UpdateUserForm, PasswordResetAskForm, PasswordResetForm
)
from app.auth import bp
logger = logging.getLogger(__name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('index'))
        flash('dane są niepoprawne')
        return redirect(url_for('login'))
    return render_template('login.html', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        user = User(username=username, email=email)
        password = form.password1.data
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        disable_log = form.disable_log.data
        if not disable_log:
            login_user(user)
        return redirect(url_for('index'))
    return render_template('signup.html', form=form)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    form = UpdateUserForm(obj=user)
    if form.validate_on_submit():
        user.about = form.about.data
        user.email = form.email.data
        db.session.commit()
        flash('Aktualizacja danych przebiegła pomyślnie')
        return redirect(url_for('index'))
    return render_template('update_profile.html', form=form)


@bp.route('/password_change', methods=['GET', 'POST'])
@login_required
def password_change():
    user = current_user
    form = PasswordResetForm()
    if form.validate_on_submit():
        password = form.password1.data
        user.set_password(password)
        db.session.commit()
        flash('Zmiana hasła powiodła się')
        return redirect(url_for('index'))
    return render_template('password_reset.html', form=form)


@bp.route('/password_reset_ask', methods=['GET', 'POST'])
def password_reset_ask():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = PasswordResetAskForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            user.send_password_reset_token()
        flash('Sprawdź swoją skrzynkę i postępuj według instrukcji')
        return redirect(url_for('index'))
    return render_template('password_reset_ask.html', form=form)


@bp.route('/password_reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_password_reset_token(token)
    if not user:
        return redirect(url_for('index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        password = form.password1.data
        user.set_password(password)
        db.session.commit()
        flash('Zmiana hasła powiodła się')
        return redirect(url_for('index'))
    return render_template('password_reset.html', form=form)
