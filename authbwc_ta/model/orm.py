#import sqlalchemy as sa
#
#from sqlalchemybwc import db
#from sqlalchemybwc.lib.declarative import declarative_base
#from sqlalchemybwc.lib.decorators import ignore_unique, transaction
#
#Base = declarative_base(metadata=db.meta)
#
#class Car(Base):
#    __tablename__ = 'sabwp_cars'
#
#    make = sa.Column(sa.Unicode(255), nullable=False)
#    model = sa.Column(sa.Unicode(255), nullable=False)
#    year = sa.Column(sa.Integer, nullable=False)
#
#    def __repr__(self):
#        return '<Car %s, %s, %s>' % (self.make, self.model, self.year)
