'''
Authors: 
    Justin Wu, z5316037
    William Zheng, z5313015

Date: 31 March 2021
'''
import pytest
import requests
import json
from src import config
from src.error import InputError, AccessError
from http_tests.helpers_http_test import create_channel, register_user, send_message,\
get_channel_messages, register_user_modified, send_messagelater, timestamps, user_register, channel_invite,\
channel_details, get_dm_messages, send_messagelaterdm, create_dm, dm_invite, send_messagelaterdm
from http_tests.channels_http_test import register_users, users, channels_create
from http_tests.other_http_test import test_clear
import time, threading
# from datetime import timezone, timedelta, datetime
ACCESS_ERROR = 403
INPUT_ERROR = 400

# --------------------------------------------------------------------------------------- #
# ----------------------------- Fixture for Dm_Create  ---------------------------------- #
# --------------------------------------------------------------------------------------- #
@pytest.fixture
def dms_create(users):
    '''
    Setting up 2 dms:
        - Dm from User1 to User2
        - Dm from User2 to User1 & User3 
    '''
    user1 = users['user1']
    user2 = users['user2']

    # Creating User3
    user3 = requests.post(config.url + 'auth/register/v2', json = {
        'email': 'MarcChee@gmail.com',
        'password': 'asldfkj34kj',
        'name_first': 'Marc' ,
        'name_last': 'Chee',
    }).json()

    dm1 = requests.post(config.url + 'dm/create/v1', json = {
        'token': user1['token'],
        'u_ids': [user2['auth_user_id']]
    }).json()

    dm2 = requests.post(config.url + 'dm/create/v1', json = {
        'token': user2['token'],
        'u_ids': [user1['auth_user_id'], user3['auth_user_id']]
    }).json()
    
    return {
        'dm1': dm1,
        'dm2': dm2,
        'user3': user3
    }
# --------------------------------------------------------------------------------------- #
# ----------------------------- Helper Function  ---------------------------------------- #
# --------------------------------------------------------------------------------------- #
def channel_messages_input(user, channel, start):
    '''
    Returns a list of recent messages.
    '''
    messages = requests.get(config.url + 'channel/messages/v2', \
        params={'token': user['token'], 'channel_id': channel['channel_id'], 'start': start}).json()
    return messages

def dm_messages_input(user, dm, start):
    '''
    Returns a list of recent messages.
    '''
    messages = requests.get(config.url + 'dm/messages/v1', \
        params={'token': user['token'], 'dm_id': dm['dm_id'], 'start': start}).json()
    return messages
# --------------------------------------------------------------------------------------- #
# ----------------------------- Testing Message Send ------------------------------------ #
# --------------------------------------------------------------------------------------- #
def test_message_send(users, channels_create):
    '''
    Tests the intended behavior of message send when
    a user sends a message to a channel they've created. 
    '''
    user1 = users['user1']
    channel, _ = channels_create

    # User1 sends a message to the channel
    message_id = requests.post(config.url + 'message/send/v2', json = {
        'token': user1['token'],
        'channel_id': channel['channel_id'],
        'message': 'Testing'
    }).json()['message_id']

    msg_list = channel_messages_input(user1, channel, 0)['messages'][0]

    assert message_id == msg_list['message_id']
    assert msg_list['message'] == 'Testing'
    assert msg_list['u_id'] == user1['auth_user_id']

def test_message_send_InputError(users, channels_create):
    '''
    Test message_send for InputError when message
    contains over 1000 characters. 
    '''
    user1 = users['user1']
    channel, _ = channels_create

    invalid_message = {
        'token': user1['token'],
        'channel_id': channel['channel_id'],
        'message': 'x'*1001
    }
    assert requests.post(config.url + 'message/send/v2', json=invalid_message).status_code == INPUT_ERROR

def test_message_send_AccessError(users, channels_create):
    '''
    Test message_send for AccessError when 
    the authorised user has not joined the channel 
    they are trying to post to.
    '''
    # User2 is the user who hasn't joined user1's channel
    user2 = users['user2']
    channel, _ = channels_create

    invalid_message = {
        'token': user2['token'],
        'channel_id': channel['channel_id'],
        'message': 'Hello'
    }
    assert requests.post(config.url + 'message/send/v2', json=invalid_message).status_code == ACCESS_ERROR

