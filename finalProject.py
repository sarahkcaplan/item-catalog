from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm	import sessionmaker
from database_setup import Base, Restaurant, MenuItem

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json

from flask import make_response
import requests

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# JSON endpoints
@app.route('/restaurants/JSON')
def allRestaurantsJSON():
	restaurants = session.query(Restaurant).all()
	return jsonify(Restaurant=[restaurant.serialize for restaurant in restaurants])


@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
	restaurant = session.query(Restaurant).first()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	return jsonify(MenuItems=[i.serialize for i in items])

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def MenuItemJSON(restaurant_id, menu_id):
	item = session.query(MenuItem).filter_by(restaurant_id = restaurant_id, id = menu_id).one()
	return jsonify(MenuItems=item.serialize)

# Routing for app pages

@app.route('/login/', methods=['GET', 'POST'])
def showLogin():
	if request.method == "GET":
		# Anti forgery state tokens
		state = ''.join(random.choice(string.ascii_uppercase + string.digits)
						for x in xrange(32))
		# Store state in login_session object under the name "state"
		login_session['state'] = state
		return render_template('login.html', STATE=state)

@app.route('/gconnect/', methods=["POST"])
def gconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	code = request.data
	try:
		# Upgrate the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = "postmessage"
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps("Failed to upgrade the authorization code."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Check that the access token is valid
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()
	result = json.loads(h.requests(url, 'GET')[1])
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		response = make_response(json.dumpts(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'
	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's uer ID does not match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		reponse = make_response(json.dumps("Token's client ID does not match the app's"), 401)
		print "Token's client ID does not match the app's."
		reponse.headers['Content-Type'] = 'application/json'
		return response
	# Check to see if user is already logged in
	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'), 200)
		response.headers['Content-Type'] = 'application/json'

	# Store the access token in the session for later use.
	login_session['credentials'] = credentials
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt':'json'}
	answer = request.get(userinfo_url, params=params)
	data = json.loads(answer.text)

	login_session['username'] = data["name"]
	login_session['picture'] = data["picture"]
	login_session['email'] = data["email"]

	output = ''
	output += "Welcome,"
	output += login_session['username']
	return output

@app.route('/')
@app.route('/restaurants/')
def allRestaurants():
	restaurants = session.query(Restaurant).all()
	return render_template('index.html', restaurants=restaurants)

@app.route('/restaurant/<int:restaurant_id>/')
def restaurantAllMenuItems(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id)
	return render_template('restaurant_all_menu_items.html', restaurant=restaurant, items=items)

@app.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def restaurantEdit(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == "POST":
		if request.form["name"]:
			editedRestaurant = restaurant
			editedRestaurant.name = request.form["name"]
			session.add(editedRestaurant)
			session.commit()
			return redirect(url_for('restaurantAllMenuItems', restaurant_id = restaurant_id))
	else:
		return render_template('restaurant_edit.html', restaurant = restaurant)

@app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def restaurantDelete(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == "POST":
		deleteRestaurant = restaurant
		session.delete(deleteRestaurant)
		session.commit()
		return redirect(url_for('allRestaurants'))
	else:
		return render_template('restaurant_delete.html', restaurant = restaurant)

@app.route('/restaurant/new/', methods=['GET', 'POST'])
def restaurantNew():
	restaurants = session.query(Restaurant).all()
	if request.method == "POST":
		if request.form["name"]:
			restaurantNew = Restaurant(name = request.form["name"])
			session.add(restaurantNew)
			session.commit()
			return redirect(url_for('allRestaurants', restaurants=restaurants))
	else:
		return render_template('restaurant_new.html')

@app.route('/restaurant/<int:restaurant_id>/new/', methods=['GET', 'POST'])
def itemNew(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == "POST":
		newItem = MenuItem(name = request.form["name"],
						   restaurant_id = restaurant_id)
		session.add(newItem)
		session.commit()
		flash("New menu item created!")
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('item_new.html', restaurant_id = restaurant_id, restaurant = restaurant)


@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET', 'POST'])
def itemEdit(restaurant_id, menu_id):
	restaurant = session.query(MenuItem).filter_by(restaurant_id = restaurant_id, id = menu_id).one()
	if request.method == "POST":
		if request.form["name"]:
			editedItem.name = request.form["name"]
			session.add(editedItem)
			session.commit()
			flash("Menu item edited.")
			return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('item_edit.html', restaurant_id = restaurant_id, menu_id = menu_id, item = editedItem)


@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/delete/', methods=['GET', 'POST'])
def itemDelete(restaurant_id, menu_id):
	deletedItem = session.query(MenuItem).filter_by(restaurant_id = restaurant_id, id = menu_id).one()
	if request.method == "POST":
		session.delete(deletedItem)
		session.commit()
		flash("Menu item deleted.")
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('item_delete.html', restaurant_id = restaurant_id, menu_id = menu_id, item = deletedItem)

if __name__ == '__main__':
	app.secret_key = "super_key"
	app.debug = True
	app.run(host='0.0.0.0', port=5000)