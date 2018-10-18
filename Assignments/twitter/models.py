from app import db, login_manager
from flask_login import UserMixin

class User(UserMixin, db.Model):
    username = db.Column(db.String(140), primary_key=True)
    password = db.Column(db.String(140))
    email = db.Column(db.Text, unique=True)

    def __init__(self , username ,password , email):
        self.username = username
        self.password = password
        self.email = email

    def get_id(self):
        return str(self.username)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def __repr__(self):
        return "<User {} {}".format(self.username, self.email)

class History(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    sender = db.Column('sender', db.String(140))
    replyto = db.Column('replyto', db.String(140))
    message = db.Column('message', db.String(300))
