from app import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    total_points = db.Column(db.Float, default=0)

class GameResult(db.Model):
    __tablename__ = 'game_results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    champion_id = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GameResult {self.id} user={self.user_id} champ={self.champion_id} points={self.points}>'

class Champion(db.Model):
    __tablename__ = 'champions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    region = db.Column(db.String(50))
    damage_type = db.Column(db.String(50))
    position = db.Column(db.String(50))