# --------------------------------------------------------------------------------------- #
# ----------------------------- Testing Message Edit ------------------------------------ #
# --------------------------------------------------------------------------------------- #
def test_message_edit(users, channels_create):
    '''
    Tests the intended behavior of message edit when
    a user edits a message they've sent to the channel
    they've created. 
    '''
    owner = users['user1']
    channel, _ = channels_create

    # Owner sends a message to the channel
    message_id = requests.post(config.url + 'message/send/v2', json = {
        'token': owner['token'],
        'channel_id': channel['channel_id'],
        'message': 'Helo Word'
    }).json()['message_id']

    # Owner edits their message
    requests.put(config.url + 'message/edit/v2', json = {
        'token': owner['token'],
        'message_id': message_id,
        'message': 'Hello World!'
    })

    msg_list = channel_messages_input(owner, channel, 0)['messages'][0]
    assert msg_list['message_id'] == message_id
    assert msg_list['message'] == 'Hello World!'
    assert msg_list['u_id'] == owner['auth_user_id']

def test_message_empty(users, channels_create):
    '''
    Tests the intended behavior of message edit when
    a user wants to edit a message with an empty string.
    '''
    owner = users['user1']
    channel, _ = channels_create

    message_id = requests.post(config.url + 'message/send/v2', json = {
        'token': owner['token'],
        'channel_id': channel['channel_id'],
        'message': 'Helo Word'
    }).json()['message_id']

    # Empty string should remove old message
    requests.put(config.url + 'message/edit/v2', json = {
        'token': owner['token'],
        'message_id': message_id,
        'message': ''
    })

    msg_list = channel_messages_input(owner, channel, 0)['messages'][0]
    assert msg_list['message_id'] == message_id
    assert msg_list['message'] == ''
    assert msg_list['u_id'] == owner['auth_user_id']

def test_message_edit_too_long(users, channels_create):
    '''
    Test message_edit for InputError when message
    contains over 1000 characters. 
    '''
    owner = users['user1']
    channel, _ = channels_create

    message_id = requests.post(config.url + 'message/send/v2', json = {
        'token': owner['token'],
        'channel_id': channel['channel_id'],
        'message': 'Hey'
    }).json()['message_id']

    invalid_message = {
        'token': owner['token'],
        'message_id': message_id,
        'message': 'a'*1001
    }
    assert requests.put(config.url + 'message/edit/v2', json=invalid_message).status_code == INPUT_ERROR

def test_edit_removed_message(users, channels_create):
    '''
    Test message_edit for InputError when message_id 
    refers to a deleted message.
    '''
    owner = users['user1']
    channel, _ = channels_create

    message_id = requests.post(config.url + 'message/send/v2', json = {
        'token': owner['token'],
        'channel_id': channel['channel_id'],
        'message': 'Hey'
    }).json()['message_id']

    # Message is removed from the channel
    requests.delete(config.url + 'message/remove/v1', json={
        'token': owner['token'],
        'message_id': message_id
    })

    assert requests.put(config.url + 'message/edit/v2', json={
        'token': owner['token'],
        'message_id': message_id,
        'message': 'Hello World!'
    }).status_code == INPUT_ERROR


def test_message_edit_not_auth_user(users, channels_create):
    '''
    Test message_edit for AccessError when message 
    with message_id was not sent by the authorised user 
    making the request.
    '''
    owner = users['user1']
    user2 = users['user2']
    channel, _ = channels_create

    # Owner sends a message
    message_id = requests.post(config.url + 'message/send/v2', json = {
        'token': owner['token'],
        'channel_id': channel['channel_id'],
        'message': 'Hey'
    }).json()['message_id']

    # User2 attempts to edit owner's message
    assert requests.put(config.url + 'message/edit/v2', json={
        'token': user2['token'],
        'message_id': message_id,
        'message': 'Hello World!'
    }).status_code == ACCESS_ERROR


def test_message_edit_not_channel_owner(users, channels_create):
    '''
    Test message_edit for AccessError when the authorised user 
    is not an owner of this channel (if it was sent to a channel) 
    or the **Dreams**.
    '''
    owner = users['user1']
    user2 = users['user2']
    channel, _ = channels_create

    # Owner invites user2 to channel.
    requests.post(config.url + 'channel/invite/v2', json = {
        'token': owner['token'],
        'channel_id': channel['channel_id'],
        'u_id': user2['auth_user_id']
    })

    # User2 sends a message to the channel.
    message_id = requests.post(config.url + 'message/send/v2', json = {
        'token': user2['token'],
        'channel_id': channel['channel_id'],
        'message': 'Hi'
    }).json()['message_id']

    # User2 shouldn't be able to edit message.
    assert requests.put(config.url + 'message/edit/v2', json={
        'token': user2['token'],
        'message_id': message_id,
        'message': 'Hi !!!'
    }).status_code == ACCESS_ERROR

