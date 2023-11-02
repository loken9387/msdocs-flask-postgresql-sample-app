from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean, Float
from sqlalchemy.orm import validates
from sqlalchemy.orm import relationship
import datetime


from app import db

class Group(db.Model):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    nodes = relationship('Nodes', backref='group', lazy=True)
    temp_data = relationship('TempData', backref='group')

    def __str__(self):
        return self.name
    
class Node(db.Model):
    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    group_id = Column(Integer, ForeignKey('group.id'))
    location = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    sleeptime = Column(Integer, default=0)  
    interval_time = Column(Integer, default=0)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    temp_data = relationship('TempData', backref='node')


class TempData(db.Model):
    __tablename__ = 'temp_data'
    id = Column(Integer, primary_key=True)
    temp = Column(Float, nullable=False)
    time = Column(DateTime, default=datetime.datetime.utcnow)
    node_id = Column(Integer, ForeignKey('nodes.id'))
    group_id = Column(Integer, ForeignKey('groups.id'))


class Restaurant(db.Model):
    __tablename__ = 'restaurant'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    street_address = Column(String(50))
    description = Column(String(250))

    def __str__(self):
        return self.name

class Review(db.Model):
    __tablename__ = 'review'
    id = Column(Integer, primary_key=True)
    restaurant = Column(Integer, ForeignKey('restaurant.id', ondelete="CASCADE"))
    user_name = Column(String(30))
    rating = Column(Integer)
    review_text = Column(String(500))
    review_date = Column(DateTime)

    @validates('rating')
    def validate_rating(self, key, value):
        assert value is None or (1 <= value <= 5)
        return value

    def __str__(self):
        return f"{self.user_name}: {self.review_date:%x}"
