import os
from flask import Flask, g, render_template, request, jsonify, session, url_for, redirect, Response
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_socketio import SocketIO, send, disconnect
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///' + os.path.join(basedir, 'carousel.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SESSION_TYPE = 'filesystem'
    SECRET_KEY = 'chat'
    POSTS_PER_PAGE = 20


app = Flask(__name__)
app.config.from_object(Config)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)
socketio = SocketIO(app, manage_session=False)
