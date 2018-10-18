from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    username = db.Column(db.String(140), primary_key=True)
    password = db.Column(db.String(140))
    email = db.Column(db.Text, unique=True)

    def get_id(self):
        return str(self.username)

    def __repr__(self):
        return "<User {} {}".format(self.username, self.email)

class History(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    sender = db.Column('sender', db.String(140))
    replyto = db.Column('replyto', db.String(140))
    message = db.Column('message', db.String(300))
