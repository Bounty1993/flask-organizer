import logging
from datetime import datetime, timedelta

from sqlalchemy import or_

from flask import flash, redirect, url_for, render_template, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required

from app import app, db
from .models import User, Task
from .forms import (
    TaskCreationForm, LoginForm, RegistrationForm,
    UpdateUserForm, PasswordResetAskForm, PasswordResetForm
)
from .paginator import Paginator

logger = logging.getLogger(__name__)


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    return render_template('base.html', title='Title')


@app.route('/login', methods=['GET', 'POST'])
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


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
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


@app.route('/profile', methods=['GET', 'POST'])
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


@app.route('/password_change', methods=['GET', 'POST'])
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


@app.route('/password_reset_ask', methods=['GET', 'POST'])
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


@app.route('/password_reset/<token>', methods=['GET', 'POST'])
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


def get_datetime(date, time):
    return datetime(date.year, date.month, date.day, time.hour, time.minute)


def make_short(data, num):
    if len(data) < num:
        return data
    short_data = data[:num]
    short_data += '...'
    return short_data


@app.route('/new', methods=['GET', 'POST'])
@login_required
def new_task():
    form = TaskCreationForm()
    if form.validate_on_submit():
        date = form.date.data
        start = get_datetime(date, form.start.data)
        end = get_datetime(date, form.end.data)
        task = Task(
            name=form.name.data, place=form.place.data,
            description=form.description.data,
            start=start, end=end
        )
        task.user_id = current_user.id
        db.session.add(task)
        db.session.commit()
        flash('Udało ci się utworzyć nowe zadanie')
        return redirect(url_for('index'))
    return render_template('task_create.html', form=form)


@app.route('/tasks/')
@login_required
def tasks_list():
    user_id = current_user.id
    tasks = Task.query.filter_by(user_id=user_id)
    limit = request.args.get('limit')
    if limit == 'important':
        tasks = tasks.filter_by(important=True)
    if limit == 'finishing':
        two_days = datetime.now() - timedelta(days=2)
        tasks = tasks.filter((Task.end > two_days))
    tasks = tasks.order_by(Task.start)
    search = request.args.get('search')
    if search:
        tasks = tasks.filter(
            (Task.name == search) |
            (Task.description == search) |
            (Task.place == search))
    data = {}
    num_page = request.args.get('page', 1)
    paginator = Paginator(tasks.all())
    page = paginator.page(num_page)
    for task in page.paginated:
        value = {
            'id': task.id,
            'name': task.name,
            'place': task.place,
            'summary': make_short(task.description, 20),
            'start': task.start.strftime('%H:%M'),
            'end': task.end.strftime('%H:%M'),
            'important': task.important,
        }
        date = task.start.date()
        if data.get(date):
            data[date].append(value)
        else:
            data[date] = [value, ]
    return render_template('tasks_list.html', tasks=data, page=page)


@app.route('/important/', methods=['POST'])
@login_required
def add_important():
    data = request.json
    task_id = int(data['id'])
    task = Task.query.get(task_id)
    if task:
        task.change_important()
        db.session.commit()
        return jsonify({'success': 'Hello'}), 200
    return jsonify({'error': 'Zapytanie błędne'}), 400


@app.route('/tasks/<int:id>/')
def task_detail(id):
    task = Task.query.filter_by(id=id).first()
    form = TaskCreationForm(obj=task)
    form.populate_obj(task)
    if form.validate_on_submit():
        print('Hello')
    return render_template('tasks_detail.html', form=form)


@app.route('/tasks/past')
def past_tasks():
    user_id = current_user.id
    print(user_id)
    past_tasks = Task.past_tasks(user_id)
    return render_template('past_tasks.html')
