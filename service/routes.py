"""
My Service
Describe what your service does here
"""

import uuid
import os
from werkzeug.utils import secure_filename
import datetime


# from email.mime import application
from flask import jsonify, request, url_for, abort, flash, redirect, render_template
from service.models import Lines, Status, Predictions
from .common import status  # HTTP Status Codes
from .config import *
from service.train import Train
from service.predict_image import Predictor
from service.tasks import train_task, predict_batch_task

# Import Flask application
from . import app
from . import celery
import time





app.config['DATA_FOLDER'] = DATA_FOLDER
app.config['MODELS_FOLDER'] = DATA_FOLDER
app.config['DEFECTS_FOLDER'] = DEFECTS_FOLDER







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
    data_path = get_line_data_path(line.id)
    model_path = get_line_models_path(line.id)
    # Make line directory if not exists
    if not os.path.isdir(line_path):
        os.mkdir(line_path)
    if not os.path.isdir(model_path):
        os.mkdir(model_path)
    line.data_path = data_path
    line.model_path = model_path
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
    line.model_path = body.get("model_path", None) or line.model_path
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




@app.route("/predict", methods=["POST"])
def predict():
    predictor = Predictor()
    data = request.get_json()
    img_path = data["path"]
    response = predictor.predict(img_path)
    response["status"] = "Success"
    return response


@app.route("/train/<int:line_id>", methods=["GET"])
def train(line_id):
    app.logger.info("Request to train line %d", line_id)
    train_task.apply_async((line_id,))
    return "", status.HTTP_204_NO_CONTENT




    


@app.route('/upload/train/<int:line_id>', methods=['POST'])
def upload_training_data(line_id):
    # file Upload

    app.logger.info('Uploading training data for line {0}'.format(line_id))

    line_path = get_line_data_path(line_id)

    # Make line directory if not exists
    if not os.path.isdir(line_path):
        os.mkdir(line_path)

    train_data_path = os.path.join(line_path, "train")
    if not os.path.isdir(train_data_path):
        os.mkdir(train_data_path)

    train_data_path = os.path.join(train_data_path, "good")
    if not os.path.isdir(train_data_path):
        os.mkdir(train_data_path)
    
    test_data_path = os.path.join(line_path, "test")
    if not os.path.isdir(test_data_path):
        os.mkdir(test_data_path)
    valid_data_path = os.path.join(test_data_path, "good")
    if not os.path.isdir(valid_data_path):
        os.mkdir(valid_data_path)

    

    if request.method == 'POST':
        
        if 'files[]' not in request.files:
            print('No file part')
            return jsonify({"error": "No files to upload"}), status.HTTP_400_BAD_REQUEST

        app.logger.info(request.files.getlist('files[]'))
        files = request.files.getlist('files[]')
        app.logger.info('Files found {0}'.format(len(files)))
        split = int(len(files)/10)
        train_files = files[split:]
        valid_files = files[:split]
        for file in train_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(train_data_path,file.filename))

        for file in valid_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(valid_data_path,file.filename))

        app.logger.info('Files successfully uploaded')
        return jsonify({"file_count": len(files),"message" : "Upload Success"}), status.HTTP_200_OK



@app.route('/upload/test/<int:line_id>', methods=['POST'])
def upload_test_data(line_id):
    # file Upload

    line_path = get_line_data_path(line_id)

    # Make line directory if not exists
    if not os.path.isdir(line_path):
        os.mkdir(line_path)


    
    prediction_name = "test_" + str(int(time.time())) 
    predictions_data_path = os.path.join(line_path, prediction_name)
    prediction = Predictions()
    prediction.name = prediction_name
    prediction.data_path = predictions_data_path
    prediction.line_id = line_id
    prediction.created_on = datetime.datetime.now()

    
    if not os.path.isdir(predictions_data_path):
        os.mkdir(predictions_data_path)

    if request.method == 'POST':
        app.logger.info('Uploading files')
        if 'files[]' not in request.files:
            app.logger.info(('No files found'))
            return jsonify({"error": "No files to upload"}), status.HTTP_400_BAD_REQUEST

        files = request.files.getlist('files[]')

        count = 0
        for file in files:
            if file and allowed_file(file.filename):
                # filename = secure_filename(file.filename)
                app.logger.info(file.filename)
                file.save(os.path.join(predictions_data_path,file.filename))
                count = count + 1

        app.logger.info('File(s) successfully uploaded')
        prediction.total_count = count
        prediction.create()
        predict_batch_task.apply_async((line_id, prediction.id))
        app.logger.info('Prediction task sent to queue')
        return jsonify({"file_count": count,"message" : "Upload Success"}), status.HTTP_200_OK





######################################################################
# Quality of line in last n minutes
######################################################################
@app.route("/quality/<int:line_id>/<int:minutes>", methods=["GET"])
def quality(line_id,minutes):
    """
    Retrieve predictions for line in last n minutes
    This endpoint will return all lines
    """

    app.logger.info("Request for quality for line_id {0} in last {1} minutes".format(line_id, minutes))
    predictions = Predictions.find_recent_predictions(line_id,minutes)
    app.logger.info(predictions)
    quality = []
    for prediction in predictions:
        prediction_quality = (1.0 - ((prediction.defects_count*1.0)/prediction.total_count))*100.0
        quality.append((prediction.created_on, prediction_quality))
        
    return jsonify({"quality": quality}), status.HTTP_200_OK









######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


    

def get_line_data_path(line_id):
    return os.path.join(app.config['DATA_FOLDER'],  str(line_id))

def get_line_models_path(line_id):
    return os.path.join(app.config['MODELS_PATH'],  str(line_id))

def get_line_defects_path(line_id):
    return os.path.join(app.config['DEFECTS_FOLDER'],  str(line_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    Predictions.init_db(app)