# --------------------------------------------------------------------------------------- #
# ----------------------------- Testing Message SendDm ---------------------------------- #
# --------------------------------------------------------------------------------------- #
def test_message_senddm(users, dms_create, channels_create):
    '''
    Tests the intended behavior of message senddm when
    a user sends a message to a channel they've created. 
    '''
    user1 = users['user1']
    user3 = dms_create['user3']
    
    dm1 = dms_create['dm1']
    dm2 = dms_create['dm2']
    
    channel1, _ = channels_create

    # User1 sends a message to dm1
    message_id1 = requests.post(config.url + 'message/senddm/v1', json = {
        'token': user1['token'],
        'dm_id': dm1['dm_id'],
        'message': 'COMP1531'
    }).json()['message_id']
    
    msg_list1 = dm_messages_input(user1, dm1, 0)['messages'][0]

    assert message_id1 == msg_list1['message_id']
    assert msg_list1['message'] == 'COMP1531'
    assert msg_list1['u_id'] == user1['auth_user_id']

    # User3 sends a message to dm2
    message_id2 = requests.post(config.url + 'message/senddm/v1', json = {
        'token': user3['token'],
        'dm_id': dm2['dm_id'],
        'message': 'Testing'
    }).json()['message_id']

    msg_list2 = dm_messages_input(user3, dm2, 0)['messages'][0]

    assert message_id2 == msg_list2['message_id']
    assert msg_list2['message'] == 'Testing'
    assert msg_list2['u_id'] == user3['auth_user_id']

    # User1 sends same message sent to dm1 but to channel1
    message_id3 = requests.post(config.url + 'message/send/v2', json = {
        'token': user1['token'],
        'channel_id': channel1['channel_id'],
        'message': 'COMP1531'
    }).json()['message_id']

    msg_list3 = channel_messages_input(user1, channel1, 0)['messages'][0]

    assert message_id3 == msg_list3['message_id']
    assert msg_list3['message'] == 'COMP1531'
    assert msg_list3['u_id'] == user1['auth_user_id']

def test_message_senddm_too_long(users, dms_create):
    '''
    Test message_senddm for InputError when message
    contains over 1000 characters. 
    '''
    user1 = users['user1']
    user2 = users['user1']
    user3 = dms_create['user3']

    dm1 = dms_create['dm1']['dm_id']
    dm2 = dms_create['dm2']['dm_id']

    invalid_message1 = {
        'token': user1['token'],
        'dm_id': dm1,
        'message': 'a'*1001
    }
    invalid_message2 = {
        'token': user2['token'],
        'dm_id': dm2,
        'message': 'b'*1001
    }
    invalid_message3 = {
        'token': user3['token'],
        'dm_id': dm2,
        'message': 'c'*1001
    }

    assert requests.post(config.url + 'message/senddm/v1', json=invalid_message1).status_code == INPUT_ERROR
    assert requests.post(config.url + 'message/senddm/v1', json=invalid_message2).status_code == INPUT_ERROR
    assert requests.post(config.url + 'message/senddm/v1', json=invalid_message3).status_code == INPUT_ERROR

def test_message_senddm_auth_not_member(users, dms_create):
    '''
    Test message_senddm for AccessError when auth user
    is not a member of the DM they are trying to post to.
    '''
    # User3 is not a part of dm1.
    user3 = dms_create['user3']
    dm1 = dms_create['dm1']['dm_id']

    invalid_message = {
        'token': user3['token'],
        'dm_id': dm1,
        'message': 'Hi'
    }

    assert requests.post(config.url + 'message/senddm/v1', json=invalid_message).status_code == ACCESS_ERROR

