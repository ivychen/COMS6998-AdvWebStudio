from flask import Flask, g, render_template, request, jsonify, url_for, redirect, Response
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from wtforms import Form, BooleanField, StringField, TextField, PasswordField, validators
# from TestAPI import test_api
from flask_bootstrap import Bootstrap
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

# Custom app modules
from config import Config
# from user_class import User

# === APP CONFIGURATION ===
app = Flask(__name__)
app.config.from_object(Config)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'
db = SQLAlchemy(app)
import models
# app.register_blueprint(test_api)

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
    m = models.Movie.query.all()
    series = db.session.query(models.Series.seriesId, models.Series.seriesName, func.count(models.Series.seriesId).label('count'))\
        .join(models.movieInSeries)\
        .filter_by(seriesId=models.Series.seriesId, movieId=models.Movie.id)\
        .group_by(models.Series.seriesId).all()

    seriesMovies = db.session.query(models.Series.seriesId, models.Movie)\
        .join(models.movieInSeries)\
        .filter_by(seriesId=models.Series.seriesId, movieId=models.Movie.id)\
        .order_by(models.Movie.year).all()

    return render_template('main.html', movies=m, series=series, seriesMovies=seriesMovies, range=range)

@app.route('/movie/<id>', methods=['GET'])
def movie(id):
    movie_data = models.Movie.query.get(id)
    genre = db.session.query(models.Genre.category)\
        .join(models.movieIsGenre)\
        .filter_by(movieId=movie_data.id).all()
    cast = db.session.query(models.Talent.name, models.stars)\
        .join(models.stars)\
        .filter_by(movieId=movie_data.id, talentId=models.Talent.tid).all()
    db.session.commit()

    releaseDate = datetime.strftime(movie_data.releaseDate, "%B %d, %Y")

    if movie_data.budget and movie_data.boxOfficeOpeningWeekend and movie_data.boxOfficeGross:
        budget = "{0:,.2f}".format(movie_data.budget)
        boxOfficeOpeningWeekend = "{0:,.2f}".format(movie_data.boxOfficeOpeningWeekend)
        boxOfficeGross = "{0:,.2f}".format(movie_data.boxOfficeGross)

        return render_template('movie.html', movie_data=movie_data, cast=cast, genre=genre, releaseDate=releaseDate, budget=budget, boxOfficeOpeningWeekend=boxOfficeOpeningWeekend, boxOfficeGross=boxOfficeGross)

    return render_template('movie.html', movie_data=movie_data, cast=cast, genre=genre, releaseDate=releaseDate)

@app.route('/series/<id>', methods=['GET'])
def series(id):
    series = models.Series.query.get(id)
    seriesMovies = db.session.query(models.Movie)\
        .join(models.movieInSeries)\
        .filter_by(seriesId=id, movieId=models.Movie.id)\
        .order_by(models.Movie.year).all()

    cast = db.session.query(models.Movie, models.Talent, models.stars)\
        .join(models.movieInSeries)\
        .filter_by(seriesId=id, movieId=models.Movie.id)\
        .join(models.stars)\
        .filter_by(talentId=models.Talent.tid, movieId=models.Movie.id)\
        .order_by(models.Movie.year).all()

    casting = list(set([(x.Talent.name, x.role) for x in cast]))
    chars = sorted(list(set([x.role for x in cast])))
    totalrt = sum([m.runtime for m in seriesMovies])

    return render_template('series.html', series=series, seriesMovies=seriesMovies, enumerate=enumerate, datetime=datetime, totalrt=totalrt, len=len, chars=chars, cast=cast)

@app.route('/cast/<id>', methods=['GET'])
def cast(id):
    cast_data = models.Talent.query.get(id)
    m = db.session.query(models.Movie.title, models.Movie.year, models.stars)\
        .join(models.stars)\
        .filter_by(talentId=cast_data.tid)\
        .order_by(models.Movie.year.desc()).all()

    print(m)

    return render_template('cast.html', cast=cast_data, movies=m)

@app.route('/addMovie', methods=['POST', 'GET'])
def addMovie():
    if request.method == 'POST':
        title = request.form['title']
        year = int(request.form['year'])
        genre = request.form['genre']
        runtime = int(request.form['runtime'])
        overview = request.form['overview']
        castList = list(request.form['cast'].split('\n'))
        cast = [tuple(c.split(',')) for c in castList]

        # Add movie to db
        m = models.Movie(title=title, year=year, genre=genre, runtime=runtime, overview=overview)
        db.session.add(m)
        db.session.commit()
        db.session.refresh(m)

        # Add any new cast members with their roles only if new name
        for name,role in cast:
            # Check if the actor already exists
            exists = models.Talent.query.filter_by(name=name).first()

            if not exists:
                t = models.Talent(name=name)
                db.session.add(t)
                db.session.commit()
                db.session.refresh(t)
                statement = models.stars.insert().values(movieId=m.id, talentId=t.tid, role=role)
            else:
                statement = models.stars.insert().values(movieId=m.id, talentId=exists.tid, role=role)

            db.session.execute(statement)
            db.session.commit()

        return redirect('/movie/' + str(m.id))

    return render_template('addMovie.html')

