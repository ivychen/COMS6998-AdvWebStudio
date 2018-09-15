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
    return render_template('addMovie.html')

@app.route('/saveMovie', methods=['POST', 'GET'])
def save():
    send_back = {
        'status': 'failed'
    }

    if request.method == 'POST':
        # data = request.args
        # data = request.get_json(force=True)

        cast = list(request.form['cast'].split('\n'))
        movies.addMovie(title=request.form['title'], year=request.form['year'], desc=request.form['description'], cast=cast)
        # db.session.add(newMovie)
        # db.session.commit()

        send_back['status'] = 'success'

    return redirect('/addMovie')

@app.route('/deleteMovie', methods=['POST', 'GET'])
def delete():
    if request.method == 'POST':
        id = request.form['id']
        db.session.query(models.Movie).filter_by(id=id).delete()
        db.session.commit()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
