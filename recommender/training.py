import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
import random
from werkzeug.security import generate_password_hash


# Data import and cleaning
def data_cleaning(ratings, movies):

    ## Basic attributes
    n_ratings = len(ratings)
    n_movies = len(ratings['movieId'].unique())
    n_users = len(ratings['userId'].unique())

    ## Forge name data
    name_list = ["Liam","Olivia","Noah","Emma","Oliver","Ava","Elijah","Charlotte","William","Sophia",
                 "Amelia","Benjamin","Isabella","Lucas","Mia","Henry","Evelyn","Alexander","Harper"]
    user_names = [random.choice(name_list) for i in range(n_users)]
    ratings = pd.merge(ratings, pd.DataFrame({
        "userId": list(range(1,n_users+1)),
        "names": user_names
    }), how="left", on="userId")

    ## Create ratingId
    ratings["ratingId"] = list(range(n_ratings))

    ## Extract year and title from movie names
    movies["year"]=movies["title"].str.extract(r"\((\d\d\d\d)\)$")
    movies["title"] = movies["title"].str.extract(r"^(.*)\s\(\d\d\d\d\)$")

    ## merge movie info into ratings
    ratings = pd.merge(ratings, movies, how = "left", on="movieId")

    ## Create users table
    users = ratings[["userId", "names"]].drop_duplicates().rename(columns = {"userId":"id"})
    #set default password: password
    users["password_hash"] = [generate_password_hash("password"),]*n_users
    users["username"] = [str(i) for i in list(range(1,n_users+1))]
    return users, ratings, movies

# Get popular movies

def popular_movies(ratings, movies):
    selected = ratings["movieId"].value_counts()[:10].index.tolist()
    pop_data = movies[movies["movieId"].isin(selected)]
    popular = []
    for i in range(len(pop_data["movieId"])):
        popular.append(dict(pop_data.iloc[i,]))
    return popular


# Recommender system modeling and prediction

## Data cleaning

def create_matrix(df):
    N = len(df['userId'].unique())
    M = len(df['movieId'].unique())

    # Map Ids to indices
    user_mapper = dict(zip(np.unique(df["userId"]), list(range(N))))
    movie_mapper = dict(zip(np.unique(df["movieId"]), list(range(M))))

    # Map indices to IDs
    user_inv_mapper = dict(zip(list(range(N)), np.unique(df["userId"])))
    movie_inv_mapper = dict(zip(list(range(M)), np.unique(df["movieId"])))

    user_index = [user_mapper[i] for i in df['userId']]
    movie_index = [movie_mapper[i] for i in df['movieId']]

    X = csr_matrix((df["rating"], (movie_index, user_index)), shape=(M, N))

    return X, user_mapper, movie_mapper, user_inv_mapper, movie_inv_mapper

## Modeling

def find_similar_movies(ratings, movie_id, k, metric='cosine', show_distance=False):
    neighbour_ids = []
    X, user_mapper, movie_mapper, user_inv_mapper, movie_inv_mapper = create_matrix(ratings)
    movie_ind = movie_mapper[movie_id]
    movie_vec = X[movie_ind]
    k += 1
    kNN = NearestNeighbors(n_neighbors=k, algorithm="brute", metric=metric)
    kNN.fit(X)
    movie_vec = movie_vec.reshape(1, -1)
    neighbour = kNN.kneighbors(movie_vec, return_distance=show_distance)
    for i in range(0, k):
        n = neighbour.item(i)
        neighbour_ids.append(movie_inv_mapper[n])
    neighbour_ids.pop(0)
    return neighbour_ids

## Prediction

def similar_movie(ratings, movies, userid, movieid, k=10):
    kmax = len(movies['movieId'].unique()) - len(ratings.loc[ratings["userId"] == userid]["movieId"].unique())
    if k > kmax:
        return (None, None)
    similar_ids = find_similar_movies(ratings, movie_id=movieid, k=k)
    selected = [i for i in similar_ids if i not in ratings.loc[ratings["userId"] == userid]["movieId"].values]
    recm_data = movies[movies["movieId"].isin(selected)]
    movie_base = movies[movies["movieId"] == movieid]
    movie_base_info= {
        "movieId": movieid,
        "title": movie_base["title"].values[0],
        "year": movie_base["year"].values[0],
        "genres": movie_base["genres"].values[0]
    }
    movies_recommend = []
    for i in range(len(recm_data["movieId"])):
        movies_recommend.append(dict(recm_data.iloc[i,]))
    return movie_base_info, movies_recommend

def recommend(ratings, movies, userid, k=5, num=20):
    user_info = ratings.loc[ratings["userId"] == userid]
    if len(user_info) == 0:
        return None
    rate_max = user_info["rating"].max()
    all_info = pd.merge(user_info, movies, how="left", on="movieId")
    kmax = len(movies['movieId'].unique()) - len(all_info["movieId"].unique())
    if k > kmax or num > kmax:
        return None
    # Recommend based on movies with ratings greater than maximum rating-0.5
    like_info = all_info.loc[all_info["rating"] >= rate_max-0.5]
    movie_base_info = []
    movies_recommend = []
    already_recommend = []
    inf_prevender = 0
    while len(movies_recommend) < num and inf_prevender <= 10:
        movie_id = random.choice(like_info['movieId'].values)
        similar_ids = find_similar_movies(ratings, movie_id=movie_id, k=k)
        selected = [i for i in similar_ids if (i not in all_info["movieId"].values) and (i not in already_recommend)]
        if len(selected) == 0:
            inf_prevender += 1
            continue
        already_recommend += selected
        recm_data = movies[movies["movieId"].isin(selected)]
        for i in range(len(recm_data["movieId"])):
            if len(movies_recommend) < num:
                movies_recommend.append(dict(recm_data.iloc[i,]))
            else:
                break
    return movies_recommend





