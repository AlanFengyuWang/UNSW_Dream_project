'''
Authors:    
    Justin Wu, z5316037
    William Zheng, z5313015

Date:       
    25 March 2021
'''

import pytest
import src.auth

from src.auth import auth_register, get_data
from src.channel import channel_invite, channel_messages, channel_join
from src.channels import channels_create
from src.dm import dm_create, dm_messages
from src.message import message_send, message_react, message_edit, message_remove, \
                        message_pin, message_senddm, message_share, message_unpin, \
                        message_unreact, message_sendlater, message_sendlaterdm
from src.helper import search_message_id
from src.other import clear
from src.error import InputError, AccessError
from tests.dm_test import users, dm_ids, spare_user
import threading, time
from datetime import timezone, timedelta, datetime

# --------------------------------------------------------------------------------------- #
# ----------------------------- Fixture Set Up ------------------------------------------ #
# --------------------------------------------------------------------------------------- #

@pytest.fixture
def register_user():
    '''
    Fixture that sets up the details for 2 test users.
    '''
    clear()
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
            'name_first': 'First' ,
            'name_last': 'Last'
        }
    }

@pytest.fixture
def user_token(register_user):
    '''
    Returns the tokens of users from register_user.
    '''
    token1 = auth_register(**register_user['user1'])['token']
    token2 = auth_register(**register_user['user2'])['token']
    return (token1, token2)

@pytest.fixture
def channel_id(user_token):
    '''
    Returns the channel id of a public and private channel created by registered user1.
    '''
    token, _ = user_token
    pub_id = channels_create(token, 'public channel', True)['channel_id']
    priv_id = channels_create(token, 'private channel', False)['channel_id'] 
    return (pub_id, priv_id)

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for message_send ---------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_single_message_send(user_token, channel_id):
    '''
    Test for correct message_id output for a message sent by user to channel.
    '''
    token, _ = user_token
    channel1, _ = channel_id
    message_id1 = message_send(token, channel1, 'Hello')['message_id']
    assert message_id1 == 1

def test_multiple_messages(user_token, channel_id):
    '''
    Test for correct message_ids for multiple messages made by user in channel.
    '''
    token, _= user_token
    channel1, _ = channel_id
    message_id1 = message_send(token, channel1, 'Hello World')['message_id']
    message_id2 = message_send(token, channel1, 'Test123')['message_id']
    message_id3 = message_send(token, channel1, 'Marc Chee')['message_id']
    assert message_id1 == 1 
    assert message_id2 == 2
    assert message_id3 == 3

def test_multiple_messages_users(user_token, channel_id):
    '''
    Test for correct message_ids for multiple messages made by users in channel.
    '''
    token1, token2 = user_token
    channel1, _ = channel_id
    # Invite user2 to user1's channel.
    channel_invite(token1, channel1, 2)
    message_id1 = message_send(token1, channel1, 'WYD')['message_id']
    message_id2 = message_send(token2, channel1, 'Sleeping')['message_id']
    message_id3 = message_send(token1, channel1, '...')['message_id'] 
    assert message_id1 == 1 
    assert message_id2 == 2
    assert message_id3 == 3

def test_multiple_messages_users_channels(user_token, channel_id):
    '''
    Test for correct message_ids for multiple messages made by users in different channels.
    '''
    token1, token2 = user_token
    channel1, channel2 = channel_id
    # Invite user2 to both channels made by user1.
    channel_invite(token1, channel1, 2)
    channel_invite(token1, channel2, 2)
    message_id1 = message_send(token1, channel1, 'Hey')['message_id']
    message_id2 = message_send(token2, channel1, 'Go to the other channel')['message_id']
    message_id3 = message_send(token1, channel1, 'okayy')['message_id']
    message_id4 = message_send(token1, channel2, "How's this?")['message_id']
    message_id5 = message_send(token2, channel2, 'NOT BAD')['message_id']
    assert message_id1 == 1 
    assert message_id2 == 2
    assert message_id3 == 3
    assert message_id4 == 4
    assert message_id5 == 5

def test_message_send_too_long(user_token, channel_id):
    '''
    Test for InputError when messages are more than 1000 chars.
    '''
    token, _ = user_token
    channel1, channel2 = channel_id
    with pytest.raises(InputError):
        message_send(token, channel1, 'test' + 'x' * 1000)
        message_send(token, channel2, '123'+ 'x' * 1000)

