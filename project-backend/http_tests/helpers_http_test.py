import pytest
import requests
import json
from src import config
from src.error import InputError, AccessError
import time, threading
from datetime import timezone, timedelta, datetime
from src.config import url

# --------------------------------------------------------------------------------------- #
# ----------------------------- Helpers for Message ------------------------------------- #
# --------------------------------------------------------------------------------------- #\
def send_message(token, channel_id, message):
    resp = requests.post(config.url + 'message/send/v2', json = {
        'token': token,
        'channel_id': channel_id,
        'message': message
    })
    return resp.json()

def send_messagelater(token, channel_id, message, time_sent):
    resp = requests.post(config.url + 'message/sendlater/v1', json = {
        'token': token,
        'channel_id': channel_id,
        'message': message,
        'time_sent': time_sent
    })
    return resp.json()

def send_messagelaterdm(token, dm_id, message, time_sent):
    resp = requests.post(config.url + 'message/sendlaterdm/v1', json = {
        'token': token,
        'dm_id': dm_id,
        'message': message,
        'time_sent': time_sent
    })
    return resp.json()

def get_dm_messages(token, dm_id, start):
    resp = requests.get(config.url + 'dm/messages/v1', params = {
        'token': token,
        'dm_id': dm_id,
        'start': start
    })
    return resp.json()

def get_channel_messages(token, channel_id, start):
    resp = requests.get(config.url + 'channel/messages/v2', params = {
        'token': token,
        'channel_id': channel_id,
        'start': start
    })
    return resp.json()

def get_user_profile(token, u_id):
    resp = requests.get(config.url + 'user/profile/v2', params={
        'token': token,
        'u_id' : u_id
    })
    return resp.json()['user']

# --------------------------------------------------------------------------------------- #
# ----------------------------- Helpers for Registering Users -------------------------- #
# --------------------------------------------------------------------------------------- #
@pytest.fixture
def user_register():
    requests.delete(config.url + 'clear/v1')
    return {
        'user1': {
            'email' : 'useremail@email.com',
            'password' : 'validpassword',
            'name_first' : 'user',
            'name_last' : 'test'
        },
        'user2':{
            'email': 'firstlast@gmail.com',
            'password': 'password321',
            'name_first': 'Firsttwo' ,
            'name_last': 'Lasttwo'
        },
        'user3':{
            'email': 'secondlast@gmail.com',
            'password': 'password3212',
            'name_first': 'Firstthree' ,
            'name_last': 'Lastthree'
        },
        'user4':{
            'email': 'thirdlast@gmail.com',
            'password': 'password321',
            'name_first': 'Firstfour' ,
            'name_last': 'Lastfour'
        }
    }

@pytest.fixture
def users():
    '''
    Returns two registered users.
    '''
    requests.delete(config.url + 'clear/v1')
    user1 = requests.post(config.url + 'auth/register/v2', json = register_users()['user1']).json()
    user2 = requests.post(config.url + 'auth/register/v2', json = register_users()['user2']).json()
    return (user1, user2)

@pytest.fixture
def spare_users():
    '''
    These are some extra users in additon
    to the 'users' fixture.
    '''    
    user3 = requests.post(config.url + 'auth/register/v2', json = {
        'email': 'MarcChee@gmail.com',
        'password': 'asldfkj34kj',
        'name_first': 'Marc' ,
        'name_last': 'Chee',
    }).json()
    
    user4 = requests.post(config.url + 'auth/register/v2', json = {
        'email': 'HaydenSmithies@gmail.com',
        'password': 'x384sdmfn34kj',
        'name_first': 'Hayden' ,
        'name_last': 'Smith',
    }).json()

    return (user3, user4)

def register_user(email, password, name_first, name_last):
    resp = requests.post(config.url + 'auth/register', json = {
        'email': email,
        'password': password,
        'name_first': name_first,
        'name_last': name_last
    })
    return resp.json()

def register_user_modified(user_info):
    resp = requests.post(config.url + '/auth/register/v2', json = {
        'email': user_info['email'],
        'password': user_info['password'],
        'name_first': user_info['name_first'],
        'name_last': user_info['name_last']
    })
    return resp.json()

