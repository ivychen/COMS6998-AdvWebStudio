from app import db

stars = db.Table(
                'stars',
                db.Column('movieId', db.Integer, db.ForeignKey('movie.id', ondelete="CASCADE"), primary_key=True),
                db.Column('talentId', db.Integer, db.ForeignKey('talent.tid', ondelete="CASCADE"), primary_key=True),
                db.Column('role', db.String(140), nullable=False)
                )

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String(140), nullable=False)
    runtime = db.Column(db.Integer)
    overview = db.Column(db.Text)
    talent = db.relationship('Talent', secondary=stars, backref=db.backref('movie', cascade='all', lazy=True), lazy='subquery')

    def __repr__(self):
        return '<Movie {}, {}, {}>'.format(self.title, self.year, self.overview)

class Talent(db.Model):
    tid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False, unique=True)
    # movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)

    def __repr__(self):
        return '<Talent {}>'.format(self.name)

# https://stackoverflow.com/questions/38654624/flask-sqlalchemy-many-to-many-relationship-new-attribute
