from app import db, login_manager
from flask_login import UserMixin

collects = db.Table('collects',
    db.Column('listId', db.Integer, db.ForeignKey('list.id'), primary_key=True),
    db.Column('msgId', db.Integer, db.ForeignKey('message.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    username = db.Column(db.String(140), primary_key=True)
    password = db.Column(db.String(140))
    email = db.Column(db.Text, unique=True)
    lists = db.relationship('List', backref='user', lazy=True)

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

class Message(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    sender = db.Column('sender', db.String(140))
    replyto = db.Column('replyto', db.String(140))
    message = db.Column('message', db.String(300))

class List(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    title = db.Column('title', db.String(256), nullable=False)

    # Owner of list
    owner = db.Column(db.Integer, db.ForeignKey('user.username', ondelete='CASCADE'), nullable=False)
    messages = db.relationship('Message', secondary=collects, lazy='subquery', backref=db.backref('list', lazy=True))
