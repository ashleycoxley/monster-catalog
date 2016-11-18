import json

CLIENT_ID = json.loads(
    open('client_secret_478230017741-rd1hon3dcgt9eoutdkjd5lsiidat2gp5.apps.googleusercontent.com.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Monster Catalog"

FB_TOKEN_EXCHANGE_URL = 'https://graph.facebook.com/oauth/access_token'
FB_USER_QUERY_URL = 'https://graph.facebook.com/v2.4/me'
FB_LOGOUT_URL = 'https://graph.facebook.com/%s/permissions'

GOOGLE_SECRETS_FILE = 'client_secret_478230017741-rd1hon3dcgt9eoutdkjd5lsiidat2gp5.apps.googleusercontent.com.json'
GOOGLE_VERIFY_TOKEN_URL = 'https://www.googleapis.com/oauth2/v1/tokeninfo'
GOOGLE_USER_QUERY_URL = 'https://www.googleapis.com/oauth2/v1/userinfo'
GOOGLE_LOGOUT_URL = 'https://accounts.google.com/o/oauth2/revoke'
