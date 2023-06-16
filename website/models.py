from . import db 
from flask_login import UserMixin
from sqlalchemy.sql import func


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cash = db.Column(db.String(100))
    account_value = db.Column(db.String(100))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10))
    orderType = db.Column(db.String(5))
    price = db.Column(db.String(100))
    quantity = db.Column(db.String(10))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    trades = db.relationship('Trade')
    portfolios = db.relationship('Portfolio')