def test_message_send_invalid_channelID(user_token):
    '''
    Test for InputError when channel_id is invalid
    '''
    token, _ = user_token
    with pytest.raises(InputError):
        message_send(token, 3, 'test')
        message_send(token, 4, '123')

def test_message_send_user_not_member(user_token, channel_id, register_user):
    '''
    Test AccessError when the authorised user has not joined the channel they are trying to post to.
    '''
    # Creating a random new user who has not joined any channels
    new_user_token = auth_register('MarcCheemail@email.com', '122323d', 'Marc','Chee')['token']
    channel1, channel2 = channel_id
    with pytest.raises(AccessError):
        message_send(new_user_token, channel1, 'Let me in')
        message_send(new_user_token, channel2, 'OI')

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for message_edit ---------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_message_edit_single_user(user_token, channel_id):
    '''
    Test to see if message edits made by channel owner appear.
    '''
    token1, _ = user_token
    channel1, _ = channel_id

    message_id1 = message_send(token1, channel1, 'Hey')['message_id']
    message_edit(token1, message_id1, 'This message should replace Hey')

    message_id2 = message_send(token1, channel1, 'Test')['message_id']
    message_edit(token1, message_id2, 'Test One')

    # Check whether message has been updated.
    messages = channel_messages(token1, channel1, 0)['messages']
    for message in messages:
        if message['message_id'] == message_id1:
            assert message['message'] == 'This message should replace Hey'
        if message['message_id'] == message_id2:
            assert message['message'] == 'Test One'

def test_message_edit_multiple_users(user_token, channel_id):
    '''
    Test to see if message edits made by channels owner appear.
    '''
    token1, token2 = user_token
    channel1, _ = channel_id
    channel2 = channels_create(token2, "user2's channel", True)['channel_id']

    message_id1 = message_send(token1, channel1, 'your Marc Chee?')['message_id']
    message_id2 = message_send(token2, channel2, "hello word")['message_id']
    message_edit(token1, message_id1, "You're Marc Chee?")
    message_edit(token2, message_id2, 'Hello World!!')

    messages = channel_messages(token1, channel1, 0)['messages']
    for message in messages:
        if message['message_id'] == message_id1:
            assert message['message'] == "You're Marc Chee?"

    messages = channel_messages(token2, channel2, 0)['messages']
    for message in messages:
        if message['message_id'] == message_id2:
            assert message['message'] == 'Hello World!!'


def test_message_edit_delete(user_token, channel_id):
    '''
    Test to see if message is deleted if message_edit is given an empty string by channel owner.
    '''
    token1, _ = user_token
    channel1, _ = channel_id

    message_id1 = message_send(token1, channel1, 'To be deleted')['message_id']
    message_edit(token1, message_id1, '')

    # If new message is an empty string, old message should be deleted
    messages = channel_messages(token1, channel1, 0)['messages']
    for message in messages:
        if message['message_id'] == message_id1:
            assert message['message'] == ''

def test_message_edit_input_except(user_token, channel_id):
    '''
    Tests for InputError when:
        - Length of message is over 1000 characters
        - Message_id refers to a deleted message
    '''
    user1, _ = user_token
    new_user = auth_register('comp1@email.com', 'password', 'comp', '1531')
    u_id2 = new_user['auth_user_id']
    channel1, _ = channel_id
    
    channel_invite(user1, channel1, u_id2)

    message_id1 = message_send(user1, channel1, 'test')['message_id']
    message_id2 = message_send(user1, channel1, 'a')['message_id']
    message_id3 = message_send(user1, channel1, 'to be removed')['message_id']
    message_remove(user1, message_id3)

    with pytest.raises(InputError):
        message_edit(user1, message_id1, 'test' * 1000)
        message_edit(user1, message_id2, 'a' * 1001) # Message has more than 1000 chars.
        message_edit(user1, message_id3, 'bring back my message') # Inputted message_id has been removed
        message_edit(user1, 99, 'bring back my message') #Invalid message_id
        
    # TO DO:
    # Auth user is not dreams