def register_users():
    '''
    Returns a dictionary containing 2 users' details.
    '''
    return {
        'user1':{
            'email': 'authuser@gmail.com',
            'password': 'password321',
            'name_first': 'Auth' ,
            'name_last': 'User',
        },
        'user2':{
            'email': 'firstlast@gmail.com',
            'password': 'password321',
            'name_first': 'First' ,
            'name_last': 'Last',
        }
    }

# --------------------------------------------------------------------------------------- #
# ----------------------------- Helpers for Channels ------------------------------------ #
# --------------------------------------------------------------------------------------- #

@pytest.fixture
def channels_create(users):
    '''
    Previously registered user1 creates a public & private channel.
    '''
    user1, user2 = users
    public = requests.post(config.url + 'channels/create/v2', json = {
        'token': user1['token'],
        'name': 'Public Channel',
        'is_public': True
    }).json()['channel_id']

    private = requests.post(config.url + 'channels/create/v2', json = {
        'token': user1['token'],
        'name': 'Private Channel',
        'is_public': False
    }).json()['channel_id']

    # Priv Channel has user1 and user2
    requests.post(config.url + 'channel/invite/v2', json = {
        'token': user1['token'],
        'channel_id': private,
        'u_id': user2['auth_user_id']
    })

    return (public, private)

def create_channel(token, is_public, channel_name):
    resp = requests.post(config.url + 'channels/create/v2', json = {
        'token': token,
        'name': channel_name,
        'is_public': is_public
    })
    return resp.json()

def create_dm(token, u_ids):
    resp = requests.post(config.url + 'dm/create/v1', json = {
        'token': token,
        'u_ids': u_ids
    })
    return resp.json()

def channel_invite(token, channel_id, u_id):
    resp = requests.post(config.url + 'channel/invite/v2', json = {
        'token': token,
        'channel_id': channel_id,
        'u_id': u_id
    })
    return resp.json()

def dm_invite(token, dm_id, u_id):
    resp = requests.post(config.url + 'dm/invite/v1', json = {
        'token': token,
        'dm_id': dm_id,
        'u_id': u_id
    })
    return resp.json()

def channel_details(token, channel_id):
    resp = requests.get(config.url + 'channel/details/v2', params = {
        'token': token,
        'channel_id': channel_id
    })
    return resp.json()

# --------------------------------------------------------------------------------------- #
# ----------------------------- Helpers for Standups ------------------------------------ #
# --------------------------------------------------------------------------------------- #
def standup_create(token, channel_id, length):
    resp = requests.post(config.url + 'standup/start/v1', json = {
        'token': token,
        'channel_id': channel_id,
        'length': length
    })
    return resp.json()['time_finish']

def standup_active(token, channel_id):
    resp = requests.get(config.url + 'standup/active/v1', params = {
        'token': token,
        'channel_id': channel_id
    })
    return resp.json()

def standup_send(token, channel_id, message):
    resp = requests.post(config.url + 'standup/send/v1', json = {
        'token': token,
        'channel_id': channel_id,
        'message': message
    })
    return resp.json()

# --------------------------------------------------------------------------------------- #
# ----------------------------- Helpers for Timestamps ---------------------------------- #
# --------------------------------------------------------------------------------------- #
@pytest.fixture
def timestamps():
    valid_sending_time = datetime.now() + timedelta(seconds = 1.5)
    valid_timestamp = valid_sending_time.timestamp()
    invalid_sending_time = datetime.now() - timedelta(seconds = 1.5)
    invalid_timestamp = invalid_sending_time.replace(tzinfo=timezone.utc).timestamp()
    return (valid_timestamp, invalid_timestamp)


# --------------------------------------------------------------------------------------- #
# ----------------------------- Helpers for uploadPhoto --------------------------------- #
# --------------------------------------------------------------------------------------- #
def member_info(user_profile):
    return {
        'u_id': user_profile['u_id'],
        'email': user_profile['email'],
        'name_first': user_profile['name_first'],
        'name_last': user_profile['name_last'],
        'handle_str': user_profile['handle_str'],
    }

def uploadphoto(token, img_url, x_start, y_start, x_end, y_end):
    resp = requests.post(config.url + '/user/profile/uploadphoto/v1', params = {
        'token': token,
        'img_url': img_url,
        'x_start': x_start,
        'y_start': y_start,
        'x_end': x_end,
        'y_end': y_end
    })
    return resp.json()