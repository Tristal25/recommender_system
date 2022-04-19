import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

# Initialize (including Database)
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(os.path.dirname(app.root_path), os.getenv('DATABASE_FILE', 'data.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控

db = SQLAlchemy(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    from recommender.database import User
    user = User.query.get(int(user_id))
    return user

login_manager.login_view = 'login'
login_manager.login_message ='Please login first!'

@app.context_processor
def inject_user():
    from recommender.database import User, Movie, Ratings
    users = User.query.all()
    movies = Movie.query.all()
    return dict(users = users, movies = movies)

from recommender import views, errors, commands