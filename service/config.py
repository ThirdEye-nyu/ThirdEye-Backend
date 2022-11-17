"""
Global Configuration for Application
"""
import os

# Get configuration from environment
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

# Get S3 variables

S3_BUCKET=  os.getenv("S3_BUCKET", "thirdeye-dev")
S3_DATA_BASE_PREFIX = os.getenv("S3_DATA_BASE_PREFIX", "data/")
S3_MODELS_BASE_PREFIX = os.getenv("S3_DATA_BASE_PREFIX", "models/")

# Configure SQLAlchemy
SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret for session management
SECRET_KEY = os.getenv("SECRET_KEY", "s3cr3t-key-shhhh")
