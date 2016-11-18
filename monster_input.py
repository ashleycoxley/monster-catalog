import s3_storage
import flask


def gather_monster_data(form_input):
    monster_data = {}
    monster_data['name'] = form_input['name']
    monster_data['diet'] = form_input['diet']
    monster_data['enjoys'] = form_input['enjoys']
    monster_data['intentions'] = form_input['intentions']
    monster_data['creator'] = flask.session['user_id']

    validate_input(monster_data)
    encoded_picture = form_input.get('encoded_picture')
    picture_url = s3_storage.decode_and_add_picture(encoded_picture)
    monster_data['picture'] = picture_url

    return monster_data


def validate_input(monster_data):
    """Validate monster form input and stay on page if fields are empty.
    Form-validation user feedback is handled on the client side."""
    not_null_fields = [monster_data['name'],
                       monster_data['diet'],
                       monster_data['enjoys']]

    for user_input in not_null_fields:
            if len(user_input) < 1:
                return ('', 204)
