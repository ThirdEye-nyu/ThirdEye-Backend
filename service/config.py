"""
Global Configuration for Application
"""
import os

# Get configuration from environment
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

# Local Data Paths

path = "/home/thirdeye/thirdeye"

if not os.path.isdir(path):
    os.mkdir(path)

DATA_FOLDER = os.path.join(path, 'data')
if not os.path.isdir(DATA_FOLDER):
    os.mkdir(DATA_FOLDER)

MODELS_FOLDER = os.path.join(path, 'models')
if not os.path.isdir(MODELS_FOLDER):
    os.mkdir(MODELS_FOLDER)

DEFECTS_FOLDER = os.path.join(path, 'defects')
if not os.path.isdir(DEFECTS_FOLDER):
    os.mkdir(DEFECTS_FOLDER)


# Allowed extension you can set your own
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


# Get S3 variables

S3_BUCKET=  os.getenv("S3_BUCKET", "thirdeye-dev")
S3_DATA_BASE_PREFIX = os.getenv("S3_DATA_BASE_PREFIX", "data/")
S3_MODELS_BASE_PREFIX = os.getenv("S3_DATA_BASE_PREFIX", "models/")

# Configure SQLAlchemy
SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret for session management
SECRET_KEY = os.getenv("SECRET_KEY", "s3cr3t-key-shhhh")


CELERY_CONFIG={
    'broker_url': 'redis://redis:6379',
    'result_backend': 'redis://redis:6379/0',
}


ALERTS_CHECK_TIMER = 3 # in minutes

SENDER_EMAIL = "sakhamurijaikar@gmail.com"
SENDER_PASSWORD = ""
