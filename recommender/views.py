import pandas as pd
from flask import render_template, request, url_for, redirect, flash
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import func
import time
import numpy as np
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
import random

from recommender.database import User, Movie, Ratings
from recommender import app, db
from recommender.training import create_matrix, find_similar_movies, recommend, popular_movies, similar_movie

# login page
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":

        users = User.query.all()
        if not users:
            flash("Please register first.")
            return redirect(url_for("index"))

        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            flash("Invalid input.")
            return redirect(url_for("login"))

        for user in users:
            if user.username == username and user.validate_password(password):
                login_user(user)
                flash("Login success.")
                return redirect(url_for("recommend_root"))

        flash("Invalid username or password.")
        return redirect(url_for("login"))
    return render_template("login.html")

# log out
@app.route("/user/logout")
def logout():
    logout_user()
    flash("Goodbye.")
    return(redirect(url_for("popular")))

# register
@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        users = User.query.all()
        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password or not name:
            flash("Invalid input.")
            return redirect(url_for("register"))

        for usr in users:
            if usr.username == username:
                flash("UserId occupied, please choose a different userId.")
                return redirect(url_for("register"))

        user = User(id = User.query.count()+1, names = name, username = username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created.")
        return redirect(url_for("recommend_root"))

    return render_template("register.html")


# settings
@app.route("/user/settings", methods = ["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        name = request.form["name"]

        if not name or len(name) > 20:
            flash ("Invalid input.")
            return redirect(url_for("settings"))

        current_user.names = name
        db.session.commit()
        flash("Settings updated.")
        return redirect(url_for("index"))
    return render_template("settings.html")


@app.route('/rating', methods = ["GET", "POST"])
def index():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        if not (request.form.get('rating').replace('.','',1).isdigit()):
            flash("Invalid input, please input number for rating.")
            return redirect(url_for('index'))
        title = request.form.get('title')
        rating = float(request.form.get('rating'))
        if not title.lower() in [str(i[0]).lower() for i in Movie.query.with_entities(Movie.title).all()] or len(title) > 60:
            flash('Movie not in our database.')
            return redirect(url_for('index'))
        input = Movie.query.filter(func.lower(Movie.title)==func.lower(title)).all()[0]
        new_info = Ratings(ratingId = Ratings.query.count(), title = input.title, year = input.year,
                           rating = rating, timestamp = int(time.time()),
                           names = current_user.names, userId = current_user.id,
                           movieId = input.movieId, genres = input.genres)
        db.session.add(new_info)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('index'))
    if current_user.is_authenticated:
        ratings = Ratings.query.filter_by(userId = current_user.id).all()
    else:
        ratings = Ratings.query.all()
    return render_template('index.html', ratings = ratings)

@app.route('/', methods = ['GET', 'POST'])
def recommend_root():
    if not current_user.is_authenticated:
        return redirect(url_for("popular"))
    movies = pd.read_sql_table("movies", con=db.engine)
    ratings = pd.read_sql_table("ratings", con=db.engine)
    if len(ratings.loc[ratings["userId"] == current_user.id]) == 0:
        flash("Input ratings to get recommendations")
        return redirect(url_for('index'))

    if request.method == 'POST':
        if not (request.form.get('k').isdigit() and request.form.get('num').isdigit()):
            flash("Invalid input, please input integer number.")
            return redirect(url_for('recommend_root'))
        k = int(request.form.get('k'))
        num = int(request.form.get('num'))
        maxnum = movies.movieId.count()-len(ratings.loc[ratings["userId"]==current_user.id]["movieId"].unique())
        if k > maxnum or num > maxnum:
            flash('Number to recommend exceed capacity, try to recommend less.')
            return redirect(url_for('recommend_root'))
    else:
        k = 5
        num = 20

    recommend_data = recommend(ratings, movies, current_user.id, k, num)
    return render_template('recommend.html', recommend_data = recommend_data)

@app.route("/popular", methods=['GET', 'POST'])
def popular():
    ratings = pd.read_sql_table("ratings", con=db.engine)
    movies = pd.read_sql_table("movies", con=db.engine)
    popular_ls = popular_movies(ratings, movies)
    return render_template('popular.html', popular = popular_ls)


@app.route("/movie/similar/<int:rating_id>", methods = ["GET", "POST"])
@login_required
def similar(rating_id):
    movies = pd.read_sql_table("movies", con=db.engine)
    ratings = pd.read_sql_table("ratings", con=db.engine)

    if request.method == 'POST':
        if not (request.form.get('k').isdigit()):
            flash("Invalid input, please input integer number.")
            return redirect(url_for('recommend_root'))
        k = int(request.form.get('k'))
        maxnum = movies.movieId.count() - len(ratings.loc[ratings["userId"] == current_user.id]["movieId"].unique())
        if k > maxnum:
            flash('Number to recommend exceed capacity, try to recommend less.')
            return redirect(url_for('recommend_root'))
    else:
        k = 20

    movieid = int(ratings[ratings["ratingId"] == rating_id].movieId)
    movie_based, recommend_data = similar_movie(ratings, movies, current_user.id, movieid, k=k)
    return render_template('similar.html', movie_based = movie_based, recommend_data = recommend_data)


# Editing page
@app.route("/movie/edit/<int:rating_id>", methods = ["GET", "POST"])
@login_required
def edit(rating_id):
    record = Ratings.query.get_or_404(rating_id)

    if request.method == "POST":
        if not (request.form.get('rating').replace('.','',1).isdigit()):
            flash("Invalid input, please input number for rating.")
            return redirect(url_for('index'))
        title = request.form.get('title')
        rating = float(request.form.get('rating'))
        if not title.lower() in [str(i[0]).lower() for i in Movie.query.with_entities(Movie.title).all()] or len(title) > 60:
            flash('Movie not in our database.')
            return redirect(url_for("edit", rating_id = rating_id))
        input = Movie.query.filter(func.lower(Movie.title) == func.lower(title)).all()[0]
        record.title = input.title
        record.year = input.year
        record.rating = rating
        record.timestamp = int(time.time())
        record.movieId = input.movieId
        record.genres = input.genres
        db.session.commit()
        flash("Item updated.")
        return redirect(url_for('index'))

    return render_template('edit.html', rating = record)

# Deleting records
@app.route("/movie/delete/<int:rating_id>", methods = ["GET", "POST"])
@login_required
def delete(rating_id):
    if request.method == "POST":
        record = Ratings.query.get_or_404(rating_id)
        db.session.delete(record)
        db.session.commit()
        flash("Item deleted.")
        return redirect(url_for('index'))