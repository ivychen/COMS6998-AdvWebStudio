from flask import Flask, g, render_template, request, jsonify, session, url_for, redirect, Response
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_socketio import SocketIO, send, disconnect

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import functools
import dateutil.parser as dt

from config import app, db, login_manager, socketio
import models

# Aux
def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped

# Define routes
@app.route('/', methods=['POST', 'GET'])
def main():
    page = request.args.get('page', 1, type=int)
    products = models.Product.query.order_by(models.Product.name.asc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main', page=products.next_num) \
        if products.has_next else None
    prev_url = url_for('main', page=products.prev_num) \
        if products.has_prev else None

    return render_template('main.html', products=products.items, next_url=next_url, prev_url=prev_url)

@app.route('/shelf/<username>', methods=['POST', 'GET'])
def products(username):
    products = models.Product.query.filter(models.Product.users.any(username=username)).all()

    print("===PRODUCTS", products)

    return render_template('shelf.html', products=products)

@app.route('/product/<id>', methods=['POST', 'GET'])
def product(id):
    product = models.Product.query.filter_by(id=id).first()
    # inShelf = db.session.query(models.owns).filter_by(username=current_user.username, productId=id).first()

    inShelf = models.User_own_product.query.filter_by(username=current_user.username, productId=id).first()

    return render_template('product.html', product=product, inShelf=inShelf)

@app.route('/newProduct', methods=['POST', 'GET'])
def newProduct():
    if request.method == "POST":
        product = models.Product(
            brand=request.form['brand'],
            category=request.form['category'],
            name=request.form['name'],
            imgsrc=request.form['imgsrc'],
            description=request.form['description']
        )
        db.session.add(product)
        db.sesion.commit()
        db.session.refresh(product)
        return redirect('/product/' + str(product.id))

    return render_template('newProduct.html')

@app.route("/shelf/add", methods=['POST'])
def add_to_shelf():
    if request.method == "POST":
        # statement = models.owns.insert().values(username=current_user.username, productId=request.form['id'], quantity=request.form['quantity'])

        # db.session.execute(statement)
        prod = models.User_own_product(username=current_user.username, productId=request.form['id'], quantity=request.form['quantity'])
        db.session.add(prod)
        db.session.commit()

    return redirect(request.referrer or url_for('main'))

@app.route("/shelf/update", methods=['POST'])
def update_to_shelf():
    # statement = models.owns.insert().values(username=current_user.username, productId=request.form['product'], quantity=request.form['quantity'])

    # statement = update(models.owns).where()

    # db.session.execute(statement)
    prod = models.User_own_product.query.filter_by(username=current_user.username, productId=request.form['id']).first()
    prod.quantity = int(request.form['quantity'])
    db.session.merge(prod)
    db.session.flush()
    db.session.commit()

    return redirect(request.referrer or url_for('main'))

@app.route("/shelf/remove/<id>", methods=['POST'])
def remove_from_shelf(id):
    # statement = models.owns.delete(models.owns.productId==item_id, username=current_user.username)

    prod = models.User_own_product.query.filter_by(username=current_user.username, productId=id).first()
    db.session.delete(prod)
    db.session.flush()
    db.session.commit()

    return redirect(request.referrer or url_for('main'))

@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        # search query can include:
        # - product name
        # - product brand
        search = request.form['query']
        productSet = set()
        allProducts = []
        products = models.Product.query.filter(models.Product.name.ilike("%" + search + "%")).all()
        brands = models.Product.query.filter(models.Product.brand.ilike("%" + search + "%")).all()

        for p in products:
            if p.id not in productSet:
                productSet.add(p.id)
                allProducts.append(p)

        for p in brands:
            if p.id not in productSet:
                productSet.add(p.id)
                allProducts.append(p)
    else:
        allProducts = []
        search = "No results for search"

    return render_template('search.html', search=search, products=allProducts, len=len)

@app.route('/messages/<username>', methods=['POST', 'GET'])
# @login_required
def messages(username):
    page = request.args.get('page', 1, type=int)
    messages = models.Message.query.filter_by(sender=username).order_by(models.Message.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('messages', username=username, page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('messages', username=username, page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items, next_url=next_url, prev_url=prev_url)

@app.route('/saved', methods=['POST', 'GET'])
# @login_required
def saved():
    page = request.args.get('page', 1, type=int)
    listId = models.List.query.filter_by(owner=current_user.username).first()
    # saved = models.List.query.filter_by(owner=current_user.username).first().messages
    messages = db.session.query(models.Message)\
        .join(models.collects)\
        .filter_by(listId=listId.id)\
        .order_by(models.Message.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('saved', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('saved', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('saved.html', messages=messages.items, next_url=next_url, prev_url=prev_url)


# === LOGIN ====
@login_manager.user_loader
def load_user(username):
    try:
        return models.User.query.get(username)
    except:
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))

    error = None
    if request.method == 'POST':
        user = models.User.query.filter_by(username=request.form['username'].lower(), password=request.form['password']).first()
        if user:
            login_user(user, remember=True)
            print('Logged in user', user.username)
            return redirect(url_for('main'))
        else:
            error = 'Invalid username or password.'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        exist = models.User.query.filter_by(username=request.form['username'].lower()).first()
        if exist:
            error = "Username is taken."
        else:
            # Create user and saved msg list
            user = models.User(username=request.form['username'].lower(), password=request.form['password'], email=request.form['email'])
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main'))

# Sockets
# @socketio.on('connect')
# def connect_handler():
#     print("CURRENT USER", current_user)
#     if current_user.is_authenticated:
#         emit('my response',
#              {'message': '{0} has joined'.format(current_user.name)},
#              broadcast=True)
#     else:
#         return False  # not allowed here

# @socketio.on('message')
# def handleMessage(msg):
#     time = dt.parse(msg['timestamp'])
#     message = models.Message(message=msg['message'], timestamp=time, sender=msg['sender'], replyto=msg['replyto'])
#     db.session.add(message)
#     db.session.commit()
#     send(msg, broadcast=True)
#
# @socketio.on('save')
# def handleSave(msg):
#     ls = models.List.query.filter_by(owner=msg['user']).first()
#     savedMsg = models.Message.query.get(msg['messageId'])
#
#     statement = models.collects.insert().values(listId=ls.id, msgId=msg['messageId'])
#     db.session.execute(statement)
#     db.session.commit()
#     # send(msg, broadcast=True)

# AJAX
@app.route('/autocomplete',methods=['POST', 'GET'])
def autocomplete():
    search = request.args.get('term')
    if not search:
        search = ""
    query = models.Product.query.filter(models.Product.brand.ilike("%" + search + "%")).with_entities(models.Product.brand).distinct().all()
    results = [res.brand for res in query]
    return jsonify(matching_results=results)

@app.route('/autocomplete_category',methods=['POST', 'GET'])
def autocomplete_category():
    search = request.args.get('term')
    if not search:
        search = ""
    query = models.Product.query.filter(models.Product.category.ilike("%" + search + "%")).with_entities(models.Product.category).distinct().all()
    results = [res.category for res in query]
    return jsonify(matching_results=results)

if __name__ == '__main__':
	socketio.run(app)
