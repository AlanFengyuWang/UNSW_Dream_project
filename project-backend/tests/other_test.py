'''
Authors: 
    Alec Dudley-Bestow, z5260201
    Dionne So, z5310329

Date: 16 March 2021
'''

import json
import pytest
import jwt

from src.error import InputError, AccessError
from src.other import clear, search, admin_userpermission_change, admin_user_remove, notifications_get
from src.user import user_profile
from src.auth import auth_login, auth_register, get_data
from src.channels import channels_create, channels_listall
from src.channel import channel_messages, channel_invite
from src.message import message_send, message_senddm
from tests.user_test import users, invalid_user, channels
from src.dm import dm_create, dm_invite
#clear is tested throughout all later functions, this is a sanity check
def test_clear():
    assert clear() == json.dumps({})

def test_search_long_string(users):
    with pytest.raises(InputError):
        search(users['user1']['token'], 'x'*1001)

#test can use empty string to search for all messages
def test_search_empty_string(users, channels):
    resp = search(users['user1']['token'], "")
    #check that returns from both public and private channels
    assert resp['messages'][1]['message'] == 'alsomessage'
    assert resp['messages'][0]['message'] == 'thisisamessage'
    assert len(resp['messages']) == 2

#test that can search for a specific message
def test_search_specific_string(users, channels):    
    resp = search(users['user1']['token'], "thisis")
    
    assert len(resp['messages']) == 1
    assert resp['messages'][0]['message'] == 'thisisamessage'

#test that returns empty list when no messages were sent
def test_no_messages(users):
    resp = search(users['user1']['token'], "")
    assert not resp['messages']
        
#test that removing a user complies with spec
def test_admin(users, channels):
    admin_user_remove(users['user1']['token'], users['user3']['auth_user_id'])
    with pytest.raises(InputError):
        auth_login('email2@email.com', 'password')
    resp = channel_messages(users['user1']['token'], channels['channel3']['channel_id'], 0)
    assert resp['messages'][0]['message'] == 'Removed user'
    user_profile(users['user1']['token'], users['user3']['auth_user_id'])['user']
    
#test that cannot remove when not an owner
def test_admin_not_auth(users):
    with pytest.raises(AccessError):
        admin_user_remove(users['user2']['token'], users['user3']['auth_user_id'])

#test that cannot remove the last owner
def test_admin_remove_only(users):
    with pytest.raises(InputError):
        admin_user_remove(users['user1']['token'], users['user1']['auth_user_id'])

#test that cannot remove an invalid user
def test_admin_remove_invalid_user(invalid_user):
    with pytest.raises(InputError):
        admin_user_remove(invalid_user['valid']['token'], invalid_user['invalid']['auth_user_id'])

#test that changing the permission works
def test_admin_change(users):
    admin_userpermission_change(users['user1']['token'], users['user2']['auth_user_id'], 1)
    admin_user_remove(users['user2']['token'], users['user3']['auth_user_id'])

#test that cannot change to an invalid permission
def test_admin_change_invalid_permission(users):
    with pytest.raises(InputError):
        admin_userpermission_change(users['user1']['token'], users['user2']['auth_user_id'], 123)

#test that throws error when given an invalid user
def test_admin_change_invalid_user(invalid_user):
    with pytest.raises(InputError):
        admin_userpermission_change(invalid_user['valid']['token'], \
            invalid_user['invalid']['auth_user_id'], 1)

#test cannot remove permissions of the only owner
def test_admin_change_only_owner(users):
    with pytest.raises(InputError):
        admin_userpermission_change(users['user1']['token'], users['user1']['auth_user_id'], 2)

#test that cannot change permissions if not an owner
def test_admin_change_not_owner(users):
    with pytest.raises(AccessError):
        admin_userpermission_change(users['user2']['token'], users['user3']['auth_user_id'], 1)

@pytest.fixture
def register_input():
    clear()
    return {
        #user 1
        'email': 'validemail@qq.com',
        'password': 'validpassword',
        'name_first': 'userfirstname',
        'name_last': 'userlastname'}

@pytest.fixture
def user_create(register_input):
    clear()
    #Send to one person
    #1):Create accounts
    user2 = {
        'email': 'validemailone@qq.com',
        'password': 'validpasswordone',
        'name_first': 'userfirstnameone',
        'name_last': 'userlastnameone'
    }
    user3 = {
        'email': 'validemailtwo@qq.com',
        'password': 'validpasswordtwo',
        'name_first': 'userfirstnametwo',
        'name_last': 'userlastnametwo'
    }
    user4 = {
        'email': 'validemailthree@qq.com',
        'password': 'validpasswordthree',
        'name_first': 'userfirstnamethree',
        'name_last': 'userlastnamethree'
    }
    #Create accounts
    user1_info = auth_register(**register_input)
    user2_info = auth_register(**user2)
    user3_info = auth_register(**user3)
    user4_info = auth_register(**user4)
    return user1_info, user2_info, user3_info, user4_info

@pytest.fixture
def handle_create(user_create):
    user1_info, user2_info, user3_info, user4_info = user_create
    user1_handle = user_profile(user1_info['token'], user1_info['auth_user_id'])['user']['handle_str']
    user2_handle = user_profile(user2_info['token'], user2_info['auth_user_id'])['user']['handle_str']
    user3_handle = user_profile(user3_info['token'], user3_info['auth_user_id'])['user']['handle_str']
    user4_handle = user_profile(user4_info['token'], user4_info['auth_user_id'])['user']['handle_str']
    return user1_handle, user2_handle, user3_handle, user4_handle

