from flask import Flask, g, render_template, request, jsonify, url_for, redirect, Response
# from TestAPI import test_api
from flask_bootstrap import Bootstrap
import uuid
import pickle
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
@app.route('/')
def main():
    m = models.Movie.query.all()
    return render_template('main.html', movies=m)

@app.route('/movie/<id>', methods=['GET'])
def movie(id):
    movie_data = models.Movie.query.get(id)
    cast = db.session.query(models.Talent.name, models.stars)\
        .join(models.stars)\
        .filter_by(movieId=movie_data.id).all()
    db.session.commit()

    return render_template('movie.html', movie_data=movie_data, cast=cast)

@app.route('/cast/<id>', methods=['GET'])
def cast(id):
    cast_data = models.Talent.query.get(id)
    m = db.session.query(models.Movie.title, models.stars)\
        .join(models.stars)\
        .filter_by(talentId=cast_data.tid).all()

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
            t = models.Talent(name=name)
            # Check if the actor already exists
            exists = models.Talent.query.filter_by(name=name).first()
            if not exists:
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
    cast = db.session.query(models.Talent.name, models.stars)\
        .join(models.stars)\
        .filter_by(movieId=movie_data.id).all()
    db.session.commit()

    castDefault = ""
    for c in cast:
        castDefault = castDefault + str(c.name + "," + c.role) + "\n"

    return render_template('updateMovie.html', m=movie_data, cast=cast, castDefault=castDefault)

@app.route('/saveMovie', methods=['POST', 'GET'])
def save():
    # send_back = {
    #     'status': 'failed'
    # }

    if request.method == 'POST':
        # data = request.args
        # data = request.get_json(force=True)
        id = request.form['id']

        # Remove all stars in relationships that aren't in the updated cast list
        delCast = models.stars.delete(models.stars.c.movieId == id)
        db.session.execute(delCast)
        db.session.commit()

        m = db.session.query(models.Movie).filter_by(id=id).first()
        m.title = request.form['title']
        m.year = int(request.form['year'])
        m.genre = request.form['genre']
        m.runtime = int(request.form['runtime'])
        m.overview = request.form['overview']
        db.session.commit()

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

        # db.session.add(newMovie)
        # db.session.commit()
        # send_back['status'] = 'success'

        return redirect('/movie/' + str(id))

    return render_template('/')

@app.route('/deleteMovie', methods=['POST', 'GET'])
def delete():
    if request.method == 'POST':
        id = request.form['id']
        db.session.query(models.Movie).filter_by(id=id).delete()
        db.session.commit()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
