import s3_storage
import flask


def gather_monster_data(form_input):
    monster_data = {}
    monster_data['name'] = form_input['name']
    monster_data['diet'] = form_input['diet']
    monster_data['enjoys'] = form_input['enjoys']
    monster_data['intentions'] = form_input['intentions']
    monster_data['creator'] = flask.session['user_id']

    encoded_picture = form_input.get('encoded_picture')
    picture_url = s3_storage.decode_and_add_picture(encoded_picture)
    monster_data['picture'] = picture_url

    return monster_data
