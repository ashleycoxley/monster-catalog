import flask
import requests
import json
import random
import string
import urlparse

from oauth_vars import *
import database_operations

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError


def set_session_token():
    """Generate random session token to send to 3rd party oauth service, and
    save in Flask session."""
    session_token = ''.join(random.choice(string.ascii_uppercase + string.digits)
                            for x in xrange(32))
    flask.session['session_token'] = session_token
    return session_token


def verify_session_token(returned_session_token):
    """Verify that session token parameter sent to 3rd party oauth service
    matches current session token."""
    flask_session_token = flask.session.get('session_token')

    if returned_session_token != flask_session_token:
        return ('Invalid oauth session token parameter.', 401)


def third_party_login(service, db_session):
    # Check that Flask session_token parameter matches the one originally sent
    # to 3rd party
    returned_session_token = flask.request.args.get('session_token')
    verify_session_token(returned_session_token)

    # Exchange returned short-lived access token for long-lived access token,
    # and use that token to retrieve user data.
    # Facebook and Google have slightly different methods.
    short_lived_access_token = flask.request.data
    if service == 'facebook':
        long_lived_access_token = exchange_fb_token(short_lived_access_token,
                                                    FB_TOKEN_EXCHANGE_URL)
        user_data = get_fb_user_data(long_lived_access_token,
                                     FB_USER_QUERY_URL)
        third_party_id = user_data['id']

    elif service == 'google':
        try:
            google_credentials = exchange_g_token(short_lived_access_token,
                                                  GOOGLE_SECRETS_FILE)
        except FlowExchangeError:
            return ('Authorization failed.', 401)
        long_lived_access_token = google_credentials.access_token
        third_party_id = verify_google_token(long_lived_access_token,
                                             google_credentials,
                                             GOOGLE_VERIFY_TOKEN_URL)
        user_data = get_google_user_data(long_lived_access_token,
                                         GOOGLE_USER_QUERY_URL)

    # Check if user exists using email; if not, add user
    user_id = add_or_verify_user(user_data, db_session)

    if user_id:
        third_party_id_name = service + '_id'
        flask.session[third_party_id_name] = third_party_id
        flask.session['access_token'] = long_lived_access_token
        return ('Login successful.', 200)
    else:
        return ('Failed to login.', 401)


def add_or_verify_user(user_data, db_session):
    user_id = database_operations.get_user_id_by_email(user_data['email'],
                                                       db_session)
    if not user_id:
        user_id = database_operations.create_user(user_data,
                                                  db_session)
    flask.session['user_id'] = user_id
    return user_id


def third_party_logout():
    facebook_id = flask.session.get('facebook_id')
    google_id = flask.session.get('google_id')
    access_token = flask.session['access_token']

    if facebook_id:
        user_logout_query_url = FB_LOGOUT_URL % facebook_id
        logout_params = {
            'access_token': access_token
        }
        logout_result = requests.delete(user_logout_query_url,
                                        params=logout_params)
    elif google_id:
        user_logout_query_url = GOOGLE_LOGOUT_URL
        logout_params = {
            'token': access_token
        }
        logout_result = requests.get(user_logout_query_url,
                                     params=logout_params)
    flask.session.clear()
    # TODO add success message to template
    return flask.redirect('/')


# GOOGLE

def exchange_g_token(short_lived_access_token, GOOGLE_SECRETS_FILE):
    oauth_flow = flow_from_clientsecrets(GOOGLE_SECRETS_FILE, scope='')
    oauth_flow.redirect_uri = 'postmessage'
    credentials = oauth_flow.step2_exchange(short_lived_access_token)
    return credentials


def verify_google_token(long_lived_access_token, google_credentials,
                        GOOGLE_VERIFY_TOKEN_URL):
    verify_token_params = {
        'access_token': long_lived_access_token
    }
    verify_google_token_result = requests.get(GOOGLE_VERIFY_TOKEN_URL,
                                              params=verify_token_params)

    # Verify that token valid with Google
    verify_google_token_result_dict = verify_google_token_result.json()
    if verify_google_token_result.status_code != 200:
        return ('Google token invalid', 401)

    # Verify access token valid for this user
    google_id = google_credentials.id_token['sub']
    if verify_google_token_result_dict['user_id'] != google_id:
        return ("Token's user ID doesn't match given user ID", 401)

    # Verify access token valid for this app
    if verify_google_token_result_dict['issued_to'] != CLIENT_ID:
        return ("Token's client ID does not match app's", 401)

    return google_id


def get_google_user_data(long_lived_access_token, GOOGLE_USER_QUERY_URL):
    google_user_data_params = {
        'access_token': long_lived_access_token,
        'alt': 'json'
    }
    google_user_data_response = requests.get(GOOGLE_USER_QUERY_URL,
                                             params=google_user_data_params)
    return google_user_data_response.json()


# FACEBOOK

def load_fb_app_data():
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    return app_id, app_secret


def exchange_fb_token(short_lived_access_token, FB_TOKEN_EXCHANGE_URL):
    """Exchange short-lived access token for long-lived one."""
    app_id, app_secret = load_fb_app_data()
    fb_token_exchange_params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': short_lived_access_token
    }

    fb_token_exchange_result = requests.get(FB_TOKEN_EXCHANGE_URL,
                                            params=fb_token_exchange_params)
    fb_token_exchange_result_dict = urlparse.parse_qs(fb_token_exchange_result.text)
    long_lived_access_token = fb_token_exchange_result_dict.get('access_token')
    return long_lived_access_token


def get_fb_user_data(long_lived_access_token, FB_USER_QUERY_URL):
    """Using long-lived access token, query Facebook Graph API for user data."""
    fb_user_query_params = {
        'fields': 'name,id,email,picture',
        'access_token': long_lived_access_token
    }
    fb_user_query_result = requests.get(FB_USER_QUERY_URL,
                                        params=fb_user_query_params)
    fb_user_data = json.loads(fb_user_query_result.text)

    return standardize_fb_user_data(fb_user_data)


def standardize_fb_user_data(user_data):
    """Un-nest the picture url string in Facebook user data so that user_data
    object matches the user_data object returned from Google."""
    user_data['picture'] = user_data['picture']['data']['url']
    return user_data
