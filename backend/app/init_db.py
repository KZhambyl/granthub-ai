from app.db import Base, engine
from app.models import Grant

def init_db():
    Base.metadata.create_all(bind=engine)
