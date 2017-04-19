import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()



class Shelter(Base):
	__tablename__ = 'shelter'

	name = Column(String(80), nullable = False)

	address = Column(String(250), nullable = False)

	city = Column(String(80), nullable = False)

	state = Column(String(80), nullable = False)

	zipCode = Column(Integer, nullable = False)

	website = Column(String(250))

	id = Column(Integer, primary_key = True)


class Puppy(Base):
	__tablename__ = 'puppy'

	name = Column(String(80), primary_key = True)

	dob = Column(String(80), nullable = False)

	gender = Column(String(80), nullable = False)

	weight = Column(Integer, nullable = False)

	shelter_id = Column(Integer, ForeignKey('shelter.id'))

	photo = Column(LargeBinary)


engine = create_engine('sqlite:///puppies.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

Base.metadata.create_all(engine)

