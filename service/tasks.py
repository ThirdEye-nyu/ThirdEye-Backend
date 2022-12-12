from . import celery
from . import app
from service.train import Train
from service.predict_image import Predictor
from service.models import Lines,Status,Predictions,PredictionStatus
from service.config import *
import logging
import yagmail
import smtplib    


logger = logging.getLogger("tasks")


@celery.task
def train_task(line_id):
    try:
        line = Lines.find(line_id)
        line.status = Status.TRAINING
        line.update()
        logger.info("Queue message received to train line %d", line_id)
        trainer = Train(line_id =line_id)
        trainer.train()
        line = Lines.find(line_id)
        line.status = Status.TRAINED
        line.update()
        logger.info("Model trained for line %d ", line_id)
        return True
    except Exception as e:
        logger.error("Training failed for line %d ", line_id)
        logger.error(e)
        line = Lines.find(line_id)
        line.status = Status.NOT_TRAINED
        line.update()
        return False


@celery.task
def predict_batch_task(line_id,prediction_id):
    try:
        logger.info("Queue message received to predict batch for prediction %d", prediction_id)
        prediction = Predictions.find(prediction_id)
        test_dir = prediction.data_path
        prediction.status = Status.TRAINING
        prediction.update()
        predictor = Predictor(line_id=line_id)
        defect_images = predictor.predict_batch(test_dir=test_dir)
        prediction.defects_count = len(defect_images)
        prediction.status = Status.TRAINED
        prediction.update()
        logger.info("Prediction completed for prediction %d ", prediction_id)
        return True
    except Exception as e:
        logger.error("Prediction failed for prediction %d ", prediction_id)
        logger.error(e)
        prediction = Predictions.find(prediction_id)
        prediction.status = Status.TRAINING
        prediction.update()
        return False



@celery.task
def quality_check():
    try:
        logger.info("Quality Check : START")
        lines = Lines.find_active_lines()
        for line in lines:
            total_count = 0.0
            defects_count = 0.0
            predictions = Predictions.find_recent_predictions(line_id=line.id, minutes=ALERTS_CHECK_TIMER)
            for prediction in predictions:
                total_count = total_count + prediction.total_count
                defects_count = defects_count + prediction.defects_count

            if total_count > 0:
                quality = (1.0 - (defects_count/total_count))*100
                threshold = line.alert_threshold
                if quality < threshold:
                    alert(line.alert_email, line.name, quality)
            
            else:
                logger.info("No predictions in last {0} minutes".format(ALERTS_CHECK_TIMER))

        logger.info("Qaulity Check : SUCCESS")
        return True
    except Exception as e:
        logger.error("Quality check failed %s", e)
        return False



def alert(email,name, quality):
    logger.info("Sending Email to {0}: Quality for line {1} decreased below threshold - Quality {2} %".format(email,name,quality))
    try:
        yag = yagmail.SMTP(SENDER_EMAIL, SENDER_PASSWORD)
        contents = ["Alert : Quality for line {0} is below threshold. Quality - {1} ".format(name,quality)]
        yag.send(email, 'ThirdEye - Quality Alert', contents)
        logger.info("Successfully sent email")
    except smtplib.SMTPException as error:
        logger.error(str(error))
        logger.error("Error: unable to send email")




    