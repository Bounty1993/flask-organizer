import logging
from datetime import datetime, timedelta

from flask import flash, redirect, url_for, render_template, request, jsonify
from flask_login import current_user, login_required

from app import app, db
from .models import Task
from .forms import (
    TaskCreationForm,
)
from .paginator import Paginator

logger = logging.getLogger(__name__)


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('auth.profile'))
    return render_template('base.html', title='Title')


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
    is_filtered = limit is not None
    tasks = tasks.order_by(Task.start)
    search = request.args.get('search')
    tasks = Task.search(tasks, search)
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
    return render_template('tasks_list.html',
                           tasks=data, page=page,
                           is_filtered=is_filtered)


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


@app.route('/tasks/<int:id>/delete/', methods=['POST'])
@login_required
def task_delete(id):
    task = Task.query.get(id)
    user_id = current_user.id
    if task.user_id == user_id:
        task.set_deleted()
        flash('Zadanie zostało usunięte')
        return redirect(url_for('tasks_list'))
    flash('Nie możesz usunąć wybranego zadania')
    return redirect(url_for('tasks_list'))


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


@app.route('/tasks/tags')
def task_tags():
    return render_template('tasks_tags.html')


@app.route('/tasks/tags/create')
def create_tag():
    pass
