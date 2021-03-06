from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
import jinja2
import cgi # Common gateway interface
import database_setup
import lotsofmenus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem

engine = create_engine('sqlite:///restaurantmenu2.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

# Load templates and envoke Jinja2
template_dir = os.path.join(os.path.dirname(__file__), 'templates')

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

def renderTemplate(self, template, **params):
	template = jinja_env.get_template(template)
	return template.render(params)

def renderPage(self, template, **params):
	self.wfile.write(self.renderTemplate(template, **params))

class webserverHandler(BaseHTTPRequestHandler):
	def renderTemplate(self, template, **params):
		template = jinja_env.get_template(template)
		return template.render(params)

	def renderPage(self, template, **params):
		self.wfile.write(self.renderTemplate(template, **params))

	def do_GET(self):
		try:
			if self.path.endswith("/restaurants"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				items = session.query(Restaurant).all()
				self.renderPage("restaurants.html", items=items, message=None)

				print items
				return

			if self.path.endswith("/new"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				self.renderPage("newrestaurant.html")
				return

			if self.path.endswith("/edit"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				path = self.path
				print "path:",path
				restaurant_id = path.split('/')[2]
				print "restaurant_id:",restaurant_id

				item = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
				print "item:",item

				self.renderPage("edit.html", item=item)
				return

			if self.path.endswith("/delete"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				path = self.path
				print "path:",path
				restaurant_id = path.split('/')[2]
				print "restaurant_id:",restaurant_id

				item = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
				print "item:",item
				self.renderPage("delete.html", item=item)
				return

		except IOError:
			self.send_error(404, "File Not Found %s" % self.path)

	def do_POST(self):
		try:
			self.send_response(301)
			self.end_headers()

			ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))

			if ctype == 'multipart/form-data':
				fields = cgi.parse_multipart(self.rfile, pdict)

				if self.path.endswith("/new"):
					name = fields.get("name")
					print "restuarant name:", name
					print "not a list?:", name[0]
					createRestaurant = Restaurant(name=name[0])
					session.add(createRestaurant)
					session.commit()

					items = session.query(Restaurant).all()
					message = "Your restaurant has been added :D"
					self.renderPage("restaurants.html", items=items, message=message)
					return

				if self.path.endswith("/edit"):
					path = self.path
					restaurant_id = path.split('/')[2]
					name = fields.get("name")

					updateRestaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
					updateRestaurant.name = name[0]
					session.add(updateRestaurant)
					session.commit()

					items = session.query(Restaurant).all()
					message = "Your restaurant has been edited :D"
					self.renderPage("restaurants.html", items=items, message=message)
					return

				if self.path.endswith("/delete"):
					path = self.path
					restaurant_id = path.split('/')[2]

					deleteRestaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
					session.delete(deleteRestaurant)
					session.commit()

					items = session.query(Restaurant).all()
					message = "Your restaurant has been deleted :D"
					self.renderPage("restaurants.html", items=items, message=message)

					return



		except:
			pass


def main ():
	try:
		port = 8080
		server = HTTPServer(('',port), webserverHandler)
		print "Web server running on port %s" % port
		server.serve_forever()

	except KeyboardInterrupt:
		print "^C entered, stopping web server..."
		server.socket.close()

if __name__ == '__main__':
	main()