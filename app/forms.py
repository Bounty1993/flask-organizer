from datetime import datetime, timedelta

from flask_wtf import FlaskForm
from wtforms import StringField, TimeField, DateField
from wtforms.validators import (
    DataRequired, ValidationError, Length)


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


class CategoryCreationForm(FlaskForm):
    title = StringField('Nazwa', validators=[DataRequired()])


class TaskAddForm(FlaskForm):
    pass
