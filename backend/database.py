from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import urllib.parse

# Replace 'YOUR_ACTUAL_PASSWORD' with your pgAdmin password
# Ensure the database name at the end is 'clinical_db'
password = urllib.parse.quote_plus("Vedant@windows.1745")
SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:{password}@localhost:5432/clinical_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# This creates a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This is used for ORM models (if you decide to use them later)
Base = declarative_base()