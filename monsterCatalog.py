import flask
import httplib2
import json
import requests
import random
import string
import datetime
import boto3
import base64
import uuid
import urlparse

import sqlalchemy
from models import Base, User, Monster


CLIENT_ID = json.loads(
    open('client_secret_478230017741-rd1hon3dcgt9eoutdkjd5lsiidat2gp5.apps.googleusercontent.com.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Monster Catalog"


app = flask.Flask(__name__)

engine = sqlalchemy.create_engine('postgres:///monstercatalog')
Base.metadata.bind = engine

DBSession = sqlalchemy.orm.sessionmaker(bind=engine)
db_session = DBSession()


@app.route('/')
def main_page():
    print flask.session
    user_id = flask.session.get('user_id')
    monsters = db_session.query(Monster).limit(20).all()
    return flask.render_template('main.html',
                                 monsters=monsters,
                                 user_id=user_id)


@app.route('/create', methods=['GET', 'POST'])
def create_monster():
    if 'username' not in flask.session:
        return flask.redirect('/signin')

    if flask.request.method == 'GET':
        return flask.render_template('create.html',
                                     submit_button_text='CREATE A MONSTER')

    elif flask.request.method == 'POST':
        name = flask.request.form['name']
        diet = flask.request.form['diet']
        enjoys = flask.request.form['enjoys']
        intentions = flask.request.form['intentions']

        for user_input in [name, diet, enjoys]:
            if len(user_input) < 1:
                return ('', 204)  # Stay on page if any fields are empty

        encoded_picture = flask.request.form.get('encoded_picture')
        picture = decode_picture(encoded_picture)
        picture_id, picture_url = generate_picture_id_url()

        try:
            s3_store_picture(picture_id, picture)
        except:
            # Add error message here in template
            return flask.render_template('create.html')

        monster = Monster(
            name=name,
            diet=diet,
            enjoys=enjoys,
            creator=flask.session['user_id'],
            picture=picture_url,
            intentions=intentions,
            created_date=datetime.datetime.now()
            )

        try:
            db_session.add(monster)
            db_session.commit()
            return flask.jsonify({'result': 'success'})
        except sqlalchemy.exc.SQLAlchemyError as e:
            db_session.rollback()
            # Add error message here in template
            return flask.jsonify({'result': 'fail'})


def decode_picture(encoded_picture):
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


@app.route('/edit/<int:monster_id>', methods=['GET', 'POST'])
def edit_monster(monster_id):
    monster = authorize_monster_change(monster_id)

    if flask.request.method == 'GET':
        return flask.render_template('create.html',
                                     name=monster.name,
                                     intentions=monster.intentions,
                                     diet=monster.diet,
                                     enjoys=monster.enjoys,
                                     picture_url=monster.picture,
                                     submit_button_text='SUBMIT EDIT')

    elif flask.request.method == 'POST':
        encoded_picture = flask.request.form.get('encoded_picture')
        picture = decode_picture(encoded_picture)
        picture_id, picture_url = generate_picture_id_url()

        try:
            s3_store_picture(picture_id, picture)
        except:
            # TODO add error message here in template
            return flask.render_template('create.html')

        monster.name = flask.request.form['name']
        monster.diet = flask.request.form['diet']
        monster.enjoys = flask.request.form['enjoys']
        monster.picture = picture_url
        monster.intentions = flask.request.form['intentions']
        monster.edited_date = datetime.datetime.now()

        try:
            db_session.add(monster)
            db_session.commit()
            return flask.jsonify({'result': 'success'})
        except Exception as e:
            db_session.rollback()
            # TODO add error message here in template
            return flask.jsonify({'result': 'fail'})


@app.route('/delete/<int:monster_id>', methods=['POST'])
def delete_monster(monster_id):
    monster = authorize_monster_change(monster_id)
    try:
        db_session.delete(monster)
        db_session.commit()
        # TODO add success message here in template
        return flask.redirect('/')

    except sqlalchemy.exc.SQLAlchemyError as e:
        db_session.rollback()
        # TODO add error message here in template
        return flask.redirect('/')


def authorize_monster_change(monster_id):
    monster = db_session.query(Monster).filter_by(id=monster_id).one()
    current_user_id = flask.session.get('user_id')
    if monster is None:
        flask.redirect('/')
    if current_user_id is None:
        flask.redirect('/signin')
    if current_user_id != monster.creator:
         # Add error message here
        flask.redirect('/')
    return monster


@app.route('/api/monsters', methods=['GET'])
def monsters():
    monsters = db_session.query(Monster).all()
    monsters_serialized = [monster.serialize for monster in monsters]

    return flask.jsonify(monsters=monsters_serialized)


@app.route('/signin')
def sign_in():
    print flask.session
    if 'user_id' not in flask.session:
        state = set_state()
        return flask.render_template('signup.html',
                                     state=state)
    else:
        return flask.redirect('/')


def set_state():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    flask.session['state'] = state
    return state


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    # Check that local state parameter matches the one sent to Facebook
    fb_returned_state = flask.request.args.get('state')
    check_state_parameter(fb_returned_state)

    # Exchange for long-lived access token
    short_lived_access_token = flask.request.data
    long_lived_access_token = exchange_fb_token(short_lived_access_token)

    # Get FB user data; if email doesn't exist, add user
    fb_user_data = get_fb_user_data(long_lived_access_token)
    user_id = add_or_verify_user(fb_user_data)

    if user_id:
        print fb_user_data['id']
        flask.session['facebook_id'] = fb_user_data['id']
        flask.session['access_token'] = long_lived_access_token
        print flask.session
        success_message = 'Login successful.'
        return (success_message, 200)
    else:
        fail_message = 'Failed to login.'
        return (fail_message, 401)


def check_state_parameter(returned_state):
    flask_state = flask.session['state']

    if returned_state != flask_state:
        bad_state_response = flask.jsonify('Invalid state parameter.')
        bad_state_response.status_code = 401
        return bad_state_response


def load_fb_app_data():
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    return app_id, app_secret


def exchange_fb_token(short_lived_access_token):
    """Exchange short-lived access token for long-lived one."""
    app_id, app_secret = load_fb_app_data()
    fb_token_exchange_url = 'https://graph.facebook.com/oauth/access_token'
    fb_token_exchange_params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': short_lived_access_token
    }
    fb_token_exchange_result = requests.get(fb_token_exchange_url,
                                            params=fb_token_exchange_params)
    fb_token_exchange_text = fb_token_exchange_result.text
    long_lived_access_token = fb_token_exchange_text.split("&")[0].split('=')[1]
    return long_lived_access_token


def get_fb_user_data(long_lived_access_token):
    """Using long-lived access token, query Facebook Graph API for user data."""
    fb_user_query_url = 'https://graph.facebook.com/v2.4/me'
    fb_user_query_params = {
        'fields': 'name,id,email',
        'access_token': long_lived_access_token
    }
    fb_user_query_result = requests.get(fb_user_query_url,
                                        params=fb_user_query_params)
    fb_user_data = json.loads(fb_user_query_result.text)

    return fb_user_data


def add_or_verify_user(user_data):
    user_id = get_user_id_by_email(user_data['email'])
    if not user_id:
        user_id = create_user(user_data)
    flask.session['user_id'] = user_id
    return user_id


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = flask.session['facebook_id']
    access_token = flask.session['access_token']

    logout_params = {
        'access_token': access_token
    }

    fb_logout_url = 'https://graph.facebook.com/%s/permissions' % facebook_id
    logout_result = requests.delete(fb_logout_url,
                                    params=logout_params)
    flask.session.clear()
    return flask.redirect('/')


def create_user(user_data):
    user = User(
        name=user_data['username'],
        email=user_data['email'],
        picture=user_data['data']['url']
        )
    try:
        db_session.add(user)
        db_session.commit()
    except sqlalchemy.ext.SQLAlchemyError:
        db_session.rollback()
    user = db_session.query(User).filter_by(email=user_data['email']).one()
    return user.id


def get_user(user_id):
    user = db_session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id_by_email(email):
    try:
        user = db_session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.config.from_pyfile('monster_config.py')
    app.run(host='0.0.0.0', port=5000)
