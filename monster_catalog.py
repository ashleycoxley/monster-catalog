import flask
import sqlalchemy
import json

from models import Base, Monster
import monster_input
import database_operations
import login


app = flask.Flask(__name__)

engine = sqlalchemy.create_engine('postgres:///monstercatalog')
Base.metadata.bind = engine

DBSession = sqlalchemy.orm.sessionmaker(bind=engine)
db_session = DBSession()

with open('user_messages.json') as message_file:
    user_messages = json.load(message_file)


@app.route('/')
def main_page():
    user_id = flask.session.get('user_id')
    monsters = db_session.query(Monster).limit(20).all()
    action = flask.request.args.get('action')
    result = flask.request.args.get('result')
    if action:
        alert_text = user_messages['messages'][action].get(result)
    else:
        alert_text = ''
    return flask.render_template('main.html',
                                 monsters=monsters,
                                 user_id=user_id,
                                 alert_class=result,
                                 alert_text=alert_text)


@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_id' not in flask.session:
        return flask.redirect('/signin?action=user_login&result=alert-danger')

    if flask.request.method == 'GET':
        return flask.render_template('create.html',
                                     submit_button_text='CREATE A MONSTER',
                                     user_id=flask.session['user_id'])

    elif flask.request.method == 'POST':
        monster_data = monster_input.gather_monster_data(flask.request.form)

        # Validate input
        not_null_fields = [monster_data['name'],
                           monster_data['diet'],
                           monster_data['enjoys']]

        for user_input in not_null_fields:
            if len(user_input) < 1:
                return ('', 204)

        create_response = database_operations.create_monster(monster_data, db_session)
        return create_response


@app.route('/edit/<int:monster_id>', methods=['GET', 'POST'])
def edit_monster(monster_id):
    if 'user_id' not in flask.session:
        return flask.redirect('/signin?action=user_login&result=alert-danger')

    monster_auth_result = database_operations.authorize_monster_change(monster_id,
                                                                       db_session)

    # Check for error response
    if type(monster_auth_result) != Monster:
        return monster_auth_result
    else:
        monster = monster_auth_result

    if flask.request.method == 'GET':
        return flask.render_template('create.html',
                                     name=monster.name,
                                     intentions=monster.intentions,
                                     diet=monster.diet,
                                     enjoys=monster.enjoys,
                                     picture_url=monster.picture,
                                     submit_button_text='SUBMIT EDIT')

    elif flask.request.method == 'POST':
        monster_data = monster_input.gather_monster_data(flask.request.form)
        edit_response = database_operations.modify_monster(monster,
                                                           monster_data,
                                                           db_session)
        return edit_response


@app.route('/delete/<int:monster_id>', methods=['POST'])
def delete_monster(monster_id):
    if 'user_id' not in flask.session:
        return flask.redirect('/signin?action=user_login&result=alert-danger')
    monster = database_operations.authorize_monster_change(monster_id,
                                                           db_session)

    try:
        db_session.delete(monster)
        db_session.commit()
        return flask.redirect('/?action=monster_delete&result=alert-success')

    except sqlalchemy.exc.SQLAlchemyError as e:
        db_session.rollback()
        return flask.redirect('/?action=monster_delete&result=alert-danger')


@app.route('/signin')
def sign_in():
    if 'user_id' not in flask.session:
        action = flask.request.args.get('action')
        result = flask.request.args.get('result')
        if action:
            alert_text = user_messages['messages'][action].get(result)
        else:
            alert_text = ''
        session_token = login.set_session_token()
        return flask.render_template('signup.html',
                                     session_token=session_token,
                                     alert_class=result,
                                     alert_text=alert_text)
    else:
        # If user is logged in, return to main page
        return flask.redirect('/')


@app.route('/api/monsters', methods=['GET'])
def monsters():
    monsters = db_session.query(Monster).all()
    monsters_serialized = [monster.serialize for monster in monsters]

    return flask.jsonify(monsters=monsters_serialized)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    login_response = login.third_party_login('facebook', db_session)
    return login_response


@app.route('/gconnect', methods=['POST'])
def gconnect():
    login_response = login.third_party_login('google', db_session)
    return login_response


@app.route('/logout')
def logout():
    logout_response = login.third_party_logout()
    return logout_response


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.config.from_pyfile('monster_config.py')
    app.run(host='0.0.0.0', port=5000)
