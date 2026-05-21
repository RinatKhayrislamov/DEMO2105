from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Email, Regexp
from models import User
import re

def validate_phone(form, field):
    # Ожидаем формат +7 (XXX) XXX-XX-XX или похожий, минимум 10 цифр
    if len(field.data) < 10:
        raise ValidationError('Некорректный номер телефона')

def validate_birth_date(form, field):
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', field.data):
        raise ValidationError('Дата должна быть в формате ДД.ММ.ГГГГ')

class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=3, max=80)])
    full_name = StringField('ФИО', validators=[DataRequired(), Length(min=5, max=150)])
    email = StringField('E-mail', validators=[DataRequired(), Email(message='Некорректный E-mail')])
    phone = StringField('Телефон', validators=[DataRequired(), validate_phone])
    birth_date = StringField('Дата рождения (ДД.ММ.ГГГГ)', validators=[DataRequired(), validate_birth_date])
    
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Этот логин уже занят.')
            
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Этот E-mail уже зарегистрирован.')

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RequestForm(FlaskForm):
    title = StringField('Тема заявки', validators=[DataRequired(), Length(max=100)])
    category = SelectField('Категория', choices=[
        ('', '-- Выберите категорию --'),
        ('Автобус', 'Автобус'),
        ('Электробус', 'Электробус'),
        ('Трамвай', 'Трамвай'),
    ], validators=[DataRequired(message='Выберите категорию')])
    date_str = StringField('Дата события (ДД.ММ.ГГ)', validators=[
        DataRequired(), 
        Length(min=8, max=8),
        Regexp(r'^\d{2}\.\d{2}\.\d{2}$', message='Формат: ДД.ММ.ГГ')
    ])
    description = TextAreaField('Описание проблемы', validators=[DataRequired()])
    submit = SubmitField('Отправить заявку')