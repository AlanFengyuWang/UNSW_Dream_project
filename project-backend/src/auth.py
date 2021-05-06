'''
Authors:
    Alec Dudley-Bestow, z5260201

Date:
    24 March 2021
'''

from src.error import InputError, AccessError
from src.config import url
import re
import json
import jwt
import hashlib
import random
import urllib.request
import datetime


SECRET = 'atotallysecuresecret'

#simplify reading data
def get_data():
    data = {}
    while True:
        with open('data.json', 'r') as datafile:
            try:
                data = json.load(datafile)
                break
            except:
                pass
    return data

# overwrite data.json with the given data
def write_data(data):
    with open('data.json', 'w') as datafile:
        json.dump(data, datafile, indent="")
    return {}

#return a hash string, used for passwords
def new_hash(string):
    return hashlib.sha256(string.encode()).hexdigest()

#generates a new session token
def generate_token(u_id, session_id):
    return jwt.encode({'u_id': u_id, 'session_id' : session_id}, \
        SECRET, algorithm='HS256')

def check_u_id(u_id, ignore_removed=False):
    '''
        checks if a given u_id is valid

    Arguments:
        u_id (integer) - a user's unique identifier

    Exceptions:
        InputError - occurs when the u_id doesn't match a user
        Exception - occurs when

    Return Value:
        Returns the index of the user in data['users']
    '''

    data = get_data()
    for i, user in enumerate(data['users']):
        if user['u_id'] == u_id:
            return i
    raise InputError(description=f'u_id: {u_id} does not exist')

def new_session_id(u_id):
    '''
        Takens in a user id and returns a new login session id

    Arguments:
        u_id (integer) - a user's unique identifier

    Exceptions:
        None

    Return Value:
        Returns the new session_id integer
    '''

    data = get_data()
    new_session_id = 1
    try:
        user = data['users'][check_u_id(u_id)]

        for session in user['sessions_list']:
            if session['session_id'] == new_session_id:
                new_session_id += 1
    except InputError:
        #if the user is being registered return 1
        pass
    return new_session_id

def check_token(token):
    '''
        Takes in a token and checks if it's valid, returns user index if it is valid

    Arguments:
        token (string) - a user's jwt session token

    Exceptions:
        AccessError - Occurs when the u_id or session_id doesn't match anything in data

    Return Value:
        Returns the index of the user that the token checks for in data['users']
    '''

    data = get_data()
    #print(f"token = {token}")
    token_structure = jwt.decode(token, SECRET, algorithms=['HS256'])
    try:
        user_index = check_u_id(token_structure['u_id'])
        if token_structure['session_id'] not in \
            [session['session_id'] for session in data['users'][user_index]['sessions_list']]:
            # print(data['users'][user_index]['sessions_list'])
            raise AccessError(description='invalid token')
    except InputError:
        raise AccessError(description='invalid token') from None
    return user_index

#checks if a handle is already in use
def handle_taken(handle):
    data = get_data()
    for user in data['users']:
        if user['handle_str'] == handle:
            return True
    return False

#checks if an id is already used
def id_taken(id_num):
    data = get_data()
    for user in data['users']:
        if user['u_id'] == id_num:
            return True
    return False

#checks if an email is already in use
def email_taken(email):
    data = get_data()
    for user in data['users']:
        if email == user['email']:
            return True
    return False

def valid_email(email):
    return re.search('^[a-zA-Z0-9]+[\\._]?[a-zA-Z0-9]+[@]\\w+[.]\\w{2,3}$', email)

def valid_name(name):
    return 1 <= len(name) <= 50

def generate_handle(name_first, name_last):
    '''
        Produces a new handle from a user's full name

    Arguments:
        name_first (string) - a user's first name
        name_last (string) - a user's first name

    Exceptions:
        None

    Return Value:
        Returns a new handle string
    '''
    handle = name_first.lower() + name_last.lower()
    if len(handle) > 20:
        handle = handle[:20]
    handle = handle.replace('@','')
    handle = handle.replace(' ','')
    if handle_taken(handle):
        i = 0
        while handle_taken(handle + str(i)):
            i += 1
        return handle + str(i)
    else:
        return handle

def auth_register(email, password, name_first, name_last):
    '''
        Takes in a users details and registers them with the database

    Arguments:
        email (string) - a user's email address
        password (string) - a user's chosen password
        name_first (string) - a user's given first name
        name_last (string) - a user's given last name
   
    Exceptions:
        InputError - Occurs when the email address is of invalid format
        InputError - Occurs when the email address is already being used
        InputError - Occurs when the password is less than 6 characters long
        InputError - Occurs when the either name isn't between 1 and 50 characters

    Return Value:
        Returns a jwt token for the user's session and the user's u_id in a dictionary
    '''
    if not valid_email(email):
        raise InputError(description="The email is not valid")

    if email_taken(email):
        raise InputError(description="The email is repeated")

    if len(password) < 6:
        raise InputError(description="The password is smaller than 6")

    if not valid_name(name_first):
        raise InputError(description="The first name is not valid")

    if valid_name(name_last) == False:
        raise InputError(description="The last name is not valid")

    #Generate unique numbers for id
    id_num = 1
    while id_taken(id_num):
        id_num += 1
    session_id = new_session_id(id_num)
    data = get_data()

    permission_id = 2
    #make first user an owner
    if not data['users']:
        permission_id = 1
    ts = datetime.datetime.now().timestamp()

    data['users'].append({
        'u_id':id_num, 
        'name_first': name_first, 
        'name_last': name_last, 
        'email': email, 
        'password': new_hash(password), 
        'profile_img_url': new_img_name(id_num),
        'handle_str': generate_handle(name_first, name_last),
        'sessions_list' : [{'session_id' : session_id}],
        'notifications' : [],
        'permission_id' : permission_id,
        'reset_code' : '',
        'channels_joined' : [{'num_channels_joined' : 0, 'time_stamp' : ts}],
        'dms_joined' : [{'num_dms_joined' : 0, 'time_stamp' : ts}],
        'messages_sent' : [{'num_messages_sent' : 0, 'time_stamp' : ts}]
    })
    write_data(data)
    return {'token' : generate_token(id_num, session_id), 'auth_user_id' : id_num}

