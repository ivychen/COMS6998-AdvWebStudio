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
login_manager.login_view = '/'
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
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])


# Define routes
@app.route('/', methods=['POST', 'GET'])
def main():
    messages = models.History.query.all()
    return render_template('main.html', messages=messages)

@socketio.on('message')
def handleMessage(msg):
    print('Message: ' + msg)
    if current_user.is_authenticated:
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
    return models.User.query.get(username)

def authenticate_user(user):
    cursor = g.conn.execute("SELECT * FROM Users U WHERE U.username=%s", user.username)
    data = cursor.fetchone()
    cursor.close()

    if data[1] == user.password:
        return True
    else:
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))

    form = UserLoginForm(request.form)
    error = None
    if request.method == 'POST':
        user = models.User.query.filter_by(username=request.form['username'].lower()).first()
        if user:
            if login_user(user):
                # app.logger.debug('Logged in user %s', user.username)
                return redirect(url_for('main'))
        error = 'Invalid username or password.'
    return render_template('login.html', form=form, error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        user = models.User(form.username.data, form.password.data, form.email.data)
        db_session.add(user)
        # flash('Thanks for registering')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

def register_user(user):
    cursor = g.conn.execute("INSERT INTO Users (username, password, email) VALUES (%s, %s, %s)", (user.username, user.password, user.email))

    cursor.close()

def is_registered_user(user):
    cursor = g.conn.execute("SELECT * FROM Users U WHERE U.username=%s", (user.username, ))
    data = cursor.fetchone()
    cursor.close()

    if data:
        return True
    else:
        return False

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main'))

if __name__ == '__main__':
	socketio.run(app)
