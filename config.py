import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = os.getenv("DEBUG", "True") == "True"
    ENV = os.getenv("ENV", "development")