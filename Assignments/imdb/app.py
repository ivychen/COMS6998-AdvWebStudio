from flask import Flask, g, render_template, request, jsonify, url_for, redirect, Response
# from TestAPI import test_api
from flask_bootstrap import Bootstrap
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Custom app modules
from config import Config

# === APP CONFIGURATION ===
app = Flask(__name__)
app.config.from_object(Config)
Bootstrap(app)
db = SQLAlchemy(app)
import models
# app.register_blueprint(test_api)

# Define routes
@app.route('/', methods=['POST', 'GET'])
def main():
    m = models.Movie.query.all()
    return render_template('main.html', movies=m)

@app.route('/movie/<id>', methods=['GET'])
def movie(id):
    movie_data = models.Movie.query.get(id)
    genre = db.session.query(models.Genre.category)\
        .join(models.movieIsGenre)\
        .filter_by(movieId=movie_data.id).all()
    cast = db.session.query(models.Talent.name, models.stars)\
        .join(models.stars)\
        .filter_by(movieId=movie_data.id).all()
    db.session.commit()

    releaseDate = datetime.strftime(movie_data.releaseDate, "%B %d, %Y")

    if movie_data.budget and movie_data.boxOfficeOpeningWeekend and movie_data.boxOfficeGross:
        budget = "{0:,.2f}".format(movie_data.budget)
        boxOfficeOpeningWeekend = "{0:,.2f}".format(movie_data.boxOfficeOpeningWeekend)
        boxOfficeGross = "{0:,.2f}".format(movie_data.boxOfficeGross)

        return render_template('movie.html', movie_data=movie_data, cast=cast, genre=genre, releaseDate=releaseDate, budget=budget, boxOfficeOpeningWeekend=boxOfficeOpeningWeekend, boxOfficeGross=boxOfficeGross)

    return render_template('movie.html', movie_data=movie_data, cast=cast, genre=genre, releaseDate=releaseDate)

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

if __name__ == '__main__':
    app.run(debug=True)