def test_message_edit_access_except(user_token, channel_id):
    '''
    Tests for AccessError when:
        - Message with message_id was sent by an unauthorised user making this request
        - The authorised user is not a channel owner (if it was sent to a channel) or not the **Dreams*
    '''
    user1, _ = user_token
    new_user = auth_register('comp1@email.com', 'password', 'comp', '1531')
    user2 = new_user['token']
    u_id2 = new_user['auth_user_id']
    channel1, _ = channel_id
    
    channel_invite(user1, channel1, u_id2)

    message_id1 = message_send(user2, channel1, 'user2 msg')['message_id']
    message_id2 = message_send(user2, channel1, 'not the owner of this channel')['message_id']

    with pytest.raises(AccessError):
        message_edit(user1, message_id1, '123') #user1 is trying to edit user2's message
        message_edit(user1, message_id1, 'let me edit')
        message_edit(user2, message_id2, 'Hi') #user2 is trying to edit his message, but they're not the channel owner

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for message_senddm ---------------------------------#
# --------------------------------------------------------------------------------------- #

def test_single_message_senddm(users, dm_ids):
    '''
    Test for correct message_id output for a message sent by user to a dm.
    '''
    owner, _, _, _ = users
    dm1, _ = dm_ids

    message_id = message_senddm(owner, dm1['dm_id'], 'COMP1531')['message_id']
    assert message_id == 1

def test_multiple_messages_senddm(users, dm_ids):
    '''
    Test for correct message_ids for multiple messages made by users in dm.
    '''
    owner, user2, _, _ = users
    dm1, _ = dm_ids

    message_id1 = message_senddm(owner, dm1['dm_id'], 'test')['message_id']
    message_id2 = message_senddm(user2, dm1['dm_id'], '123')['message_id']
    message_id3 = message_senddm(owner, dm1['dm_id'], 'hi')['message_id']
    assert message_id1 == 1
    assert message_id2 == 2
    assert message_id3 == 3


def test_message_senddm_is_unique(users, channel_id, dm_ids):
    '''
    Test for message_id not shared with another message_id, 
    even if that other message is in a different channel or DM.
    '''
    owner, _, _, _ = users
    dm1, _ = dm_ids
    channel1 = channels_create(owner, "Owner's Pub channel", True)['channel_id']
    channel2 = channels_create(owner, "Owner's Priv channel", False)['channel_id']

    # Owner sends message to dm
    message_id1 = message_senddm(owner, dm1['dm_id'], 'COMP1531')['message_id']
    # Owner sends same message to their channel
    message_id2 = message_send(owner, channel1, 'COMP1531')['message_id']
    message_id3 = message_send(owner, channel2, 'COMP1531')['message_id']
    assert message_id1 == 1
    assert message_id2 == 2
    assert message_id3 == 3

def test_message_sendm_too_long(users, dm_ids):
    '''
    Test for InputError when messages are more than 1000 chars.
    '''
    owner, user2, _, _ = users
    dm1, _ = dm_ids
    with pytest.raises(InputError):
        message_senddm(owner, dm1['dm_id'], 'x'*1001)
        message_senddm(user2, dm1['dm_id'], '123'*1000)


def test_message_senddm_user_not_member(users, dm_ids):
    '''
    Test AccessError when the authorised user has not joined the 
    dm hey are trying to post to.
    '''
    # Creating a random new user who has not joined any dm.
    dm1, dm2 = dm_ids
    new_user = auth_register('MarcCheemail@email.com', '122323d', 'Marc','Chee')['token']
    with pytest.raises(AccessError):
        message_senddm(new_user, dm1['dm_id'], 'hello world')
        message_senddm(new_user, dm2['dm_id'], 'COMP1531')

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for message_remove -------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_message_remove_public():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')['token']
    
    pub_channel = channels_create(auth, 'public channel', True)['channel_id']
    
    message = message_send(auth, pub_channel, "Test message")
    message2 = message_send(auth, pub_channel, "Test message 1")

    message_remove(auth, message2['message_id'])

    msg_list = channel_messages(auth, pub_channel, 0)
    assert msg_list['messages'][0]['message_id'] == message['message_id']

def test_message_remove_private():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')['token']
    
    priv_channel = channels_create(auth, 'private channel', False)['channel_id']
    
    message = message_send(auth, priv_channel, "Test message")
    message2 = message_send(auth, priv_channel, "Test message 1")

    message_remove(auth, message2['message_id'])

    msg_list = channel_messages(auth, priv_channel, 0)
    assert msg_list['messages'][0]['message_id'] == message['message_id']

