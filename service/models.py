"""
Models for lines

All of the models are stored in this module
"""
import logging
from flask_sqlalchemy import SQLAlchemy
import datetime
from werkzeug.exceptions import NotFound
from enum import Enum

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()

class Status(Enum):
    """ 
    Model training Status
    """

    NOT_TRAINED = "NOT_TRAINED"
    TRAINING = "TRAINING"
    TRAINED = "TRAINED"


class PredictionStatus(Enum):

    """ 
    Model Prediction Status
    """
    NOT_PREDICTED = "NOT_PREDICTED"
    PREDICTING = "PREDICTING"
    PREDICTED = "PREDICTED"
    FAILURE = "FAILURE"




class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""

    pass


class Lines(db.Model):
    """
    Class that represents Lines
    """

    app = None

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.datetime.now())
    updated_on = db.Column(db.DateTime, default=datetime.datetime.now())
    data_path = db.Column(db.String(1024), nullable=False, default = "")
    model_path = db.Column(db.String(1024), default="")
    alert_threshold = db.Column(db.Integer, nullable=False, default=100)
    alert_email = db.Column(db.String(1024), default="")
    device_code = db.Column(db.String(1024), default="")
    status = db.Column(db.Enum(Status), nullable=False, default=Status.NOT_TRAINED)


    def __repr__(self):
        return "<Line %r id=[%s]>" % (self.name, self.id)

    def create(self):
        """
        Creates a line to the database
        """
        logger.info("Creating %s", self.name)
        self.id = None  # id must be none to generate next primary key
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a line to the database
        """
        logger.info("Saving %s", self.name)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        db.session.commit()

    def delete(self):
        """Removes a line from the data store"""
        logger.info("Deleting %s", self.name)
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        """Serializes a line into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "customer_id": self.customer_id,
            "created_on": self.created_on,
            "updated_on" : self.updated_on,
            "alert_threshold" : self.alert_threshold,
            "alert_email" : self.alert_email,
            "device_code" : self.device_code,
            "status" : str(self.status)
        }

    def deserialize(self, data):
        """
        Deserializes a line model from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.name = data["name"]
            if isinstance(data["customer_id"], int):
                self.customer_id = data["customer_id"]
            else:
                raise DataValidationError(
                    "Invalid type for integer [customer_id]: "
                    + str(type(data["customer_id"]))
                )
            self.data_path = data.get("data_path", "")
            self.device_code = data.get("device_code", "")

        except KeyError as error:
            raise DataValidationError("Invalid line : missing " + str(error.args[0])
            )
        except TypeError as error:
            raise DataValidationError( "Invalid line: body of request contained bad or no data - "
                "Error message: " + str(error)
            )
        return self

    @classmethod
    def init_db(cls, app):
        """Initializes the database session"""
        logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls):
        """Returns all of the line in the database"""
        logger.info("Processing all linesModels")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a line by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.get(by_id)

    @classmethod
    def find_by_name(cls, name):
        """Returns all lines with the given name

        Args:
            name (string): the name of the linesModels you want to match
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_customer_id(cls, customer_id):
        """Returns all lines with the given name

        Args:
            name (string): the name of the linesModels you want to match
        """
        logger.info("Processing customer id query for %s ...", str(customer_id))
        return cls.query.filter(cls.customer_id == customer_id)

    @classmethod
    def find_or_404(cls, by_id):
        """Finds a line item by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        line = cls.query.get(by_id)
        if not line:
            raise NotFound("line not found id : " + str(by_id))
        return line

    @classmethod
    def find_active_lines(cls):
        """Returns all lines with the trained models
        """
        logger.info("Processing find active lines query")
        return cls.query.filter(cls.status == Status.TRAINED)




class Predictions(db.Model):
    """
    Class that represents Lines
    """

    app = None

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1024), nullable=False)
    line_id = db.Column(db.Integer, nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.datetime.now())
    data_path = db.Column(db.String(1024), nullable=False, default = "")
    total_count = db.Column(db.Integer, nullable=False, default=0)
    defects_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.Enum(Status), nullable=False, default=Status.NOT_TRAINED)


    def __repr__(self):
        return "<Line %r id=[%s]>" % (self.name, self.id)

    def create(self):
        """
        Creates a prediction to the database
        """
        logger.info("Creating %s", self.name)
        self.id = None  # id must be none to generate next primary key
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a prediction to the database
        """
        logger.info("Saving %s", self.name)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        db.session.commit()

    def delete(self):
        """Removes a prediction from the data store"""
        logger.info("Deleting %s", self.name)
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        """Serializes a line into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "created_on": self.created_on,
            "line_id" : self.line_id,
            "total_count" : self.total_count,
            "defects_count" : self.defects_count,
            "data_path" : self.data_path,
            "status" : str(self.status)
        }

    def deserialize(self, data):
        """
        Deserializes a line model from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.name = data["name"]
            if isinstance(data["line_id"], int):
                self.line_id = data["line_id"]
            else:
                raise DataValidationError(
                    "Invalid type for integer [customer_id]: "
                    + str(type(data["customer_id"]))
                )
            self.data_path = data.get("data_path", "")
            self.total_count = data.get("total_count", 0)
            self.defects_count = data.get("defects_count", 0)

        except KeyError as error:
            raise DataValidationError("Invalid line : missing " + str(error.args[0])
            )
        except TypeError as error:
            raise DataValidationError( "Invalid line: body of request contained bad or no data - "
                "Error message: " + str(error)
            )
        return self

    @classmethod
    def init_db(cls, app):
        """Initializes the database session"""
        logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls):
        """Returns all of the line in the database"""
        logger.info("Processing all linesModels")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a line by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.get(by_id)

    @classmethod
    def find_by_name(cls, name):
        """Returns all lines with the given name

        Args:
            name (string): the name of the linesModels you want to match
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_line_id(cls, line_id):
        """Returns all lines with the line_id

        Args:
            line_id (int): the id of the linesModels you want to match
        """
        logger.info("Processing line id query for %s ...", str(line_id))
        return cls.query.filter(cls.line_id == line_id)

    @classmethod
    def find_or_404(cls, by_id):
        """Finds a line item by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        line = cls.query.get(by_id)
        if not line:
            raise NotFound("line not found id : " + str(by_id))
        return line

    
    @classmethod
    def find_recent_predictions(cls, line_id, minutes = 5):
        """Returns  prediction with the line id in the last n minutes

        Args:
            name (line_id): the id of the lines you want to match
            minutes
        """
        logger.info("Processing line id query for %s ...", str(line_id))

        threshold_datetime  = datetime.datetime.now() - datetime.timedelta(minutes=minutes)

        return cls.query.filter(cls.line_id == line_id).filter(cls.created_on >= threshold_datetime)