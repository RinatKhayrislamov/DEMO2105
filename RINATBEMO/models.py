from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    
    # Новые поля
    full_name = db.Column(db.String(150), nullable=False)      # ФИО
    birth_date = db.Column(db.String(10), nullable=False)      # Дата рождения (ДД.ММ.ГГГГ)
    phone = db.Column(db.String(20), nullable=False)           # Телефон
    email = db.Column(db.String(120), unique=True, nullable=False) # Email
    
    is_admin = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='Активен')
    
    requests = db.relationship('Request', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='author', lazy=True)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date_str = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Новая')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review = db.relationship('Review', backref='request', uselist=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)