from datetime import datetime, timedelta

from flask_wtf import FlaskForm
from wtforms import StringField, TimeField, PasswordField, BooleanField, IntegerField, DateField
from wtforms.validators import (
    DataRequired, ValidationError, Length, EqualTo, Email)

from .models import User


class LoginForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    remember = BooleanField('Zapamiętać?', default=True)


class RegistrationForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired()])
    password1 = PasswordField('Hasło', validators=[DataRequired()])
    password2 = PasswordField(
        'Potwierdź hasło', validators=[DataRequired(), EqualTo('password1')])
    email = StringField('Email', validators=[Email()])
    disable_log = BooleanField('Nie loguj po rejestracji', default=False)

    def validate_username(form, field):
        username = field.data
        is_taken = User.query.filter_by(username=username).first()
        if is_taken:
            msg = 'Nazwa użytkonika jest już zajęta. Proszę użyj innej nazwy'
            raise ValidationError(msg)

    def validate_email(form, field):
        email = field.data
        is_taken = User.query.filter_by(email=email).first()
        if is_taken:
            msg = 'Email jest już zajęty. Proszę użyj innego maila'
            raise ValidationError(msg)


class PasswordResetAskForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])


class PasswordResetForm(FlaskForm):
    password1 = PasswordField('Hasło', validators=[DataRequired()])
    password2 = PasswordField('Potwierdź hasło', validators=[DataRequired()])

    def validate_password2(form, field):
        password1 = form.password1.data
        password2 = field.data
        if not (password1 == password2):
            raise ValidationError('Hasła się różnią')


class UpdateUserForm(FlaskForm):
    id = IntegerField()
    email = StringField('Email', validators=[Email()])
    about = StringField('Opis')

    def validate_user_id(form, field):
        user_id = field.data
        user = User.query.filter_by(id=user_id).first()
        if not user:
            raise ValidationError('Użytkownik nie istnieje')

    def validate_email(form, field):
        email = field.data
        user_id = form.id.data
        print(user_id)
        if email:
            is_taken = User.query.filter(User.id != user_id, User.email == email).first()
            if is_taken:
                raise ValidationError('Nieprawidłowy adres email')


class TaskCreationForm(FlaskForm):
    name = StringField('Nazwa', validators=[DataRequired()])
    place = StringField('Miejsce')
    description = StringField(
        'Opis', validators=[DataRequired(),
                         Length(1, 1200, 'Liczba znaków musi się mieścić między 1 a 1200')],
        description='Maksymalnie 1200 znaków')
    date = DateField('Data', validators=[DataRequired()], format="%d/%m/%Y")
    start = TimeField('Rozpoczęcie', validators=[DataRequired()], format="%H:%M")
    end = TimeField('Koniec', validators=[DataRequired()], format="%H:%M")

    def validate_start(form, field):
        now = datetime.utcnow() + timedelta(seconds=10)
        form_date = form.date.data
        if form_date == now.date():
            start_date = field.data
            if start_date <= now.time():
                msg = 'Data początkowa nie może być w przeszłości'
                raise ValidationError(msg)

    def validate_end(form, field):
        start_date = form.start.data
        end_date = field.data
        if start_date > end_date:
            msg = 'Data początkowa musi byc wcześniej niż data końca'
            raise ValidationError(msg)