def test_message_remove_dm():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')['token']
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')

    dm = dm_create(auth, [user['auth_user_id']])

    message = message_send(auth, dm['dm_id'], "Test message")
    message2 = message_send(auth, dm['dm_id'], "Test message 1")

    message_remove(auth, message2['message_id'])

    msg_list = channel_messages(auth, dm['dm_id'], 0)
    assert msg_list['messages'][0]['message_id'] == message['message_id']

def test_message_remove_invalid_id():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')['token']

    pub_channel = channels_create(auth, 'public channel', True)['channel_id']

    message = message_send(auth, pub_channel, "Test message")

    with pytest.raises(InputError):
        message_remove(auth, message['message_id'] + 1)

def test_message_remove_not_sender():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')['token']
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')
    
    pub_channel = channels_create(auth, 'public channel', True)['channel_id']

    message = message_send(auth, pub_channel, "Test message")
    
    with pytest.raises(AccessError):
        message_remove(user['token'], message['message_id'])

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for message_share ----------------------------------#
# --------------------------------------------------------------------------------------- #
def test_message_share_valid(users, dm_ids):
    '''
    Tests for the intended behaviour of message share.
    '''
    token1, token2, _, u_id2 = users
    pub_channel = channels_create(token1, 'public channel', True)['channel_id']
    priv_channel = channels_create(token1, 'private channel', False)['channel_id']
    dm1, _ = dm_ids
    dm1_id = dm1['dm_id']

    # User1 and User2 are in pub_channel
    channel_invite(token1, pub_channel, u_id2)

    # User1 sends a message to pub_channel
    og_msg_id1 = message_send(token1, pub_channel, 'Original Message')['message_id']

    # User1 shares the og_msg to priv_channel & dm
    shared_channel_msg_id1 = message_share(token1, og_msg_id1, 'Hey', priv_channel, -1)['shared_message_id']
    shared_channel_msg_id2 = message_share(token1, og_msg_id1, 'Hi', -1, dm1_id)['shared_message_id']

    #User2 sends a dm message to dm
    og_msg_id2 = message_senddm(token2, dm1_id, 'Og Message')['message_id']
    # User2 shares message to pub channel
    shared_dm_msg_id3 = message_share(token2, og_msg_id2, 'COMP1531', pub_channel, -1)['shared_message_id']

    msg_list1 = channel_messages(token1, priv_channel, 0)
    msg_list2 = channel_messages(token1, pub_channel, 0)
    msg_list3 = channel_messages(token2, dm1_id, 0)

    assert shared_channel_msg_id1 == 2
    assert msg_list1['messages'][0]['message_id'] == shared_channel_msg_id1
    assert msg_list1['messages'][0]['message'] == 'Original Message, Hey'

    assert shared_channel_msg_id2 == 3
    assert msg_list2['messages'][0]['message_id'] == shared_channel_msg_id2
    assert msg_list2['messages'][0]['message'] == 'Original Message, Hi, COMP1531'

    assert shared_dm_msg_id3 == 3
    assert msg_list3['messages'][1]['message_id'] == shared_dm_msg_id3
    assert msg_list3['messages'][1]['message'] == 'Original Message, Hi'
    
def test_message_share_channel_access_error(users):
    '''
    Tests for AccessError when the authorised user has not joined the channel.
    '''
    token1, _, _, _ = users
    new_user = auth_register('email23@email.com', 'password', 'firstname', 'lastname')['token']
    pub_channel = channels_create(token1, 'public channel', True)['channel_id']
    priv_channel = channels_create(token1, 'private channel', False)['channel_id']

    # User1 sends msg to pub, priv & dm
    og_msg_id1 = message_send(token1, pub_channel, 'Test1')['message_id']
    og_msg_id2 = message_send(token1, priv_channel, 'Test2')['message_id']

    with pytest.raises(AccessError):
        message_share(new_user, og_msg_id1, 'x', pub_channel, -1)
        message_share(new_user, og_msg_id2, 'x', priv_channel, -1)

