'''
Authors: Alec Dudley-Bestow, z5260201

Date: 16 March 2021
'''
import requests
import json
import pytest
from src import config
from http_tests.user_http_test import users, invalid_user, ACCESS_ERROR, INPUT_ERROR, channels

SEARCH = config.url + 'search/v2'
REMOVE = config.url + 'admin/user/remove/v1'
CHANGE = config.url + 'admin/userpermission/change/v1'

REGISTER = 'auth/register/v2'
CHANNEL_CREATE = '/channels/create/v2'
CHANNEL_INVITE = '/channel/invite/v2'
DM_CREATE = '/dm/create/v1'
DM_INVITE = '/dm/invite/v1'
USER_PROFILE = '/user/profile/v2'
NOTIFICATION = '/notifications/get/v1'
MESSAGE_SEND = '/message/send/v2'
NOTIFICATION = '/notifications/get/v1'
DM_SEND = '/message/senddm/v1'

CHANNEL_NAME = 'My Channel'

def test_clear():
    #clear is tested throughout all later functions, this is a sanity check
    resp = requests.delete(config.url + 'clear/v1')
    assert resp.text == json.dumps({})


#test that throws an input error with a too long string
def test_search_long_string(users):
    assert requests.get(SEARCH, \
    params={'token':users['user1']['token'], 'query_string' : 'x'*1001}).status_code == INPUT_ERROR

#test that when searching with an empty string it returns all messages
def test_search_empty_string(users, channels):
    resp = requests.get(SEARCH, \
        params={'token':users['user1']['token'], 'query_string' : ''}).json()
    assert resp['messages'][1]['message'] == 'alsomessage'
    assert resp['messages'][0]['message'] == 'thisisamessage'
    assert len(resp['messages']) == 2

#test that can be used to search for specific message
def test_search_specific_string(users, channels):
    resp = requests.get(SEARCH, \
        params={'token':users['user1']['token'], 'query_string' : 'thisis'}).json()
    assert resp['messages'][0]['message'] == 'thisisamessage'
    assert len(resp['messages']) == 1

#test that returns empty list when user posted no messages
def test_no_messages(users, channels):
    resp = requests.get(SEARCH, \
        params={'token':users['user2']['token'], 'query_string' : ''}).json()
    assert not resp['messages']

#tests that a removed user cannot login
def test_admin(users):
    requests.delete(REMOVE, json = {
        'token': users['user1']['token'], 
        'u_id' : users['user3']['auth_user_id']
    })
    
    assert requests.post(config.url + 'auth/login/v2', json = {
        'email' : 'email@email.com', \
        'password' : 'asdf'
    }).status_code == INPUT_ERROR

#test that a removed user's messages are replaced
def test_admin_removed_messages(users, channels):
    requests.delete(REMOVE, json = {
        'token':users['user1']['token'], 
        'u_id' : users['user3']['auth_user_id']
    })
    
    resp = requests.get(config.url + 'channel/messages/v2', params={
        'token' : users['user1']['token'],
        'channel_id' : channels['channel3']['channel_id'], 
        'start' : 0
        }).json()
        
    assert resp['messages'][0]['message'] == 'Removed user'

#tests that a user's profile can still be accessed after being removed
def test_admin_keep_profile(users):
    requests.delete(REMOVE, json = {
        'token':users['user1']['token'], 
        'u_id' : users['user3']['auth_user_id']
    })
    
    resp = requests.get(config.url + 'user/profile/v2', params={
        'token' : users['user1']['token'],
        'u_id' : users['user3']['auth_user_id']
    }).json()['user']
    assert resp['name_first'] == 'Removed user'

#test that cannot remove user if not admin
def test_admin_not_auth(users):
    requests.delete(REMOVE, json = {
        'token' : users['user2']['token'], 
        'u_id' : users['user3']['auth_user_id']
    }).status_code == ACCESS_ERROR

#test that admin cannot remove the only admin
def test_admin_only_auth(users):
    requests.delete(REMOVE, json = {
        'token' : users['user1']['token'], 
        'u_id' : users['user1']['auth_user_id']
    }).status_code == INPUT_ERROR

#test that admin cannot remove an invalid user
def test_admin_invalid_user(invalid_user):
    requests.delete(REMOVE, json = {
        'token' : invalid_user['valid']['token'], 
        'u_id' : invalid_user['invalid']['auth_user_id']
    }).status_code == INPUT_ERROR

#test that admin can change a user's permissions
def test_admin_change(users):
    requests.post(CHANGE, json = {
        'token' : users['user1']['token'],
        'u_id' : users['user2']['auth_user_id'],
        'permission_id' : 1
    })
    requests.delete(REMOVE, json = {
        'token':users['user2']['token'], 
        'u_id' : users['user3']['auth_user_id']
    })

