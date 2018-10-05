from app import db

# Association Tables
stars = db.Table(
    'stars',
    db.Column('movieId', db.Integer, db.ForeignKey('movie.id', ondelete="CASCADE"), primary_key=True),
    db.Column('talentId', db.Integer, db.ForeignKey('talent.tid', ondelete="CASCADE"), primary_key=True),
    db.Column('role', db.String(140), primary_key=True)
    )

movieIsGenre = db.Table(
    'movieIsGenre',
    db.Column('movieId', db.Integer, db.ForeignKey('movie.id', ondelete="CASCADE"), primary_key=True),
    db.Column('category', db.Text, db.ForeignKey('genre.category', ondelete="CASCADE"), primary_key=True)
    )

movieWinsAward = db.Table(
    'movieWinsAward',
    db.Column('movieId', db.Integer, db.ForeignKey('movie.id', ondelete="CASCADE"), primary_key=True),
    db.Column('awardId', db.Integer, db.ForeignKey('award.id', ondelete="CASCADE"), primary_key=True)
    )

talentWinsAward = db.Table(
    'talentWinsAward',
    db.Column('talentId', db.Integer, db.ForeignKey('talent.tid', ondelete="CASCADE"), primary_key=True),
    db.Column('awardId', db.Integer, db.ForeignKey('award.id', ondelete="CASCADE"), primary_key=True)
    )

movieInSeries = db.Table(
    'movieInSeries',
    db.Column('seriesId', db.Integer, db.ForeignKey('series.seriesId', ondelete="CASCADE"), primary_key=True),
    db.Column('movieId', db.Integer, db.ForeignKey('movie.id', ondelete="CASCADE"), primary_key=True),
    db.Column('sequence', db.Integer, primary_key=True)
)

# Models
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    runtime = db.Column(db.Integer)
    overview = db.Column(db.Text)
    posterURL = db.Column(db.Text)
    releaseDate = db.Column(db.DateTime)
    countryOfOrigin = db.Column(db.Text)
    language = db.Column(db.String(70), default="English")
    budget = db.Column(db.Integer)
    boxOfficeGross = db.Column(db.Integer)
    boxOfficeOpeningWeekend = db.Column(db.Integer)
    isPlay = db.Column(db.Boolean, unique=True, default=False)
    isNovel = db.Column(db.Boolean, unique=True, default=False)

    # Relationships
    talent = db.relationship('Talent', secondary=stars, backref=db.backref('movie', cascade='all', lazy=True), lazy='subquery')
    genre = db.relationship('Genre', secondary=movieIsGenre, backref=db.backref('movie', cascade='all', lazy=True), lazy='subquery')
    award = db.relationship('Award', secondary=movieWinsAward, backref=db.backref('movie', cascade='all', lazy=True), lazy='subquery')

    def __repr__(self):
        return '<Movie {}, {}>'.format(self.title, self.year)

class Talent(db.Model):
    tid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False, unique=True)

    # Relationships
    award = db.relationship('Award', secondary=talentWinsAward, backref=db.backref('talent', cascade='all', lazy=True), lazy='subquery')

    def __repr__(self):
        return '<Talent {}>'.format(self.name)

class Genre(db.Model):
    category = db.Column(db.Text, primary_key=True)

class Series(db.Model):
    seriesId = db.Column(db.Integer, primary_key=True)
    seriesName = db.Column(db.Text)

    # Relationships
    movie = db.relationship('Movie', secondary=movieInSeries, backref=db.backref('series', cascade='all', lazy=True), lazy='subquery')

    def __repr__(self):
        return '<Series {}>'.format(self.seriesName)

class Award(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.Text, nullable=False)
    award = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Text)

    def __repr__(self):
        return "<Award {} {} {}".format(self.event, self.award, self.year)

# https://stackoverflow.com/questions/38654624/flask-sqlalchemy-many-to-many-relationship-new-attribute