def auth_login(email, password):
    '''
        Takes in a users email and password and makes a new session for them

    Arguments:
        email (string) - a user's email address
        password (string) - a user's chosen password

    Exceptions:
        InputError - Occurs when the email address is of invalid format
        InputError - Occurs when the email address doesn't belong to anyone
        InputError - Occurs when the password is incorrect for the given email

    Return Value:
        Returns a jwt token for the user's session and the user's u_id in a dictionary
    '''
    data = get_data()
    if not valid_email(email):
        raise InputError(description="The email entered is not a valid email")
    elif not email_taken(email):
        raise InputError(description="The email enetered does not belong to a user")

    for user in data['users']:
        if user['email'] == email and user['password'] == new_hash(password):
            if user['name_first'] == 'Removed user' and user['name_last'] == 'Removed user':
                raise InputError(description='User has been removed')
            new_id = new_session_id(user['u_id'])
            user['sessions_list'].append({'session_id' : new_id})
            write_data(data)
            return {'token' : generate_token(user['u_id'], new_id), \
                'auth_user_id' : user['u_id']}
         
    raise InputError(description="The password is not correct")


def auth_logout(token):
    '''
        Takes in a user's session token and removes the session from data

    Arguments:
        token (string) - a user's session jwt token
 
    Exceptions:
        None
 
    Return Value:
        Returns a dictionary containing if the logout was successful or not
    '''
    try:
        user_index = check_token(token)
        session_id = jwt.decode(token, SECRET, algorithms=['HS256'])['session_id']
        data = get_data()
        for session in data['users'][user_index]['sessions_list']:
            if session['session_id'] == session_id:
                data['users'][user_index]['sessions_list'].remove(session)
                write_data(data)
        return {'is_success' : True}
    except (AccessError, InputError):
        return {'is_success' : False}    

#return the user with the correct reset code or throw an error if it doesn't exist
def check_reset_code(reset_code):
    data = get_data()
    for i, user in enumerate(data['users']):
        if user['reset_code'] == new_hash(reset_code):
            return i
    raise InputError(description='reset_code is not a valid reset code')

#generate a new reset code of random characters
def generate_reset_code():
    RESET_CODE_LENGTH = 50
    LOWER_CHARACTER = 33
    UPPER_CHARACTER = 126
    new_code = ''
    while True:
        new_code = ''.join([chr(random.randint(LOWER_CHARACTER,UPPER_CHARACTER))\
            for i in range(RESET_CODE_LENGTH)])
        try:
            check_reset_code(new_code)
        except:
            break
    
    return new_code

def auth_request_reset(email):
    '''
    generate a new reset code for a given email, and append it to their data

Arguments:
    email (string) - the email of the user that wants to reset their password

Exceptions:
    InputError  - Occurs when the email doesn't exist

Return Value:
    Returns a string of the new reset code
'''
    data = get_data()
    if not email_taken(email):
        raise InputError(description='email entered does not exist')
    reset_code = generate_reset_code()
    for i, user in enumerate(data['users']):
        if user['email'] == email:
            data['users'][i]['reset_code'] = new_hash(reset_code)
    write_data(data)
    return reset_code

def auth_reset_password(reset_code, new_password):
    '''
    resets a user's password based on a given reset_code

Arguments:
    new_password (string)    - the new password for the user
    reset_code (string)    - the reset code used to identify the user

Exceptions:
    InputError  - Occurs when the new password isn't long enough
    InputError  - Occurs when the reset code doesn't match

Return Value:
    Returns nothing
'''
    if len(new_password) < 6:
        raise InputError(description="The password is smaller than 6")
    user_index = check_reset_code(reset_code)
    data = get_data()
    data['users'][user_index]['reset_code'] = ""
    data['users'][user_index]['password'] = new_hash(new_password)
    #log out all sessions after reset
    data['users'][user_index]['sessions_list'] = []
    write_data(data)
    return {}


def new_img_name(u_id):
    '''
    This function can download a default picture to the file
    Returns:
        str - default.jpg
    '''
    try:
        _ = open("src/static/defaultimg.jpg")
    except:
            #retrieve a defualt pic from the website
        default_img_url = "https://thumbs.dreamstime.com/b/profile-anonymous-face-icon-gray-silhouette-person-male-businessman-profile-default-avatar-photo-placeholder-isolated-white-113133662.jpg"
        urllib.request.urlretrieve(default_img_url, "src/static/defaultimg.jpg")

    return f"{url}/static/defaultimg.jpg"

