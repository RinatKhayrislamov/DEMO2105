from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, NumberRange
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Этот логин уже занят.')

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RequestForm(FlaskForm):
    title = StringField('Тема заявки', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Описание проблемы', validators=[DataRequired()])
    submit = SubmitField('Отправить заявку')

class ReviewForm(FlaskForm):
    text = TextAreaField('Ваш отзыв', validators=[DataRequired()])
    rating = IntegerField('Оценка (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Оставить отзыв')