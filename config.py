import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(basedir, 'instance', 'lolidle.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RIOT_API_KEY = os.environ.get('RIOT_API_KEY')