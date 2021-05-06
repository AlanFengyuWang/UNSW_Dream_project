'''
Authors:
    Justin Wu, z5316037
    William Zheng, z5313015

Date: 19 March 2021
'''
import pytest
import requests
import json
from src import config
from src.error import InputError, AccessError

ACCESS_ERROR = 403
INPUT_ERROR = 400

# --------------------------------------------------------------------------------------- #
# ----------------------------- Fixtures for Registering Users -------------------------- #
# --------------------------------------------------------------------------------------- #
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

@pytest.fixture
def users():
    '''
    Returns two registered users.
    '''
    requests.delete(config.url + 'clear/v1')
    user1 = requests.post(config.url + 'auth/register/v2', json = register_users()['user1']).json()
    user2 = requests.post(config.url + 'auth/register/v2', json = register_users()['user2']).json()
    return {
        'user1': user1,
        'user2': user2
    }

# --------------------------------------------------------------------------------------- #
# ----------------------------- Fixtures for Creating Channels -------------------------- #
# --------------------------------------------------------------------------------------- #

@pytest.fixture
def channels_create(users):
    '''
    Previously registered user1 creates a public & private channel.
    '''
    public = requests.post(config.url + 'channels/create/v2', json = {
        'token': users['user1']['token'],
        'name': 'Public Channel',
        'is_public': True
    }).json()
    private = requests.post(config.url + 'channels/create/v2', json = {
        'token': users['user1']['token'],
        'name': 'Private Channel',
        'is_public': False
    }).json()

    return (public, private)

# --------------------------------------------------------------------------------------- #
# ----------------------------- Testing Channels Create & List -------------------------- #
# --------------------------------------------------------------------------------------- #

#Channel list to be returned.
def list_channels(channel1, channel2):
    return {
        'channels': [
            {
                'channel_id': channel1['channel_id'],
                'name': 'Public Channel'
            },
            {
                'channel_id': channel2['channel_id'],
                'name': 'Private Channel'
            },
        ]
    }

def check_list_channels(user, channels_list):
    assert requests.get(config.url + 'channels/list/v2', \
        params={'token': user['token']}).json() == channels_list

def test_check_channel_list(users, channels_create):
    channel1, channel2 = channels_create
    channels_list = list_channels(channel1, channel2)

    check_list_channels(users['user1'], channels_list)

def test_channels_create_inputerror(users):
    invalid_param1 = {
        'token': users['user1']['token'],
        'name': 'Pub'*20,
        'is_public': True
    }
    invalid_param2 = {
        'token': users['user1']['token'],
        'name': 'x'*21,
        'is_public': False
    }
    assert requests.post(config.url + 'channels/create/v2', \
        json = invalid_param1).status_code == INPUT_ERROR
    assert requests.post(config.url + 'channels/create/v2', \
        json = invalid_param2).status_code == INPUT_ERROR

def test_channels_list(users, channels_create):
    user1 = users['user1']
    user2 = users['user2']
    channel1, channel2 = channels_create

    requests.post(config.url + 'channel/join/v2', json = {
        'token': user2['token'],
        'channel_id': channel1['channel_id']
    })

    requests.post(config.url + 'channel/invite/v2', json = {
        'token': user1['token'],
        'channel_id': channel2['channel_id'],
        'u_id': user2['auth_user_id']
    })

    channels_list = list_channels(channel1, channel2)
    check_list_channels(users['user2'], channels_list)


def test_channels_listall(users, channels_create):
    channel1, channel2 = channels_create

    channels_list = list_channels(channel1, channel2)
    check_list_channels(users['user1'], channels_list)