# --------------------------------------------------------------------------------------- #
# ----------------------------- Testing Message Remove ---------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_message_remove_public(users, channels_create):
    '''
    Tests the intended behavior of message remove for a public channel.
    '''
    # Register User
    auth = users['user1']
    # Create Channel
    channel, _ = channels_create
    # Send messages
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')
    message2 = send_message(auth['token'], channel['channel_id'], 'Test Message 2')
    # Remove message
    requests.delete(config.url + 'message/remove/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    })
    # Get messages   
    all_messages = get_channel_messages(auth['token'], channel['channel_id'], 0)
    assert all_messages['messages'][0]['message_id'] == message2['message_id']
    assert all_messages['messages'][0]['message'] == 'Test Message 2'

def test_message_remove_private(users, channels_create):
    '''
    Tests the intended behavior of message remove for a private channel.
    '''
    # Register User
    auth = users['user1']
    # Create Channel
    _, channel = channels_create
    # Send messages
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')
    message2 = send_message(auth['token'], channel['channel_id'], 'Test Message 2')
    # Remove message
    requests.delete(config.url + 'message/remove/v1', json = {
        'token': auth['token'],
        'message_id': message2['message_id']
    })
    # Get messages   
    all_messages = get_channel_messages(auth['token'], channel['channel_id'], 0)
    assert all_messages['messages'][0]['message_id'] == message1['message_id']
    assert all_messages['messages'][0]['message'] == 'Test Message 1'


def test_message_remove_dm(users, dms_create):
    '''
    Tests the intended behavior of message remove for a dm.
    '''
    # Register User
    auth = users['user1']
    # Create DM
    dm = dms_create['dm1']
    # Send messages
    message1 = requests.post(config.url + 'message/senddm/v1', json = {
        'token': auth['token'],
        'dm_id': dm['dm_id'],
        'message': 'Testing Message 1'
    }).json()
    message2 = requests.post(config.url + 'message/senddm/v1', json = {
        'token': auth['token'],
        'dm_id': dm['dm_id'],
        'message': 'Testing Message 2'
    }).json()  
    # Remove message1
    requests.delete(config.url + 'message/remove/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    })
    # Get messages    
    all_messages = dm_messages_input(auth, dm, 0)['messages'][0]
    assert all_messages['message_id'] == message2['message_id']
    assert all_messages['message'] == 'Testing Message 2'

def test_message_remove_invalid_msg_id(users, dms_create):
    '''
    Tests for InputError when message (based on ID) no longer exists.
    '''
    auth = users['user1']
    # Create DM
    dm = dms_create['dm1']
    # Send messages
    message1 = requests.post(config.url + 'message/senddm/v1', json = {
        'token': auth['token'],
        'dm_id': dm['dm_id'],
        'message': 'Testing Message 1'
    }).json() 
    # Remove message1
    requests.delete(config.url + 'message/remove/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    })
    # Auth tries to remove already deleted message.
    assert requests.delete(config.url + 'message/remove/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    }).status_code == INPUT_ERROR

def test_message_remove_user_not_auth(users, channels_create):
    '''
    Tests for AccessError when message with message_id was NOT sent by the authorised user making this request
    '''
    auth = users['user1']
    user2 = users['user2']
    # Create Channel
    channel, _ = channels_create
    # Auth Sends Msgs
    message1 = send_message(auth['token'], channel['channel_id'], "Can't")['message_id']
    message2 = send_message(auth['token'], channel['channel_id'], 'Touch')['message_id']
    message3 = send_message(auth['token'], channel['channel_id'], 'This')['message_id']
    assert requests.delete(config.url + 'message/remove/v1', json = {
        'token': user2['token'],
        'message_id': message1
    }).status_code == ACCESS_ERROR
    assert requests.delete(config.url + 'message/remove/v1', json = {
        'token': user2['token'],
        'message_id': message2
    }).status_code == ACCESS_ERROR
    assert requests.delete(config.url + 'message/remove/v1', json = {
        'token': user2['token'],
        'message_id': message3
    }).status_code == ACCESS_ERROR

def test_message_remove_user_not_channelOwner(users, channels_create):
    '''
    Tests for AccessError when the authorised user is NOT an owner of this channel (if it was sent to a channel) or the **Dreams**
    '''
    auth = users['user1']
    user2 = users['user2']
    channel, _ = channels_create
    # invite user2 to channel
    requests.post(config.url + 'channel/invite/v2', json = {
        'token': auth['token'],
        'channel_id': channel['channel_id'],
        'u_id': user2['auth_user_id']
    })
    message1 = send_message(user2['token'], channel['channel_id'], "I'm")['message_id']
    message2 = send_message(user2['token'], channel['channel_id'], 'not')['message_id']
    message3 = send_message(user2['token'], channel['channel_id'], 'an Owner')['message_id']
    assert requests.delete(config.url + 'message/remove/v1', json = {
        'token': user2['token'],
        'message_id': message1
    }).status_code == ACCESS_ERROR
    assert requests.delete(config.url + 'message/remove/v1', json = {
        'token': user2['token'],
        'message_id': message2
    }).status_code == ACCESS_ERROR
    assert requests.delete(config.url + 'message/remove/v1', json = {
        'token': user2['token'],
        'message_id': message3
    }).status_code == ACCESS_ERROR
# --------------------------------------------------------------------------------------- #
# ----------------------------- Testing Message Share ----------------------------------- #
# --------------------------------------------------------------------------------------- #
def test_message_share(users, channels_create, dms_create):
    '''
    Tests the intended behavior of message share.
    '''
    user1 = users['user1']
    user2 = users['user2']
    public, private = channels_create
    dm1 = dms_create['dm1']

    # User1 sends a message to the channel
    message_sent = requests.post(config.url + 'message/send/v2', json = {
        'token': user1['token'],
        'channel_id': public['channel_id'],
        'message': 'Testing'
    }).json()['message_id']

    # User1 shares message to priv channel and dm
    message_shared_priv = requests.post(config.url + 'message/share/v1', json = {
        'token': user1['token'],
        'og_message_id': message_sent,
        'message': '123',
        'channel_id': private['channel_id'],
        'dm_id': -1
    }).json()['shared_message_id']

    message_shared_dm = requests.post(config.url + 'message/share/v1', json = {
        'token': user1['token'],
        'og_message_id': message_sent,
        'message': 'abc',
        'channel_id': dm1['dm_id'],
        'dm_id': -1
    }).json()['shared_message_id']

    msg_priv_list = channel_messages_input(user1, private, 0)['messages'][0]
    assert message_shared_priv == msg_priv_list['message_id']
    assert msg_priv_list['message'] == 'Testing, 123'
    assert msg_priv_list['u_id'] == user1['auth_user_id']

    msg_dm_list = dm_messages_input(user2, dm1, 0)['messages'][0]
    assert message_shared_dm == msg_dm_list['message_id']
    assert msg_dm_list['message'] == 'Testing, abc'
    assert msg_dm_list['u_id'] == user1['auth_user_id']

def test_message_share_access_error(users, channels_create, dms_create):
    '''
    Tests for AccessError when the authorised user has not joined the channel or DM they are trying to share the message to. 
    '''
    user1 = users['user1']
    public, private = channels_create
    dm1 = dms_create['dm1']

    new_user = requests.post(config.url + 'auth/register/v2', json = {
        'email': 'haydensmith@gmail.com',
        'password': 'pwrd321',
        'name_first': 'Hayden' ,
        'name_last': 'Smith',
    }).json()

    # User1 sends a message to the channel
    message_sent = requests.post(config.url + 'message/send/v2', json = {
        'token': user1['token'],
        'channel_id': public['channel_id'],
        'message': 'Testing'
    }).json()['message_id']

    # New User tries to share message
    assert requests.post(config.url + 'message/share/v1', json = {
        'token': new_user['token'],
        'og_message_id': message_sent,
        'message': 'abc',
        'channel_id': private,
        'dm_id': -1
    }).status_code == ACCESS_ERROR

    assert requests.post(config.url + 'message/share/v1', json = {
        'token': new_user['token'],
        'og_message_id': message_sent,
        'message': 'abc',
        'channel_id': dm1['dm_id'],
        'dm_id': -1
    }).status_code == ACCESS_ERROR

# --------------------------------------------------------------------------------------- #
# ----------------------------- message_sendlater  -------------------------------------- #
# --------------------------------------------------------------------------------------- #
@pytest.fixture
def users_info(user_register):
    '''Returns the users token'''
    u = user_register
    user1_info = register_user_modified(u['user1'])
    user2_info = register_user_modified(u['user2'])
    user3_info = register_user_modified(u['user3'])
    user4_info = register_user_modified(u['user4'])
    return user1_info, user2_info, user3_info, user4_info

def test_message_sendlater_normal(users_info, timestamps):
    '''
    4 users have registered, user1 created a public channel called "testChannel"
    user1 invited user 2, user3 come joining the channel
    user1 sendlater a message, check user2, user3 have received the message only after 2 seconds
    '''
    #Get token from the users
    user1_info, user2_info, user3_info, _ = users_info

    #user 1 create a public channel, invited user 2 and user 3
    channel_info = create_channel(user1_info['token'], True, 'TestChannel')
    channel_invite(user1_info['token'], channel_info['channel_id'], user2_info['auth_user_id'])
    channel_invite(user1_info['token'], channel_info['channel_id'], user3_info['auth_user_id'])
    valid_timestamp, _ = timestamps

    #user 1 send a message that only triggers after 3 seconds
    message_info = send_messagelater(user1_info['token'], channel_info['channel_id'], "test message", valid_timestamp)
    message_info['message_id']

    # check the user2's channel message immediatelly after send, make sure there's no message
    # assert get_channel_messages(user1_info['token'], channel_info['channel_id'], 0)['messages'] == []
    # assert get_channel_messages(user2_info['token'], channel_info['channel_id'], 0)['messages'] == []
    # assert get_channel_messages(user3_info['token'], channel_info['channel_id'], 0)['messages'] == []
    time.sleep(2)
    # check the message after 3 seconds, make sure there's a message
    assert get_channel_messages(user1_info['token'], channel_info['channel_id'], 0)['messages'][0]['message'] == "test message"
    assert get_channel_messages(user2_info['token'], channel_info['channel_id'], 0)['messages'][0]['message'] == "test message"
    assert get_channel_messages(user3_info['token'], channel_info['channel_id'], 0)['messages'][0]['message'] == "test message"

def test_sendlater_inputError(users_info, timestamps):
    #Get token from the users
    user1_info, _, _, _ = users_info
    channel_info = create_channel(user1_info['token'], True, 'TestChannel')
    valid_timestamp, invalid_timestamp = timestamps
    assert send_messagelater(user1_info['token'], 100000, 'Test Message', valid_timestamp)['code'] == 400 #invalid channel ID
    assert send_messagelater(user1_info['token'], channel_info['channel_id'], 'a'*1001, valid_timestamp)['code'] == 400 #message is more than 1000 chars
    assert send_messagelater(user1_info['token'], channel_info['channel_id'], 'a'*1001, invalid_timestamp)['code'] == 400 #time send is in the past

def test_message_sendlater_accessError(users_info, timestamps):
    #user 1 created a channel, but user 2 tried to send the message
    user1_info, user2_info, _, _ = users_info
    channel_id = create_channel(user1_info['token'], True, 'TestChannel')['channel_id']
    valid_timestamp, _ = timestamps
    assert send_messagelater(user2_info['token'], channel_id, 'Test Message', valid_timestamp)['code'] == 403

# --------------------------------------------------------------------------------------- #
# ----------------------------- message_sendlaterdm  ------------------------------------ #
# --------------------------------------------------------------------------------------- #
def test_message_sendlaterdm_normal(users_info, timestamps):
    '''
    4 users have registered, user1 created a public channel called "testChannel"
    user1 invited user 2, user3 come joining the channel
    user1 sendlater a message, check user2, user3 have received the message only after 2 seconds
    '''
    #Get token from the users
    user1_info, user2_info, user3_info, _ = users_info

    #user 1 create a public channel, invited user 2 and user 3
    print(f"user2_info['auth_user_id'] = {user2_info['auth_user_id']}")
    channel_info = create_dm(user1_info['token'], [user2_info['auth_user_id']])
    print(f"channel_info['dm_id'] = {channel_info['dm_id']}")
    dm_invite(user1_info['token'], channel_info['dm_id'], user3_info['auth_user_id'])
    valid_timestamp, _ = timestamps

    #user 1 send a message that only triggers after 3 seconds
    send_messagelaterdm(user1_info['token'], channel_info['dm_id'], "test message", valid_timestamp)

    #check the user2's channel message immediatelly after send, make sure there's no message
    # assert get_channel_messages(user1_info['token'], channel_info['dm_id'], 0)['messages'] == []
    # assert get_channel_messages(user2_info['token'], channel_info['dm_id'], 0)['messages'] == []
    # assert get_channel_messages(user3_info['token'], channel_info['dm_id'], 0)['messages'] == []
    time.sleep(2)
    #check the message after 3 seconds, make sure there's a message
    assert get_channel_messages(user1_info['token'], channel_info['dm_id'], 0)['messages'][0]['message'] == "test message"
    assert get_channel_messages(user2_info['token'], channel_info['dm_id'], 0)['messages'][0]['message'] == "test message"
    assert get_channel_messages(user3_info['token'], channel_info['dm_id'], 0)['messages'][0]['message'] == "test message"

def test_sendlaterdm_inputError(users_info, timestamps):
    #Get token from the users
    user1_info, user2_info, _, _ = users_info
    channel_info = create_dm(user1_info['token'], [user2_info['auth_user_id']])
    valid_timestamp, invalid_timestamp = timestamps
    assert send_messagelaterdm(user1_info['token'], 100000, 'Test Message', valid_timestamp)['code'] == 400 #invalid channel ID
    assert send_messagelaterdm(user1_info['token'], channel_info['dm_id'], 'a'*1001, valid_timestamp)['code'] == 400 #message is more than 1000 chars
    assert send_messagelaterdm(user1_info['token'], channel_info['dm_id'], 'a'*1001, invalid_timestamp)['code'] == 400 #time send is in the past

def test_message_sendlaterdm_accessError(users_info, timestamps):
    #user 1 created a channel, but user 2 tried to send the message
    user1_info, user2_info, user3_info, _ = users_info
    channel_id = create_dm(user1_info['token'], [user2_info['auth_user_id']])
    valid_timestamp, _ = timestamps
    assert send_messagelaterdm(user3_info['token'], channel_id['dm_id'], 'Test Message', valid_timestamp)['code'] == ACCESS_ERROR


# ------------------------------------------------------------------------------ #
# --------------------------- Message_pin Testing ------------------------------ #
# ------------------------------------------------------------------------------ #

def test_message_pin(users, channels_create):
    auth = users['user1']
    channel, _ = channels_create
    # Send message
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')
    # Pin message
    requests.post(config.url + 'message/pin/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    })
    all_messages = get_channel_messages(auth['token'], channel['channel_id'], 0)

    assert all_messages['messages'][0]['message_id'] == message1['message_id']
    assert all_messages['messages'][0]['is_pinned'] == True

def test_message_pin_dm(users, dms_create):
    auth = users['user1']

    dm = dms_create['dm1']

    message1 = send_message(auth['token'], dm['dm_id'], 'Test Message 1')
    # Pin message
    requests.post(config.url + 'message/pin/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    })
    all_messages = get_channel_messages(auth['token'], dm['dm_id'], 0)

    assert all_messages['messages'][0]['message_id'] == message1['message_id']
    assert all_messages['messages'][0]['is_pinned'] == True

def test_message_pin_inputerror(users, channels_create):
    auth = users['user1']
    channel, _ = channels_create
    # Send message
    send_message(auth['token'], channel['channel_id'], 'Test Message 1')
    # Pin message
    assert requests.post(config.url + 'message/pin/v1', json = {
        'token': auth['token'],
        'message_id': -1
    }).status_code == INPUT_ERROR

def test_message_pin_accesserror(users, channels_create):
    # Register Users
    auth = users['user1']
    user = users['user2']
    # Create Channel
    channel, _ = channels_create
    # Send message
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')
    # Pin message
    assert requests.post(config.url + 'message/pin/v1', json = {
        'token': user['token'],
        'message_id': message1['message_id']
    }).status_code == ACCESS_ERROR

# ------------------------------------------------------------------------------ #
# -------------------------- Message_unpin Tests ------------------------------- #
# ------------------------------------------------------------------------------ #

def test_message_unpin(users, channels_create):
    auth = users['user1']
    channel, _ = channels_create
    # Send message
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')
    # Pin message
    requests.post(config.url + 'message/pin/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    })
    # Unpin message
    requests.post(config.url + 'message/unpin/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    })
    all_messages = get_channel_messages(auth['token'], channel['channel_id'], 0)
    assert all_messages['messages'][0]['message_id'] == message1['message_id']
    assert all_messages['messages'][0]['is_pinned'] == False

def test_message_unpin_dm(users, dms_create):
    auth = users['user1']

    dm = dms_create['dm1']

    message1 = send_message(auth['token'], dm['dm_id'], 'Test Message 1')
    # Pin message
    requests.post(config.url + 'message/pin/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    })
    # Unpin message
    requests.post(config.url + 'message/unpin/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    })
    all_messages = get_channel_messages(auth['token'], dm['dm_id'], 0)

    assert all_messages['messages'][0]['message_id'] == message1['message_id']
    assert all_messages['messages'][0]['is_pinned'] == False

def test_message_unpin_inputerror(users, channels_create):
    auth = users['user1']
    channel, _ = channels_create
    # Send message
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')
    # Pin message
    requests.post(config.url + 'message/pin/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    })
    assert requests.post(config.url + 'message/unpin/v1', json = {
        'token': auth['token'],
        'message_id': -1
    }).status_code == INPUT_ERROR

def test_message_unpin_accesserror(users, channels_create):
    # Register Users
    auth = users['user1']
    user = users['user2']
    # Create Channel
    channel, _ = channels_create
    # Send message
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')
    # Pin message
    requests.post(config.url + 'message/pin/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id']
    })
    # Unpin message
    assert requests.post(config.url + 'message/unpin/v1', json = {
        'token': user['token'],
        'message_id': message1['message_id']
    }).status_code == ACCESS_ERROR

# ------------------------------------------------------------------------------ #
# -------------------------- Message_react Tests ------------------------------- #
# ------------------------------------------------------------------------------ #

def test_message_react(users, channels_create):
    auth = users['user1']
    channel, _ = channels_create
    # Send message
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')

    requests.post(config.url + 'message/react/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id'],
        'react_id': 1
    })
    all_messages = get_channel_messages(auth['token'], channel['channel_id'], 0)
    reacts = all_messages['messages'][0]['reacts']
    assert reacts[0]['is_this_user_reacted'] == True
    assert reacts[0]['u_ids'] == [auth['auth_user_id']]

def test_message_react_dm(users, dms_create):
    auth = users['user1']
    dm = dms_create['dm1']

    message1 = send_message(auth['token'], dm['dm_id'], 'Test Message 1')

    requests.post(config.url + 'message/react/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id'],
        'react_id': 1
    })
    all_messages = get_channel_messages(auth['token'], dm['dm_id'], 0)
    reacts = all_messages['messages'][0]['reacts']
    assert reacts[0]['is_this_user_reacted'] == True
    assert reacts[0]['u_ids'] == [auth['auth_user_id']]

def test_message_react_inputerror(users, channels_create):
    auth = users['user1']
    channel, _ = channels_create

    # Send message
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')

    assert requests.post(config.url + 'message/react/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id'],
        'react_id': -1
    }).status_code == INPUT_ERROR

def test_message_react_accesserror(users, channels_create):
    # Register Users
    auth = users['user1']
    user = users['user2']

    # Create Channel
    channel, _ = channels_create

    # Send message
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')

    assert requests.post(config.url + 'message/react/v1', json = {
        'token': user['token'],
        'message_id': message1['message_id'],
        'react_id': 1
    }).status_code == ACCESS_ERROR

# ------------------------------------------------------------------------------ #
# -------------------------- Message_unreact Tests ----------------------------- #
# ------------------------------------------------------------------------------ #

def test_message_unreact(users, channels_create):
    auth = users['user1']
    channel, _ = channels_create

    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')
    # React
    requests.post(config.url + 'message/react/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id'],
        'react_id': 1
    })
    # Unreact
    requests.post(config.url + 'message/unreact/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id'],
        'react_id': 1
    })
    all_messages = get_channel_messages(auth['token'], channel['channel_id'], 0)
    reacts = all_messages['messages'][0]['reacts']
    assert reacts[0]['is_this_user_reacted'] == False
    assert reacts[0]['u_ids'] == []

