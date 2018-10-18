from flask import Flask, g, render_template, request, jsonify, url_for, redirect, Response
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from wtforms import Form, BooleanField, StringField, TextField, PasswordField, validators
from flask_socketio import SocketIO, send

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

# Custom app modules
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)
socketio = SocketIO(app)
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
    # confirm = PasswordField('Repeat Password')
    # accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])


# Define routes
@app.route('/', methods=['POST', 'GET'])
@login_required
def main():
    messages = models.History.query.all()
    return render_template('main.html', messages=messages)

@socketio.on('message')
def handleMessage(msg):
    print('Message: ' + msg)
    if current_user.is_authenticated():
        time = datetime.datetime()
        message = models.History(message=msg, timestamp=time.strftime('%Y-%m-%d %H:%M:%S'), sender=current_user.username)
        db.session.add(message)
        db.session.commit()
        send(msg, broadcast=True)
    else:
        print("Need to sign in")

# === LOGIN ====
@login_manager.user_loader
def load_user(username):
    try:
        return models.User.query.get(username)
    except:
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated():
        return redirect(url_for('main'))

    form = UserLoginForm(request.form)
    error = None
    if request.method == 'POST':
        user = models.User.query.filter_by(username=request.form['username'].lower(), password=request.form['password']).first()
        if user:
            login_user(user):
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
            flash('Thanks for registering')
            return redirect(url_for('login'))
    return render_template('register.html', form=form, error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main'))

if __name__ == '__main__':
	socketio.run(app)