@app.route('/updateMovie/<id>', methods=['POST', 'GET'])
def updateMovie(id):
    movie_data = models.Movie.query.get(id)

    genre = db.session.query(models.Genre.category)\
        .join(models.movieIsGenre)\
        .filter_by(movieId=movie_data.id).all()

    genres = ",".join([g[0] for g in genre])

    print(genres)

    cast = db.session.query(models.Talent.name, models.stars)\
        .join(models.stars)\
        .filter_by(movieId=movie_data.id).all()
    db.session.commit()

    castDefault = ""
    for c in cast:
        castDefault = castDefault + str(c.name + "," + c.role) + "\n"

    return render_template('updateMovie.html', m=movie_data, cast=cast, castDefault=castDefault, genres=genres)

@app.route('/saveMovie', methods=['POST', 'GET'])
def save():
    if request.method == 'POST':
        # data = request.args
        # data = request.get_json(force=True)
        id = request.form['id']

        # Remove all stars in relationships that aren't in the updated cast list
        delCast = models.stars.delete(models.stars.c.movieId == id)
        db.session.execute(delCast)
        db.session.commit()

        # Update Movie information
        m = db.session.query(models.Movie).filter_by(id=id).first()
        m.title = request.form['title']
        m.year = int(request.form['year'])
        m.runtime = int(request.form['runtime'])
        m.posterURL = request.form['posterURL']
        m.releaseDate = datetime.strptime(request.form['releaseDate'], "%Y-%m-%d %H:%M:%S")
        m.countryOfOrigin = request.form['countryOfOrigin']
        m.language = request.form['language']
        m.budget = int(request.form['budget']) if request.form['budget'] else 0
        m.boxOfficeOpeningWeekend = int(request.form['boxOfficeOpeningWeekend']) if request.form['boxOfficeOpeningWeekend'] else 0
        m.boxOfficeGross = int(request.form['boxOfficeGross']) if request.form['boxOfficeGross'] else 0
        m.overview = request.form['overview']
        if request.form.get('isPlay'):
            m.isPlay = True
        else:
            m.isPlay = False
        if request.form.get('isNovel'):
            m.isNovel = True
        else:
            m.isNovel = False
        db.session.commit()

        # Update cast list
        castList = list(request.form['cast'].split('\n'))
        cast = [tuple(c.split(',')) for c in castList]

        for name,role in cast:
            # Check if the actor already exists
            exists = models.Talent.query.filter_by(name=name).first()
            if not exists:
                t = models.Talent(name=name)
                db.session.add(t)
                db.session.commit()
                db.session.refresh(t)
                statement = models.stars.insert().values(movieId=id, talentId=t.tid, role=role)
            else:
                statement = models.stars.insert().values(movieId=id, talentId=exists.tid, role=role)

            db.session.execute(statement)
            db.session.commit()

        # Update genre
        genreList = list(request.form['genre'].split(','))
        for g in genreList:
            genreExists = models.Genre.query.filter_by(category=g).first()
            movieGenreExists = db.session.query(models.movieIsGenre)\
                .filter_by(movieId=id, category=g).first()

            print("EXISTS", movieGenreExists)
            if not genreExists:
                tmp = models.Genre(category=g)
                db.session.add(tmp)
                db.session.commit()
                db.session.refresh(tmp)
                statement = models.movieIsGenre.insert().values(movieId=id, category=tmp.category)
            else:
                if not movieGenreExists:
                    statement = models.movieIsGenre.insert().values(movieId=id, category=genreExists.category)
                else:
                    statement = ""

            db.session.execute(statement)
            db.session.commit()

        return redirect('/movie/' + str(id))

    return render_template('/')

@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        title = request.form['searchTitle']
        movies = db.session.query(models.Movie).filter_by(title=title)
    else:
        movies = []

    return render_template('search.html', movies=movies)

@app.route('/deleteMovie', methods=['POST', 'GET'])
def delete():
    if request.method == 'POST':
        id = request.form['id']
        db.session.query(models.Movie).filter_by(id=id).delete()
        db.session.commit()

    return redirect('/')

# === LOGIN ====
@login_manager.user_loader
def load_user(username):
    cursor = g.conn.execute("SELECT * FROM Users U WHERE U.username=%s", username)
    data = cursor.fetchone()
    cursor.close()

    if data is None:
        return None

    return User(data[0], data[1], data[2])

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
    form = UserLoginForm(request.form)
    error = None
    if request.method == 'POST' and form.validate():
        user = models.User.query.filter_by(username=username.lower()).first()
        if user:
            if login_user(user):
                app.logger.debug('Logged in user %s', user.username)
                return redirect(url_for('/'))
        error = 'Invalid username or password.'
    return render_template('login.html', form=form, error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    error = None

    if request.method == 'POST':
        try:
            new_user = User(request.form['username'],
                      request.form['password'],
                      request.form['email'])

        except ValueError:
            error = "Username or Password is empty"

        if (not is_registered_user(new_user)):
            register_user(new_user)
            login_user(new_user)
            return redirect(url_for('main'))
        else:
            error = "Username or email taken."

    return render_template('register.html', error=error)

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
    app.run(debug=True)
