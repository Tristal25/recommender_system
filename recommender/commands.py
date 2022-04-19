import click
import warnings
from flask_login import UserMixin
from recommender.training import *
from recommender.database import *
from recommender import app, db

warnings.simplefilter(action='ignore', category=FutureWarning)

@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    ratings = pd.read_csv("https://s3-us-west-2.amazonaws.com/recommender-tutorial/ratings.csv")
    movies = pd.read_csv("https://s3-us-west-2.amazonaws.com/recommender-tutorial/movies.csv")
    users, ratings, movies = data_cleaning(ratings, movies)
    if drop:
        db.drop_all()
    movies.to_sql(name="movies", con=db.engine)
    users.to_sql(name="users", con=db.engine)
    ratings.to_sql(name="ratings", con=db.engine)
    db.session.commit()