#test that cannot change a user's permission to an invalid permission_id
def test_admin_change_invalid_permission(users):
    requests.post(CHANGE, json = {
        'token' : users['user1']['token'],
        'u_id' : users['user2']['auth_user_id'],
        'permission_id' : 123
    }).status_code == INPUT_ERROR

#test that cannot change permissions of an invalid user
def test_admin_change_invalid_user(invalid_user):
    requests.post(CHANGE, json = {
        'token' : invalid_user['valid']['token'],
        'u_id' : invalid_user['invalid']['auth_user_id'],
        'permission_id' : 1
    }).status_code == INPUT_ERROR

#test that admin cannot remove the owner permission of the last owner
def test_admin_change_only_owner(users):
    requests.post(CHANGE, json = {
        'token' : users['user1']['token'],
        'u_id' : users['user1']['auth_user_id'],
        'permission_id' : 1
    }).status_code == INPUT_ERROR

#test that admin can't change permissions if user is not authorized
def test_admin_change_not_owner(users):
    requests.post(CHANGE, json = {
        'token' : users['user3']['token'],
        'u_id' : users['user2']['auth_user_id'],
        'permission_id' : 1
    }).status_code == INPUT_ERROR
'''
Authors: Fengyu Wang, z5187561

Date: 3 April 2021
'''

def register_input():
    return {
        'user1': {
            'email': 'validemail@qq.com',
            'password': 'validpassword',
            'name_first': 'userfirstname',
            'name_last': 'userlastname'
        },
        'user2': {
            'email': 'validemailone@qq.com',
            'password': 'validpasswordone',
            'name_first': 'userfirstnameone',
            'name_last': 'userlastnameone'
        },
        'user3': {
            'email': 'validemailtwo@qq.com',
            'password': 'validpasswordtwo',
            'name_first': 'userfirstnametwo',
            'name_last': 'userlastnametwo'
        },
        'user4': {
            'email': 'validemailthree@qq.com',
            'password': 'validpasswordthree',
            'name_first': 'userfirstnamethree',
            'name_last': 'userlastnamethree'
        }
    }

@pytest.fixture
def user_info():
    requests.delete(config.url + 'clear/v1')
    user1 = requests.post(config.url + REGISTER, json = register_input()['user1']).json()
    user2 = requests.post(config.url + REGISTER, json = register_input()['user2']).json()
    user3 = requests.post(config.url + REGISTER, json = register_input()['user3']).json()
    user4 = requests.post(config.url + REGISTER, json = register_input()['user4']).json()
    return {'user1': user1, 'user2': user2, 'user3': user3, 'user4': user4}

@pytest.fixture
def handle_info(user_info):
    user1_profile = requests.get(config.url + USER_PROFILE, \
    params={'token': user_info['user1']['token'], 'u_id': user_info['user1']['auth_user_id']}).json()['user']

    user2_profile = requests.get(config.url + USER_PROFILE, \
    params={'token': user_info['user2']['token'], 'u_id': user_info['user2']['auth_user_id']}).json()['user']

    user3_profile = requests.get(config.url + USER_PROFILE, \
    params={'token': user_info['user3']['token'], 'u_id': user_info['user3']['auth_user_id']}).json()['user']

    user4_profile = requests.get(config.url + USER_PROFILE, \
    params={'token': user_info['user4']['token'], 'u_id': user_info['user4']['auth_user_id']}).json()['user']

    return {"user1_handle": user1_profile['handle_str'], \
    'user2_handle': user2_profile['handle_str'], "user3_handle": user3_profile['handle_str'], \
    "use4_handle": user4_profile['handle_str']}

def get_notification(token):
    return requests.get(config.url + NOTIFICATION, params=\
    {
        'token': token
    }).json()

def expected_invite_notification_result(channel_id, dm_id, inviter_handle, channel_name = None):
    if not channel_name:
        return {
            'notifications': 
            [{
                'channel_id': channel_id, 
                'dm_id': dm_id, 
                'notification_message': f"{inviter_handle} added you to {CHANNEL_NAME}"
            }]
        }
    else:
        return {
            'notifications': 
            [{
                'channel_id': channel_id, 
                'dm_id': dm_id, 
                'notification_message': f"{inviter_handle} added you to {channel_name}"
            }]
        }

def expected_tag_notification_result(channel_id, dm_id, inviter_handle, sender_handle, message):
    return {
        'notifications': 
        [{
            'channel_id': channel_id, 
            'dm_id': dm_id, 
            'notification_message': f"{inviter_handle} tagged you in {CHANNEL_NAME}:" + ' ' + message[0:20]
        },
        {
            "channel_id" : channel_id,
            "dm_id" : dm_id,
            'notification_message': f"{inviter_handle} added you to {CHANNEL_NAME}"
        }]
    }

