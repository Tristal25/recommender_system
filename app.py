from recommender.commands import *
from recommender.training import *
import os

from dotenv import load_dotenv
from recommender import app

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)




if __name__ == '__main__':
    app.run(debug=True)
