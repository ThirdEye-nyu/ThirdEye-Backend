"""
My Service
Describe what your service does here
"""

import uuid

# from email.mime import application
from flask import jsonify, request, url_for, abort
from service.models import Lines, Status
from .common import status  # HTTP Status Codes
from .config import *
# Import Flask application
from . import app


######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/healthcheck")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="Healthy"), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    app.logger.info("Request for Root URL")
    return (
        jsonify(
            name="lines Demo REST API Service",
            version="1.0",
            paths=url_for("create_lines", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW line
######################################################################
@app.route("/lines", methods=["POST"])
def create_lines():
    """
    Creates a line
    This endpoint will create a line based the data in the body that is posted
    """
    app.logger.info("Request to create a line")
    check_content_type("application/json")
    line = Lines()
    line.deserialize(request.get_json())
    line.device_code = str(uuid.uuid4())
    line.create()
    line.data_path = S3_DATA_BASE_PREFIX + str(line.id) + "/"
    line.update()
    message = line.serialize()
    location_url = url_for("get_lines", line_id=line.id, _external=True)
    app.logger.info("line with ID [%s] created.", line.id)
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


@app.route("/lines/<int:line_id>", methods=["GET"])
def get_lines(line_id):
    """
    Retrieve a single line
    This endpoint will return a line based on it's id
    """
    app.logger.info("Request for line with id: %s", line_id)
    line = Lines.find(line_id)
    if not line:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"line with id '{line_id}' was not found.",
        )

    app.logger.info("Returning line: %s", line.name)
    return jsonify(line.serialize()), status.HTTP_200_OK


@app.route("/lines/<int:line_id>", methods=["PUT"])
def update_line(line_id):
    """Renames a line to a name specified by the "name" field in the body
    of the request.

    Args:
        line_id: The id of the line to update.
    """
    app.logger.info("Request to update line %d", line_id)
    line = Lines.find(line_id)

    if not line:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"line with id '{line_id}' was not found.",
        )

    body = request.get_json()
    app.logger.info("Got body=%s", body)

    line.name = body.get("name", None) or line.name
    line.alert_threshold = body.get("alert_threshold", None) or line.alert_threshold
    line.alert_email = body.get("alert_email", None) or line.alert_email
    line.model_path = body.get("model_path", None) or line.alert_email
    line.data_path = body.get("data_path", None) or line.data_path
    model_status = body.get("status", None)
    if model_status:
        if model_status == "TRAINING":
            line.status = Status.TRAINING
        elif model_status == "TRAINED":
            line.status = Status.TRAINED

    line.update()
    return line.serialize(), status.HTTP_200_OK



######################################################################
# LIST ALL THE lines FOR A CUSTOMER
######################################################################
@app.route("/lines", methods=["GET"])
def list_all_lines():
    """
    Retrieve all lines
    This endpoint will return all lines
    """

    if request.args:
        args = request.args
        customer_id = args.get("customer_id", type=int)
        app.logger.info("Request for lines with customer_id: %s", str(customer_id))
        lines = Lines.find_by_customer_id(customer_id)
        lines_serialized = [w.serialize() for w in lines]
        app.logger.info(lines_serialized)
        if len(lines_serialized) == 0:
            return {
                "message": "No lines found for the customer id - "
                + str(customer_id)
            }, status.HTTP_200_OK
        # app.logger.info("Returning line:", lines)
        return jsonify({"lines": lines_serialized}), status.HTTP_200_OK
    else:
        app.logger.info("Request for all lines")
        lines = Lines.all()

        lines_serialized = [w.serialize() for w in lines]
        app.logger.info(lines_serialized)
        if len(lines_serialized) == 0:
            return {"message": "No lines found"}, status.HTTP_200_OK
        return jsonify({"lines": lines_serialized}), status.HTTP_200_OK



######################################################################
# DELETE A line
######################################################################
@app.route("/lines/<int:line_id>", methods=["DELETE"])
def delete_lines(line_id):
    """
    Delete a line
    This endpoint will delete a line based the id specified in the path
    """
    app.logger.info("Request to delete line with id: %s", line_id)
    line = Lines.find(line_id)
    if line:
        line.delete()

    app.logger.info("line with ID [%s] delete complete.", line_id)
    return "", status.HTTP_204_NO_CONTENT

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


def init_db():
    """Initializes the SQLAlchemy app"""
    global app
    Lines.init_db(app)
