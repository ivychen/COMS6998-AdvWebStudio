from config import db, login_manager
from flask_login import UserMixin

collects = db.Table('collects',
    db.Column('listId', db.Integer, db.ForeignKey('list.id'), primary_key=True),
    db.Column('productId', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

class User_own_product(db.Model):
    __tablename__= 'user_own_product'
    username = db.Column(db.String(140), db.ForeignKey('user.username'), primary_key=True)
    productId = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    quantity = db.Column(db.Integer)
    rating = db.Column(db.String(5))

    user = db.relationship('User', back_populates="products")
    product = db.relationship('Product', back_populates="users")

tags = db.Table('tags',
    db.Column('tag', db.Integer, db.ForeignKey('tag.tag'), primary_key=True),
    db.Column('productId', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

concerns = db.Table('concerns',
    db.Column('concernId', db.Integer, db.ForeignKey('concern.concern'), primary_key=True),
    db.Column('username', db.Integer, db.ForeignKey('user.username'), primary_key=True)
)

class User(UserMixin, db.Model):
    username = db.Column(db.String(140), primary_key=True)
    password = db.Column(db.String(140))
    email = db.Column(db.Text, unique=True)
    skinType = db.Column(db.String(140))
    lists = db.relationship('List', backref='user', lazy=True)
    # products = db.relationship('Product', secondary=owns, lazy='subquery', backref=db.backref('users', lazy=True))
    products = db.relationship("User_own_product", back_populates="user")

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

class Product(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    brand = db.Column('brand', db.String(140))
    name = db.Column('name', db.Text)
    description = db.Column('description', db.Text)
    imgsrc = db.Column(db.Text)
    category = db.Column(db.String(200))

    tags = db.relationship('Tag', secondary=tags, lazy='subquery', backref=db.backref('products', lazy=True))

    users = db.relationship("User_own_product", back_populates="product")

class Tag(db.Model):
    tag = db.Column(db.String(140), primary_key=True)
    category = db.Column(db.String(140))

class Concern(db.Model):
    concern = db.Column(db.String(140), primary_key=True)

class List(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    title = db.Column('title', db.String(256), nullable=False)

    # Owner of list
    owner = db.Column(db.Integer, db.ForeignKey('user.username', ondelete='CASCADE'), nullable=False)
    products = db.relationship('Product', secondary=collects, lazy='subquery', backref=db.backref('list', lazy=True))

# owns = db.Table('owns',
#     db.Column('username', db.String(140), db.ForeignKey('user.username'), primary_key=True),
#     db.Column('productId', db.Integer, db.ForeignKey('product.id'), primary_key=True),
#     db.Column('quantity', db.Integer)
# )
