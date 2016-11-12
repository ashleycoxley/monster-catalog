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

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

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
    monsters = db_session.query(Monster).limit(20).all()
    return flask.render_template('main.html', monsters=monsters)


# Create anti-forgery state token
@app.route('/signin')
def sign_in():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    flask.session['state'] = state
    return flask.render_template('signup.html', STATE=state)


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


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if flask.request.args.get('state') != flask.session['state']:
        response = flask.make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = flask.request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret_478230017741-rd1hon3dcgt9eoutdkjd5lsiidat2gp5.apps.googleusercontent.com.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = flask.make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = flask.make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = flask.make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = flask.make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = flask.session.get('credentials')
    stored_gplus_id = flask.session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = flask.make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    flask.session['credentials'] = credentials.access_token
    flask.session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    flask.session['username'] = data['name']
    flask.session['picture'] = data['picture']
    flask.session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += flask.session['username']
    output += '!</h1>'
    output += '<img src="'
    output += flask.session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flask.flash("you are now logged in as %s" % flask.session['username'])
    print "done!"
    return output


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if flask.request.args.get('state') != flask.session['state']:
        response = flask.make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = flask.request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    flask.session['provider'] = 'facebook'
    flask.session['username'] = data["name"]
    flask.session['email'] = data["email"]
    flask.session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    flask.session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    flask.session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(flask.session['email'])
    if not user_id:
        user_id = createUser(flask.session)
    flask.session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += flask.session['username']

    output += '!</h1>'
    output += '<img src="'
    output += flask.session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flask.flash("Now logged in as %s" % flask.session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = flask.session['facebook_id']
    # The access token must me included to successfully logout
    access_token = flask.session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


def createUser(session):
    newUser = User(name=session['username'], email=session[
                   'email'], picture=session['picture'])
    db_session.add(newUser)
    db_session.commit()
    user = db_session.query(User).filter_by(email=session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = db_session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = db_session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.config.from_pyfile('monster_config.py')
    app.run(host='0.0.0.0', port=5000)
