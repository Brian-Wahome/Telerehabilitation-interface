from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv('../backend/.env')

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Attempting to connect to: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    print("Successfully connected to the database!")
    connection.close()
except Exception as e:
    print(f"Error connecting to the database: {e}")
