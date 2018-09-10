from flask import Flask, g, render_template, request, jsonify, url_for, redirect, Response
# from TestAPI import test_api
from flask_bootstrap import Bootstrap
import uuid
import pickle
from data import Movies

def createApp():
    app = Flask(__name__)
    Bootstrap(app)
    return app
    # app.register_blueprint(test_api)

app = createApp()
movies = Movies('movies.pkl')
# movies.addMovie('Crazy Rich Asians', '2018', 'This contemporary romantic comedy, based on a global bestseller, follows native New Yorker Rachel Chu to Singapore to meet her boyfriend\'s family.', ['Constance Wu', 'Henry Golding', 'Michelle Yeoh', 'Awkwafina', 'Gemma Chan'])

# Define routes
@app.route('/')
def main():
    # m = Movie.query.all()
    m = movies.dic.values()
    return render_template('main.html', movies=m)

@app.route('/movie/<id>', methods=['GET'])
def movie(id):
    # movie_data = Movie.query.get(id)
    movie_data = movies.dic[id]
    print(movie_data)
    return render_template('movie.html', movie_data=movie_data)

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
        movies.deleteMovie(id)

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
