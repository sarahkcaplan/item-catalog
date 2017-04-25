from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm	import sessionmaker
from database_setup import Base, Restaurant, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# JSON endpoints

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

@app.route('/restaurant/<int:restaurant_id>/edit/')
def restaurantEdit(restaurant_id):
	return

@app.route('/restaurant/<int:restaurant_id>/delete/')
def restaurantDelete(restaurant_id):
	return

@app.route('/restaurant/new/')
def restaurantNew():
	return

@app.route('/restaurant/<int:restaurant_id>/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
	if request.method == "POST":
		newItem = MenuItem(name = request.form["name"],
						   restaurant_id = restaurant_id)
		session.add(newItem)
		session.commit()
		flash("New menu item created!")
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('newmenuitem.html', restaurant_id = restaurant_id)


@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	editedItem = session.query(MenuItem).filter_by(restaurant_id = restaurant_id, id = menu_id).one()
	if request.method == "POST":
		if request.form["name"]:
			editedItem.name = request.form["name"]
			session.add(editedItem)
			session.commit()
			flash("Menu item edited.")
			return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, i = editedItem)


@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/delete/', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	deletedItem = session.query(MenuItem).filter_by(restaurant_id = restaurant_id, id = menu_id).one()
	if request.method == "POST":
		session.delete(deletedItem)
		session.commit()
		flash("Menu item deleted.")
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('deletemenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, i = editedItem)

if __name__ == '__main__':
	app.secret_key = "super_key"
	app.debug = True
	app.run(host='0.0.0.0', port=5000)