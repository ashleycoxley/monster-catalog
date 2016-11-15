from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(500))
    monsters = relationship('Monster')


class Monster(Base):
    __tablename__ = 'monster'

    id = Column(Integer, primary_key=True)
    creator = Column(Integer, ForeignKey('user.id'))
    created_date = Column(DateTime)
    edited_date = Column(DateTime)
    name = Column(String(250), nullable=False)
    diet = Column(String(500), nullable=False)
    enjoys = Column(String(500), nullable=False)
    picture = Column(String(500))
    intentions = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'diet': self.diet,
            'enjoys': self.enjoys,
            'picture': self.picture,
            'creator': self.creator,
            'created_date': self.created_date,
            'intentions': self.intentions
        }


engine = create_engine('postgresql:///monstercatalog')
Base.metadata.create_all(engine)