def test_message_share_dm_access_error(users, dm_ids):
    '''
    Tests for AccessError when the authorised user has not joined the DM they are trying to share the message to.
    '''
    token1, _, _, _ = users
    new_user = auth_register('email23@email.com', 'password', 'firstname', 'lastname')
    pub_channel = channels_create(token1, 'public channel', True)['channel_id']
    dm1, _ = dm_ids
    dm1_id = dm1['dm_id']

    # User1 and new user are in pub_channel
    channel_invite(token1, pub_channel, new_user['auth_user_id'])

    # User1 sends msg to pub
    og_msg_id = message_send(token1, pub_channel, '123')['message_id']

    # New user wants to share msg from pub to dm1
    with pytest.raises(AccessError):
        message_share(new_user['token'], og_msg_id, 'x', -1, dm1_id)


# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for message_sendlater ----------------------------- #
# --------------------------------------------------------------------------------------- #

@pytest.fixture
def timestamps():
    valid_sending_time = datetime.now() + timedelta(seconds = 1.5)
    valid_timestamp = valid_sending_time.timestamp()
    invalid_sending_time = datetime.now() - timedelta(seconds = 1.5)
    invalid_timestamp = invalid_sending_time.timestamp()
    return (valid_timestamp, invalid_timestamp)

def test_message_sendlater_normal(user_token, channel_id, timestamps):
    #Get the token
    token1, _ = user_token
    #get channel_id
    pub_id, _ = channel_id    #Here used token 1 to create a public channel
    #user 1 send a message that only triggers after 3 seconds
    valid_timestamp, _ = timestamps
    message_sendlater(token1, pub_id, 'Test Message', valid_timestamp)
    #check the message immediatelly after send, make sure there's no message
    # message = channel_messages(token1, pub_id, 0)['messages']
    # assert not message
    #check the message after 3 seconds, make sure there's a message
    time.sleep(2)
    message = channel_messages(token1, pub_id, 0)['messages'][0]['message']
    assert message == 'Test Message'

def test_message_sendlater_inputError(user_token, channel_id, timestamps):
    token1, _ = user_token
    pub_id, _ = channel_id 
    valid_timestamp, invalid_timestamp = timestamps
    with pytest.raises(InputError):
        message_sendlater(token1, 1000, 'Test Message', valid_timestamp)   #invalid channel ID
    with pytest.raises(InputError):
        message_sendlater(token1, pub_id, 'a'*1001, valid_timestamp) #message is more than 1000 chars
    with pytest.raises(InputError):
        message_sendlater(token1, pub_id, 'a'*1001, invalid_timestamp) #time send is in the past

def test_message_sendlater_accessError(user_token, channel_id, timestamps):
    #user 1 created a channel, but user 2 tried to send the message
    token1, token2 = user_token
    channel_id = channels_create(token1, 'public channel', True)['channel_id']
    valid_timestamp, _ = timestamps
    with pytest.raises(AccessError):
        message_sendlater(token2, channel_id, 'Test Message', valid_timestamp)

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for message_dm_sendlater -------------------------- #
# --------------------------------------------------------------------------------------- #
def test_message_dm_sendlater_normal(user_token, dm_ids, timestamps):
    valid_timestamp, _ = timestamps
    #Get the token
    token1, _ = user_token
    #get dm_id
    dm1, _ = dm_ids    #Here used token 1 to create a dm
    #user 1 send a message that only triggers after 3 seconds
    message_sendlaterdm(token1, dm1['dm_id'], 'Test Message', valid_timestamp)
    #check the message immediatelly after send, make sure there's no message
    # message = dm_messages(token1, dm1['dm_id'], 0)['messages']
    # assert not message
    #check the message after 3 seconds, make sure there's a message
    time.sleep(2)
    message = dm_messages(token1, dm1['dm_id'], 0)['messages'][0]['message']
    assert message == 'Test Message'

def test_message_dm_sendlater_inputError(user_token, dm_ids, timestamps):
    token1, _ = user_token
    dm1, _ = dm_ids 
    valid_timestamp, invalid_timestamp = timestamps
    with pytest.raises(InputError):
        message_sendlaterdm(token1, 1000, 'Test Message', valid_timestamp)   #invalid channel ID
    with pytest.raises(InputError):
        message_sendlaterdm(token1, dm1['dm_id'], 'a'*1001, valid_timestamp) #message is more than 1000 chars
    with pytest.raises(InputError):
        print("Test subject1: ")
        message_sendlaterdm(token1, dm1['dm_id'], 'a'*1001, invalid_timestamp) #time send is in the past

