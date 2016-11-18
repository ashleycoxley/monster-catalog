import flask
import base64
import boto3
import uuid

from flask import current_app as app


def decode_and_add_picture(encoded_picture):
    """Decode picture and attempt to store in S3."""
    picture = b64decode_picture(encoded_picture)
    picture_id, picture_url = generate_picture_id_url()

    try:
        s3_store_picture(picture_id, picture)
        return picture_url
    except:
        # Add error message here in template
        return flask.render_template('create.html')


def b64decode_picture(encoded_picture):
    """Decode base64-encoded picture."""
    return base64.b64decode(str(encoded_picture))


def generate_picture_id_url():
    """Generate random picture ID and S3 link to picture."""
    picture_id = str(uuid.uuid4())
    picture_url = 'https://s3.amazonaws.com/monster-catalog/' + picture_id
    return picture_id, picture_url


def s3_store_picture(picture_id, picture):
    """Store picture in S3."""
    s3_session = boto3.session.Session(
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY']
    )
    s3 = s3_session.resource(service_name='s3')

    s3.Bucket(app.config['AWS_S3_BUCKET']).put_object(
        Key=picture_id,
        Body=picture,
        ContentType='image/png')
