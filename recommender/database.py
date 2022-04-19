from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from recommender import db

class User(db.Model, UserMixin):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    names = db.Column(db.String(20))
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

class Ratings(db.Model):
    __tablename__ = "ratings"
    __table_args__ = {'extend_existing': True}
    ratingId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer)
    movieId = db.Column(db.Integer)
    names = db.Column(db.String(20))
    timestamp = db.Column(db.Integer)
    rating = db.Column(db.Float)
    title = db.Column(db.String(60))
    genres = db.Column(db.String(60))
    year = db.Column(db.String(4))

class Movie(db.Model):
    __tablename__ = "movies"
    __table_args__ = {'extend_existing': True}
    movieId = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    genres = db.Column(db.String(60))
    year = db.Column(db.String(4))