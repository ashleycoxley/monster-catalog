import flask
import sqlalchemy

from models import Base, Monster
import monster_input
import database_operations
import login


app = flask.Flask(__name__)

engine = sqlalchemy.create_engine('postgres:///monstercatalog')
Base.metadata.bind = engine

DBSession = sqlalchemy.orm.sessionmaker(bind=engine)
db_session = DBSession()


@app.route('/')
def main_page():
    user_id = flask.session.get('user_id')
    monsters = db_session.query(Monster).limit(20).all()
    return flask.render_template('main.html',
                                 monsters=monsters,
                                 user_id=user_id)


@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_id' not in flask.session:
        return flask.redirect('/signin')

    if flask.request.method == 'GET':
        return flask.render_template('create.html',
                                     submit_button_text='CREATE A MONSTER')

    elif flask.request.method == 'POST':
        monster_data = monster_input.gather_monster_data(flask.request.form)
        create_response = database_operations.create_monster(monster_data, db_session)
        return create_response


@app.route('/edit/<int:monster_id>', methods=['GET', 'POST'])
def edit_monster(monster_id):
    monster = database_operations.authorize_monster_change(monster_id,
                                                           db_session)
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
    monster = database_operations.authorize_monster_change(monster_id,
                                                           db_session)
    try:
        db_session.delete(monster)
        db_session.commit()
        # TODO add success message here in template
        return flask.redirect('/')

    except sqlalchemy.exc.SQLAlchemyError as e:
        db_session.rollback()
        # TODO add error message here in template
        return flask.redirect('/')


@app.route('/api/monsters', methods=['GET'])
def monsters():
    monsters = db_session.query(Monster).all()
    monsters_serialized = [monster.serialize for monster in monsters]

    return flask.jsonify(monsters=monsters_serialized)


@app.route('/signin')
def sign_in():
    if 'user_id' not in flask.session:
        session_token = login.set_session_token()
        return flask.render_template('signup.html',
                                     session_token=session_token)
    else:
        # If user is logged in, return to main page
        return flask.redirect('/')


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