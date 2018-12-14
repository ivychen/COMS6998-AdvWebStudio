from flask import Flask, g, render_template, request, jsonify, session, url_for, redirect, Response
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from datetime import datetime
from flask_socketio import SocketIO, send, disconnect

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import aliased
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
    stock = models.Product.query.order_by(models.Product.name.asc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main', page=stock.next_num) \
        if stock.has_next else None
    prev_url = url_for('main', page=stock.prev_num) \
        if stock.has_prev else None

    user = aliased(models.User)
    categories = db.session.query(models.User_own_product, models.Product.category).join(models.Product).join(user, models.User).all()

    popc = set([c.category for c in categories])

    # check if current user is the logged in username
    if current_user.is_authenticated:
        username = current_user.username
        user = aliased(models.User)
        products = db.session.query(models.User_own_product, models.Product).join(models.Product).join(user, models.User).filter(user.username==username).all()

        categories = db.session.query(models.User_own_product, models.Product.category).join(models.Product).join(user, models.User).filter(user.username==username).all()

        uniqueCategories = set([c.category for c in categories])

        return render_template('shelf.html', products=products, username=current_user.username, float=float, categories=uniqueCategories, popCategories=popc)
    else:
        return render_template('main.html', products=stock.items, next_url=next_url,prev_url=prev_url,popCategories=popc)

@app.route('/browse', methods=['POST', 'GET'])
def browse():
    page = request.args.get('page', 1, type=int)
    stock = models.Product.query.order_by(models.Product.name.asc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('browse', page=stock.next_num) \
        if stock.has_next else None
    prev_url = url_for('browse', page=stock.prev_num) \
        if stock.has_prev else None

    allCategories = models.Product.query.with_entities(models.Product.category).distinct().all()

    allc = [c.category for c in allCategories]

    return render_template('products.html', products=stock.items, next_url=next_url, prev_url=prev_url, allCategories=allc)

@app.route('/user/<username>', methods=['POST', 'GET'])
def user(username):
    user = models.User.query.filter_by(username=username).first()

    return render_template('user.html', user=user)


@app.route('/product/<id>', methods=['POST', 'GET'])
def product(id):
    product = models.Product.query.filter_by(id=id).first()

    if current_user.is_authenticated:
        inShelf = models.User_own_product.query.filter_by(username=current_user.username, productId=id).first()
        return render_template('product.html', product=product, inShelf=inShelf)

    return render_template('product.html', product=product, inShelf=False)


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


@app.route('/shelf/remove/<username>/<id>', methods=['POST', 'GET'])
@login_required
def removeProduct(username, id):
    models.User_own_product.query.filter(models.User_own_product.username == username, models.User_own_product.productId == int(id)).delete()
    db.session.commit()

    return redirect(url_for("main"))

@app.route("/shelf/add", methods=['POST'])
def add_to_shelf():
    if request.method == "POST":
        prod = models.User_own_product(username=current_user.username, productId=request.form['id'], quantity=request.form['quantity'])
        db.session.add(prod)
        db.session.commit()
        return redirect(url_for('main'))

    return redirect(url_for('main'))

@app.route("/shelf/update", methods=['POST'])
def update_to_shelf():
    prod = models.User_own_product.query.filter_by(username=current_user.username, productId=request.form['id']).first()
    prod.quantity = int(request.form['quantity'])
    db.session.merge(prod)
    db.session.flush()
    db.session.commit()

    return redirect(url_for('main'))

@app.route("/shelf/remove/<id>", methods=['POST'])
def remove_from_shelf(id):
    # statement = models.owns.delete(models.owns.productId==item_id, username=current_user.username)

    prod = models.User_own_product.query.filter_by(username=current_user.username, productId=id).first()
    db.session.delete(prod)
    db.session.flush()
    db.session.commit()

    return redirect(url_for('main'))

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
        categories = models.Product.query.filter(models.Product.category.ilike("%" + search + "%")).all()

        for p in products:
            if p.id not in productSet:
                productSet.add(p.id)
                allProducts.append(p)

        for p in brands:
            if p.id not in productSet:
                productSet.add(p.id)
                allProducts.append(p)

        for p in categories:
            if p.id not in productSet:
                productSet.add(p.id)
                allProducts.append(p)
    else:
        allProducts = []
        search = "No results for search"

    return render_template('search.html', search=search, products=allProducts, len=len)


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

@app.route('/autocomplete_all',methods=['POST', 'GET'])
def autocomplete_all():
    search = request.args.get('term')
    if not search:
        search = ""

    results = []

    query = models.Product.query.filter(models.Product.category.ilike("%" + search + "%")).with_entities(models.Product.category).distinct().all()
    categories = [res.category for res in query]

    query = models.Product.query.filter(models.Product.brand.ilike("%" + search + "%")).with_entities(models.Product.brand).distinct().all()
    brands = [res.brand for res in query]

    query = models.Product.query.filter(models.Product.name.ilike("%" + search + "%")).with_entities(models.Product.name).distinct().all()
    names = [res.name for res in query]

    results.extend(categories)
    results.extend(brands)
    results.extend(names)

    return jsonify(matching_results=results)

@app.route('/productDetails',methods=['POST', 'GET'])
def productDetails():
    prodId = request.args.get('id')
    result = models.Product.query.filter_by(id=int(prodId)).first()
    res = {"id" : result.id,
        "brand" : result.brand,
        "name" : result.name,
        "description" : result.description,
        "imgsrc" : result.imgsrc,
        "category" : result.category}
    return jsonify(result=[res])

@app.route('/rateProduct', methods=['POST', 'GET'])
def rateProduct():
    rating = request.json.get('rating')
    username = request.json.get('username')
    productId = int(request.json.get('productId'))

    record = models.User_own_product.query.filter_by(username=username, productId=productId).first()
    record.rating = rating
    db.session.merge(record)
    db.session.flush()
    db.session.commit()

    return jsonify(result=True)

@app.route('/recommend', methods=['POST', 'GET'])
def recommend():
    category = request.json.get('category')
    # get top 5 products in category based on community rating

    prod = aliased(models.Product)
    own = aliased(models.User_own_product)

    products = db.session.query(models.User_own_product.productId, func.avg(models.User_own_product.rating).label('rate')).join(models.Product).filter(models.Product.id==models.User_own_product.productId, models.Product.category==category).group_by(models.User_own_product.productId).order_by(func.avg(models.User_own_product.rating).desc()).all()

    results = []
    for p in products:
        result = models.Product.query.filter_by(id=int(p.productId)).first()
        res = {"id" : result.id,
            "brand" : result.brand,
            "name" : result.name,
            "description" : result.description,
            "imgsrc" : result.imgsrc,
            "category" : result.category,
            "rating" : p.rate}
        results.append(res)

    # empty
    if not results:
        products = models.Product.query.filter_by(category=category).limit(6).all()

        for p in products:
            res = {"id" : p.id,
                "brand" : p.brand,
                "name" : p.name,
                "description" : p.description,
                "imgsrc" : p.imgsrc,
                "category" : p.category,
                "rating" : None}
            results.append(res)

        return jsonify(recommendations=results, empty=True)

    return jsonify(recommendations=results, empty=False)


if __name__ == '__main__':
	# socketio.run(app)
    app.run(debug=True)
