from flask import Flask, g, render_template, request, jsonify, session, url_for, redirect, Response
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from wtforms import Form, BooleanField, StringField, TextField, PasswordField, validators
from flask_socketio import SocketIO, send, disconnect
# from flask_session import Session

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import functools
import dateutil.parser as dt

# Custom app modules
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# Session(app)
db = SQLAlchemy(app)
socketio = SocketIO(app, manage_session=False)
import models

# FORMS
class UserLoginForm(Form):
    username = TextField('Username', [validators.Required(), validators.Length(min=4, max=25)])
    password = PasswordField('Password', [validators.Required(), validators.Length(min=6, max=200)])
    email = TextField('Email Address', [validators.Required(), validators.Length(min=4, max=25)])

class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [
        validators.DataRequired()
        # validators.EqualTo('confirm', message='Passwords must match')
    ])

# Aux
def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped

# Define routes
@app.route('/', methods=['POST', 'GET'])
def main():
    if current_user.is_authenticated:
        messages = models.History.query.all()
    else:
        messages = []

    return render_template('main.html', messages=messages)

@app.route('/messages/<username>', methods=['POST', 'GET'])
# @login_required
def messages(username):
    messages = models.History.query.filter_by(sender=username).all()
    return render_template('messages.html', messages=messages)

# === LOGIN ====
@login_manager.user_loader
def load_user(username):
    try:
        return models.User.query.get(username)
    except:
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))

    form = UserLoginForm(request.form)
    error = None
    if request.method == 'POST':
        user = models.User.query.filter_by(username=request.form['username'].lower(), password=request.form['password']).first()
        if user:
            login_user(user, remember=True)
            print('Logged in user', user.username)
            return redirect(url_for('main'))
        else:
            error = 'Invalid username or password.'
    return render_template('login.html', form=form, error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    error = None
    if request.method == 'POST':
        exist = models.User.query.filter_by(username=request.form['username'].lower()).first()
        if exist:
            error = "Username is taken."
        else:
            user = models.User(username=request.form['username'].lower(), password=request.form['password'], email=request.form['email'])
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            return redirect(url_for('login'))
    return render_template('register.html', form=form, error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main'))


# Sockets
# @socketio.on('connect')
# def connect_handler():
#     print("CURRENT USER", current_user)
#     if current_user.is_authenticated:
#         emit('my response',
#              {'message': '{0} has joined'.format(current_user.name)},
#              broadcast=True)
#     else:
#         return False  # not allowed here

@socketio.on('message')
def handleMessage(msg):
    print('Message: ' + msg['message'])
    time = dt.parse(msg['timestamp'])
    message = models.History(message=msg['message'], timestamp=time, sender=msg['sender'], replyto=msg['replyto'])
    db.session.add(message)
    db.session.commit()
    send(msg, broadcast=True)



if __name__ == '__main__':
	socketio.run(app)