def test_channel_notification(user_info, handle_info):

    #User 1 create a channnel and invite user2, user3, user4 to the channel
    channel_info = requests.post(config.url + CHANNEL_CREATE, \
    json={'token': user_info['user1']['token'], 'name': CHANNEL_NAME, 'is_public': True}).json()

    requests.post(config.url + CHANNEL_INVITE, \
    json={'token': user_info['user1']['token'], 'channel_id': channel_info['channel_id'],\
    'u_id': user_info['user2']['auth_user_id']}).json()

    requests.post(config.url + CHANNEL_INVITE, \
    json={'token': user_info['user1']['token'], 'channel_id': channel_info['channel_id'],\
    'u_id': user_info['user3']['auth_user_id']}).json()

    requests.post(config.url + CHANNEL_INVITE, \
    json={'token': user_info['user1']['token'], 'channel_id': channel_info['channel_id'],\
    'u_id': user_info['user4']['auth_user_id']}).json()

    #Check the received notifications from each user
    user1_notification = get_notification(user_info['user1']['token'])
    user2_notification = get_notification(user_info['user2']['token'])
    user3_notification = get_notification(user_info['user3']['token'])
    user4_notification = get_notification(user_info['user4']['token'])

    assert user1_notification == {'notifications': []}
    assert user2_notification == expected_invite_notification_result(channel_info['channel_id'], -1, \
    handle_info['user1_handle'])
    assert user3_notification == expected_invite_notification_result(channel_info['channel_id'], -1, \
    handle_info['user1_handle'])
    assert user4_notification == expected_invite_notification_result(channel_info['channel_id'], -1, \
    handle_info['user1_handle'])

    # User 1 sends welcome message to the channel, tagged user2, user3
    inviter_handle = handle_info['user1_handle']
    user2_handle = handle_info['user2_handle']
    user3_handle = handle_info['user3_handle']
    requests.post(config.url + MESSAGE_SEND, \
    json={
        'token': user_info['user1']['token'],
        'channel_id': channel_info['channel_id'],
        'message': f'Hello! Welcome to my channel!@{user2_handle} @{user3_handle}'
    }).json()

    user2_notification = get_notification(user_info['user2']['token'])
    user3_notification = get_notification(user_info['user3']['token'])
    message = f"Hello! Welcome to my channel!@{user2_handle} @{user3_handle}"
    assert user2_notification == expected_tag_notification_result(channel_info['channel_id'], -1, \
    inviter_handle, user2_handle, message)
    assert user3_notification == expected_tag_notification_result(channel_info['channel_id'], -1, \
    inviter_handle, user3_handle, message)


def test_dm_invite_notification(user_info, handle_info):
    #the DM is directed to user2, and then invite the user3 to join
    dm_info = requests.post(config.url + DM_CREATE, \
    json={'token': user_info['user1']['token'], 'u_ids': [user_info['user2']['auth_user_id']]}).json()
    requests.post(config.url + DM_INVITE, \
    json={'token': user_info['user1']['token'], 
    'dm_id': dm_info['dm_id'],
    'u_id': user_info['user3']['auth_user_id']}).json() 

    user2_notification = get_notification(user_info['user2']['token'])
    user3_notification = get_notification(user_info['user3']['token'])
    assert user2_notification == expected_invite_notification_result(-1, dm_info['dm_id'], \
    handle_info['user1_handle'], dm_info['dm_name'])
    assert user3_notification == expected_invite_notification_result(-1, dm_info['dm_id'], \
    handle_info['user1_handle'], dm_info['dm_name'])

    user1_handle = handle_info['user1_handle']
    user3_handle = handle_info['user3_handle']

    dm_name = dm_info['dm_name']

    #The user1 send one message to the dm:
    requests.post(config.url + DM_SEND, json=\
    {
        'token': user_info['user1']['token'],
        'dm_id': dm_info['dm_id'],
        'message': 'a'*20 + f'@{user3_handle}'
    }).json()

    user3_notification = get_notification(user_info['user3']['token'])

    assert user3_notification == {
        'notifications': 
        [{
            'channel_id': -1, 
            'dm_id': dm_info['dm_id'], 
            'notification_message': f"{user1_handle} tagged you in {dm_name}: " + 'a'*20
        }, 
        {
            'channel_id': -1, 
            'dm_id': dm_info['dm_id'], 
            'notification_message': f"{user1_handle} added you to {dm_name}"}
        ]}
