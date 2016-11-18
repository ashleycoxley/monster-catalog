import flask
import sqlalchemy
from models import User, Monster
import datetime


def create_user(user_data, db_session):
    user = User(
        name=user_data['name'],
        email=user_data['email'],
        picture=user_data['picture']
        )
    try:
        db_session.add(user)
        db_session.commit()
    except sqlalchemy.ext.SQLAlchemyError:
        db_session.rollback()
        return ('User database error', 401)
        # TODO redirect and add error message
    user = db_session.query(User).filter_by(email=user_data['email']).one()
    return user.id


def get_user(user_id, db_session):
    user = db_session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id_by_email(email, db_session):
    try:
        user = db_session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def create_monster(monster_data, db_session):
    """Create new monster object."""
    monster = Monster(name=monster_data['name'],
                      diet=monster_data['diet'],
                      enjoys=monster_data['enjoys'],
                      creator=monster_data['creator'],
                      picture=monster_data['picture'],
                      intentions=monster_data['intentions'],
                      created_date=datetime.datetime.now()
                      )
    create_response = insert_update_monster(monster, db_session)
    return create_response


def modify_monster(monster, monster_data, db_session):
    """Modify existing monster object."""
    monster.name = monster_data['name']
    monster.diet = monster_data['diet']
    monster.enjoys = monster_data['enjoys']
    monster.picture = monster_data['picture']
    monster.intentions = monster_data['intentions']
    monster.edited_date = datetime.datetime.now()

    edit_response = insert_update_monster(monster, db_session)
    return edit_response


def insert_update_monster(monster, db_session):
    """Add or update database with a monster object."""
    try:
        db_session.add(monster)
        db_session.commit()
        return flask.jsonify({'result': 'success'})
    except sqlalchemy.exc.SQLAlchemyError as e:
        db_session.rollback()
        # Add error message here in template
        return flask.jsonify({'result': 'fail'})


def authorize_monster_change(monster_id, db_session):
    """Verify that user requesting to edit or delete a monster is the
    creator of that monster."""
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