def test_message_unreact_dm(users, dms_create):
    auth = users['user1']
    dm = dms_create['dm1']

    message1 = send_message(auth['token'], dm['dm_id'], 'Test Message 1')

    # React
    requests.post(config.url + 'message/react/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id'],
        'react_id': 1
    })
    # Unreact
    requests.post(config.url + 'message/unreact/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id'],
        'react_id': 1
    })

    all_messages = get_channel_messages(auth['token'], dm['dm_id'], 0)
    reacts = all_messages['messages'][0]['reacts']
    assert reacts[0]['is_this_user_reacted'] == False
    assert reacts[0]['u_ids'] == []

def test_message_unreact_inputerror(users, channels_create):
    auth = users['user1']
    channel, _ = channels_create

    # Send message
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')

    requests.post(config.url + 'message/react/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id'],
        'react_id': 1
    })

    assert requests.post(config.url + 'message/unreact/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id'],
        'react_id': -1
    }).status_code == INPUT_ERROR

def test_message_unreact_accesserror(users, channels_create):
    # Register Users
    auth = users['user1']
    user = users['user2']

    # Create Channel
    channel, _ = channels_create

    # Send message
    message1 = send_message(auth['token'], channel['channel_id'], 'Test Message 1')

    requests.post(config.url + 'message/react/v1', json = {
        'token': auth['token'],
        'message_id': message1['message_id'],
        'react_id': 1
    })

    assert requests.post(config.url + 'message/unreact/v1', json = {
        'token': user['token'],
        'message_id': message1['message_id'],
        'react_id': 1
    }).status_code == ACCESS_ERROR