def assert_channelInvite_notificatoin(function, channel_id, inviter_handle, channel_name):
    assert function['notifications'] == \
        [{
            "channel_id" : channel_id,
            "dm_id" : -1,
            "notification_message" : f"{inviter_handle} added you to {channel_name}"
        }]

def assert_tag_notificatoin(function, channel_id, inviter_handle, sender_handle, message, channel_name):
    assert function['notifications'] == \
        [{
            "channel_id" : channel_id,
            "dm_id" : -1,
            "notification_message" : f"{sender_handle} tagged you in {channel_name}:" + ' ' + message[0:20]
        },
        {
            "channel_id" : channel_id,
            "dm_id" : -1,
            "notification_message" : f"{inviter_handle} added you to {channel_name}"
        }]

def assert_notification_len(function, length):
    assert len(function['notifications']) == length

def test_channel_invite_notification(user_create, handle_create):

    '''
    Register user1, user2, user3, user 1 create channel, 
    user1 sends welcome message to the channel, expecting user2, user3, user4 receives the invite notification
    user2 tags user1, user3 more than 20 messages to the channel, expecting user1, user3 receives only 20 notifications
    Expecting user4 receives no spasm message from the channel because he is not tagged by user2

    parameters: 
        (tuple) user_create - user1, user2, user3's info 

    return: None
    '''
    #Getting registered users' info
    user1_info, user2_info, user3_info, user4_info = user_create
    user1_handle, user2_handle, user3_handle, _ = handle_create

    #1)user1 created channel and invite user 2, user3, user4
    channel_id = channels_create(user1_info['token'], 'Private Channel', True)['channel_id']
    channel_invite(user1_info['token'], channel_id, user2_info['auth_user_id'])
    channel_invite(user1_info['token'], channel_id, user3_info['auth_user_id'])
    channel_invite(user1_info['token'], channel_id, user4_info['auth_user_id'])
    #Check the notification for every users
    assert_channelInvite_notificatoin(notifications_get(user2_info['token']), channel_id, user1_handle, 'Private Channel')
    assert_channelInvite_notificatoin(notifications_get(user3_info['token']), channel_id, user1_handle, 'Private Channel')
    assert_channelInvite_notificatoin(notifications_get(user4_info['token']), channel_id, user1_handle, 'Private Channel')
    #2)user1 tagged the user2, user3
    message_send(user1_info['token'], channel_id, f'Hello! Welcome to my channel!@{user2_handle} @{user3_handle}')
    message = f"Hello! Welcome to my channel!@{user2_handle} @{user3_handle}"
    assert_tag_notificatoin(notifications_get(user2_info['token']), channel_id, user1_handle, user1_handle, message, 'Private Channel')
    assert_tag_notificatoin(notifications_get(user3_info['token']), channel_id, user1_handle, user1_handle, message, 'Private Channel')
    assert_channelInvite_notificatoin(notifications_get(user4_info['token']), channel_id, user1_handle, 'Private Channel')
    
    #3)User 4 is angry, he send in total of 23 messagess to user 1, the result should only show the first 20 messages
    #Check only display the first 20 notifications
    for _ in range(0, 23):
        message_send(user4_info['token'], channel_id, f'Hello! Welcome to my channel!@{user1_handle}')
    assert_notification_len(notifications_get(user1_info['token']), 20)
    assert_notification_len(notifications_get(user2_info['token']), 2)
    assert_notification_len(notifications_get(user3_info['token']), 2)
    assert_notification_len(notifications_get(user4_info['token']), 1)

def test_invalid_tag_target(user_create, handle_create):
    user1_info, _, _, user4_info = user_create
    _, _, _, user4_handle = handle_create
    #user 1 created a channel, invited user2, user2 try to tag user 3 who's not in the channle
    channel_id = channels_create(user1_info['token'], 'Private Channel', True)['channel_id']

    message = f"You should not receive my message @{user4_handle}"
    message_send(user1_info['token'], channel_id, message)
    assert notifications_get(user4_info['token'])['notifications'] == []

def test_dm_invite_notification(user_create, handle_create):
    #Getting registered users' info
    user1_info, user2_info, user3_info, _ = user_create
    user1_handle, user2_handle, _, _ = handle_create

    #the DM is directed to user2, and then invite the user3 to join 
    dm_info = dm_create(user1_info['token'], [user2_info['auth_user_id']])
    dm_invite(user1_info['token'], dm_info['dm_id'], user3_info['auth_user_id'])

    #The user1 send one message to the dm:
    message_senddm(user1_info['token'], dm_info['dm_id'], 'a'*50 + f'@{user2_handle}')['message_id']
    assert notifications_get(user2_info['token'])['notifications'] == \
        [{
            "channel_id" : -1,
            "dm_id" : dm_info['dm_id'],
            "notification_message" : f"{user1_handle} tagged you in {dm_info['dm_name']}: " + 'a'*20
        },
        {
            "channel_id" : -1,
            "dm_id" : dm_info['dm_id'],
            "notification_message" : f"{user1_handle} added you to {dm_info['dm_name']}"
        }]
    