def test_message_dm_sendlater_accessError(users, spare_user, channel_id, timestamps):
    #user 1 created a channel, but user 2 tried to send the message
    token1, _, _, u_id2 = users
    token3, _ = spare_user
    dm_id = dm_create(token1, [u_id2])['dm_id']
    valid_timestamp, _ = timestamps
    with pytest.raises(AccessError):
        print("test subject2:")
        message_sendlaterdm(token3, dm_id, 'Test Message', valid_timestamp)


# ------------------------------------------------------------------------------ #
# --------------------------- Message_pin Tests -------------------------------- #
# ------------------------------------------------------------------------------ #

def test_message_pin_invalid_message():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    with pytest.raises(InputError):
        message_pin(auth['token'], message['message_id'] + 1)


def test_message_pin_already_pinned():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    message_pin(auth['token'], message['message_id'])

    with pytest.raises(InputError):
        message_pin(auth['token'], message['message_id'])


def test_message_pin_not_channel_member():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    with pytest.raises(AccessError):
        message_pin(user['token'], message['message_id'])


def test_message_pin_permission():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']
    
    channel_join(user['token'], pub_channel)

    message = message_send(auth['token'], pub_channel, "Test message")

    with pytest.raises(AccessError):
        message_pin(user['token'], message['message_id'])

# ------------------------------------------------------------------------------ #
# -------------------------- Message_unpin Tests ------------------------------- #
# ------------------------------------------------------------------------------ #

def test_message_unpin_invalid_message():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    with pytest.raises(InputError):
        message_unpin(auth['token'], message['message_id'] + 1)


def test_message_unpin_already_unpinned():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    with pytest.raises(InputError):
        message_unpin(auth['token'], message['message_id'])


def test_message_unpin_not_channel_member():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    message_pin(auth['token'], message['message_id'])

    with pytest.raises(AccessError):
        message_unpin(user['token'], message['message_id'])


def test_message_unpin_permission():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']
    
    channel_join(user['token'], pub_channel)

    message = message_send(auth['token'], pub_channel, "Test message")

    message_pin(auth['token'], message['message_id'])

    with pytest.raises(AccessError):
        message_unpin(user['token'], message['message_id'])


# ------------------------------------------------------------------------------ #
# -------------------------- Message_react Tests ------------------------------- #
# ------------------------------------------------------------------------------ #

def test_message_react_invalid_message():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message_send(auth['token'], pub_channel, "Test message")

    with pytest.raises(InputError):
        message_react(auth['token'], -1, 1)


def test_message_react_invalid_react():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    with pytest.raises(InputError):
        message_react(auth['token'], message['message_id'], -1)


def test_message_react_already_reacted():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    message_react(auth['token'], message['message_id'], 1)

    with pytest.raises(InputError):
        message_react(auth['token'], message['message_id'], 1)
    

def test_message_react_not_member():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    with pytest.raises(AccessError):
        message_react(user['token'], message['message_id'], 1)


# ------------------------------------------------------------------------------ #
# -------------------------- Message_unreact Tests ----------------------------- #
# ------------------------------------------------------------------------------ #

def test_message_unreact_invalid_message():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    message_react(auth['token'], message['message_id'], 1)

    with pytest.raises(InputError):
        message_unreact(auth['token'], -1, 1)


def test_message_unreact_invalid_react():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    message_react(auth['token'], message['message_id'], 1)

    with pytest.raises(InputError):
        message_unreact(auth['token'], message['message_id'], -1)


def test_message_unreact_already_unreacted():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    message_react(auth['token'], message['message_id'], 1)

    message_unreact(auth['token'], message['message_id'], 1)

    with pytest.raises(InputError):
        message_unreact(auth['token'], message['message_id'], 1)
    

def test_message_unreact_not_member():
    clear()
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')

    pub_channel = channels_create(auth['token'], 'public channel', True)['channel_id']

    message = message_send(auth['token'], pub_channel, "Test message")

    message_react(auth['token'], message['message_id'], 1)

    with pytest.raises(AccessError):
        message_unreact(user['token'], message['message_id'], 1)

# ------------------------------------------------------------------------------ #
# -------------------------- Message Helpers Tests ----------------------------- #
# ------------------------------------------------------------------------------ #
def test_search_message_id_invalid():
    with pytest.raises(InputError):
        search_message_id(99)
        search_message_id(-99)
