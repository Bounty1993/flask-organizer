from time import time
from datetime import datetime
import enum

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import render_template
import jwt

from app import db, app
from app import login
from app.auth.emails import send_email


user_category = db.Table(
    'user_category',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, index=True)
    email = db.Column(db.String(128), unique=True, index=True, nullable=True)
    password_hash = db.Column(db.String(128))
    about = db.Column(db.String(1200), nullable=True)
    tasks = db.relationship('Task', backref='author', lazy='dynamic')
    categories = db.relationship(
        'Category', secondary=user_category,
        lazy='dynamic', backref=db.backref('authors', lazy=True)
    )

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        is_valid = check_password_hash(self.password_hash, password)
        return is_valid

    def get_password_reset_token(self, expires=600):
        token = jwt.encode(
            {'password_reset': self.id, 'exp': time() + expires},
            app.config['SECRET_KEY'], algorithm='HS256')
        return token.decode()

    def send_password_reset_token(self):
        token = self.get_password_reset_token()
        data = {
            'subject': 'Restart hasła - Organize',
            'sender': app.config['ADMINS'][0],
            'recipients': [self.email, ],
            'body': render_template(
                'email/reset.txt', user=self.username, token=token),
            'body_html': render_template(
                'email/reset.html', user=self.username, token=token)
        }
        send_email(**data)

    @staticmethod
    def verify_password_reset_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['password_reset']
        except:
            return
        return User.query.get(id)


class TaskStatus(enum.Enum):
    active = 'active'
    deleted = 'deleted'


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    place = db.Column(db.String(128))
    description = db.Column(db.String(250))
    start = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    end = db.Column(db.DateTime, index=True, nullable=True)
    important = db.Column(db.Boolean, default=False)
    status = db.Column(
        db.Enum(TaskStatus),
        default=TaskStatus.active
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    def __repr__(self):
        return f'<Task {self.name} for user-{self.user_id}>'

    def change_important(self):
        self.important = not self.important

    def set_deleted(self):
        self.status = TaskStatus.deleted

    @classmethod
    def past_tasks(cls, user_id, start=None, end=None):
        tasks = cls.query.filter_by(user_id=user_id)
        if not end:
            end = datetime.today().date()
        return tasks.filter(cls.end < end)

    @classmethod
    def current_tasks(cls, start=None, end=None):
        if not start:
            start = datetime.today().date()
        return cls.query.filter(cls.end >= end)

    @staticmethod
    def search(tasks, query):
        if query:
            tasks = tasks.filter(
                (Task.name == query) |
                (Task.description == query) |
                (Task.place == query))
        return tasks


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    slug = db.Column(db.String(100))
    tasks = db.relationship('Task', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.title}>'

    @classmethod
    def verify_title(cls, title, user_id):
        print('TO DO')


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
