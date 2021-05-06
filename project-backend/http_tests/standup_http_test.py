'''
Authors: Justin Wu, z5316037

Date: 12 April 2021
'''

import pytest
import requests
import json
import time

from src import config
from src.error import InputError, AccessError
from http_tests.helpers_http_test import users, spare_users, channels_create, \
    standup_create, standup_active, standup_send, get_channel_messages, get_user_profile

ACCESS_ERROR = 403
INPUT_ERROR = 400

STANDUP_START = 'standup/start/v1'
STANDUP_ACTIVE = 'standup/active/v1'
STANDUP_SEND = 'standup/send/v1'

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for StandUp-Send ---------------------------------- #
# --------------------------------------------------------------------------------------- #
def test_standup_single_send(users, channels_create):
    '''
    Tests for the successful implementation of standup_send where a sent message
    gets buffered in a standup queue.
    '''
    user1, _ = users
    token1 = user1['token']
    u_id1 = user1['auth_user_id']
    pub_channel, _ = channels_create
    time_length = 1

    # User1 starts a standup in pub_channel
    standup_create(token1, pub_channel, time_length)

    # User1 sends message to standup.
    user1_msg = 'User1 Test'
    standup_send(token1, pub_channel, user1_msg)

    # Wait until standup period is finished.
    time.sleep(time_length + 3)

    # Format expected message.
    username1 = get_user_profile(token1, u_id1)['handle_str']
    expected_msg = f"{username1}: {user1_msg}"

    resp = get_channel_messages(token1, pub_channel, 0)
    assert resp['messages'][0]['message'] == expected_msg

def test_standup_multiple_send(users, channels_create):
    '''
    Tests for the successful implementation of standup_send where multiple sent
    messages get buffered in a standup queue.
    '''
    user1, user2 = users
    token1 = user1['token']
    token2 = user2['token']
    u_id1 = user1['auth_user_id']
    u_id2 = user2['auth_user_id']
    _, priv_channel = channels_create
    time_length = 3

    # User1 starts a standup in priv_channel
    standup_create(token1, priv_channel, time_length)

    # User1 & User 2 send messages to standup.
    user1_msg1 = 'Marc'
    standup_send(token1, priv_channel, user1_msg1)
    user1_msg2 = 'Chee'
    standup_send(token1, priv_channel, user1_msg2)
    user2_msg1 = '???'
    standup_send(token2, priv_channel, user2_msg1)
    user1_msg3 = 'is my dad'
    standup_send(token1, priv_channel, user1_msg3)
    user2_msg2 = 'wow'
    standup_send(token2, priv_channel, user2_msg2)

    # Wait until standup period is over.
    time.sleep(3)

    # Format expected messages.
    username1 = get_user_profile(token1, u_id1)['handle_str']
    username2 = get_user_profile(token2, u_id2)['handle_str']
    nl = '\n'
    expected_msg = f"{username1}: {user1_msg1}{nl}" + \
        f"{username1}: {user1_msg2}{nl}" + \
        f"{username2}: {user2_msg1}{nl}" + \
        f"{username1}: {user1_msg3}{nl}" + \
        f"{username2}: {user2_msg2}"

    # Check expected message against output.
    resp = get_channel_messages(token1, priv_channel, 0)
    assert resp['messages'][0]['message'] == expected_msg

def test_standup_send_invalid_channelID(users, channels_create):
    '''
    Tests for InputError when channel ID is not a valid channel.
    '''
    user1, user2 = users
    token1 = user1['token']
    token2 = user2['token']
    _, priv_channel = channels_create
    time_length = 3

    # User1 starts a standup in priv_channel
    standup_create(token1, priv_channel, time_length)

    assert requests.post(config.url + 'standup/send/v1', json = {
        'token': token1,
        'channel_id': 99,
        'message': 'Test1'
    }).status_code == INPUT_ERROR

    assert requests.post(config.url + 'standup/send/v1', json = {
        'token': token2,
        'channel_id': -99,
        'message': 'Test1'
    }).status_code == INPUT_ERROR

def test_standup_send_message_too_long(users, channels_create):
    '''
    Tests for InputError when message is more than 
    1000 characters (not including the username and colon).
    '''
    user1, _ = users
    token1 = user1['token']
    pub_channel, _ = channels_create
    time_length = 3

    standup_create(token1, pub_channel, time_length)

    assert requests.post(config.url + 'standup/send/v1', json = {
        'token': token1,
        'channel_id': pub_channel,
        'message': 'a'*1001
    }).status_code == INPUT_ERROR

    assert requests.post(config.url + 'standup/send/v1', json = {
        'token': token1,
        'channel_id': pub_channel,
        'message': '123'*1000
    }).status_code == INPUT_ERROR

def test_standup_send_standup_not_active(users, channels_create):
    '''
    Tests for InputError when an active standup is not 
    currently running in this channel.
    '''
    user1, user2 = users
    token1 = user1['token']
    token2 = user2['token']
    _, priv_channel = channels_create
    time_length = 3

    # User1 starts a standup in priv_channel
    standup_create(token1, priv_channel, time_length)

    # Let standup finish so that it's inactive
    time.sleep(time_length)

    assert requests.post(config.url + 'standup/send/v1', json = {
        'token': token1,
        'channel_id': priv_channel,
        'message': 'xyz'
    }).status_code == INPUT_ERROR

    assert requests.post(config.url + 'standup/send/v1', json = {
        'token': token2,
        'channel_id': priv_channel,
        'message': '123'
    }).status_code == INPUT_ERROR

def test_standup_send_auth_not_member(users, channels_create, spare_users):
    '''
    Tests for AccessError when the authorised user is not 
    a member of the channel that the message is within.
    '''
    user1, user2 = users
    user3, user4 = spare_users
    token1 = user1['token']
    token2 = user2['token']
    token3 = user3['token']
    token4 = user4['token']
    pub_channel, _ = channels_create
    time_length = 3

    # User1 starts a standup in pub_channel
    standup_create(token1, pub_channel, time_length)

    assert requests.post(config.url + 'standup/send/v1', json = {
        'token': token2,
        'channel_id': pub_channel,
        'message': 'COMP1531'
    }).status_code == ACCESS_ERROR

    assert requests.post(config.url + 'standup/send/v1', json = {
        'token': token3,
        'channel_id': pub_channel,
        'message': 'COMP1532'
    }).status_code == ACCESS_ERROR

    assert requests.post(config.url + 'standup/send/v1', json = {
        'token': token4,
        'channel_id': pub_channel,
        'message': 'COMP1533'
    }).status_code == ACCESS_ERROR

# --------------------------------------------------------------------------------------- #
# ----------------------------- StandUp Start ------------------------------------------- #
# --------------------------------------------------------------------------------------- #
def test_standup_start_valid(users, channels_create):
    '''
    Tests for a working standup in a channel.
    '''
    user1, user2 = users
    token1 = user1['token']
    token2 = user2['token']
    pub_channel, priv_channel = channels_create

    end_time1 = standup_create(token1, pub_channel, 3)
    time_now1 =  int(time.time())

    assert end_time1 == time_now1 + 3

    end_time2 = standup_create(token2, priv_channel, 3)
    time_now2 =  int(time.time())
    
    assert end_time2 == time_now2 + 3

def test_standup_back_to_back(users, channels_create):
    '''
    Tests if a standup is created immediately after another standup has finished
    in the same channel.
    '''
    user1, _= users
    token1 = user1['token']
    pub_channel, _ = channels_create

    end_time1 = standup_create(token1, pub_channel, 1)
    time_now1 =  int(time.time())
    assert end_time1 == time_now1 + 1

    # Wait 1 second before created second standup
    time.sleep(1)

    end_time2 = standup_create(token1, pub_channel, 2)
    time_now2 =  int(time.time())
    assert end_time2 == time_now2 + 2

def test_standup_start_invalid_channelID(users, channels_create):
    '''
    Tests for InputError when Channel ID is not a valid channel.
    '''
    user1, user2 = users
    token1 = user1['token']
    token2 = user2['token']
    time_length = 3

    assert requests.post(config.url + 'standup/start/v1', json = {
        'token': token1,
        'channel_id': 99,
        'length': time_length
    }).status_code == INPUT_ERROR

    assert requests.post(config.url + 'standup/start/v1', json = {
        'token': token2,
        'channel_id': -99,
        'length': time_length
    }).status_code == INPUT_ERROR

def test_standup_already_active(users, channels_create):
    '''
    Tests for InputError when an active standup is currently running in this channel.
    '''
    user1, user2 = users
    token1 = user1['token']
    token2 = user2['token']
    _, priv_channel = channels_create
    time_length = 3

    # User1 starts a standup in priv_channel
    standup_create(token1, priv_channel, time_length)

    # During this time, users can't create another standup
    assert requests.post(config.url + 'standup/start/v1', json = {
        'token': token1,
        'channel_id': priv_channel,
        'length': time_length
    }).status_code == INPUT_ERROR

    assert requests.post(config.url + 'standup/start/v1', json = {
        'token': token2,
        'channel_id': priv_channel,
        'length': time_length
    }).status_code == INPUT_ERROR

def test_standup_auth_not_member(spare_users, channels_create):
    '''
    Tests for AccessError when authorised user is not in the channel.
    '''
    user3, user4 = spare_users
    token3 = user3['token']
    token4 = user4['token']
    pub_channel, priv_channel = channels_create
    time_length = 3

    assert requests.post(config.url + 'standup/start/v1', json = {
        'token': token3,
        'channel_id': pub_channel,
        'length': time_length
    }).status_code == ACCESS_ERROR

    assert requests.post(config.url + 'standup/start/v1', json = {
        'token': token4,
        'channel_id': pub_channel,
        'length': time_length
    }).status_code == ACCESS_ERROR

    assert requests.post(config.url + 'standup/start/v1', json = {
        'token': token3,
        'channel_id': priv_channel,
        'length': time_length
    }).status_code == ACCESS_ERROR

    assert requests.post(config.url + 'standup/start/v1', json = {
        'token': token4,
        'channel_id': priv_channel,
        'length': time_length
    }).status_code == ACCESS_ERROR

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for StandUp-Active -------------------------------- #
# --------------------------------------------------------------------------------------- #
def test_standup_is_active(users, channels_create):
    '''
    Tests where a standup is active or not. If it is active, test for the correct time
    that the standup finishes. Otherwise, return None.
    '''
    user1, user2 = users
    token1 = user1['token']
    token2 = user2['token']
    pub_channel, priv_channel = channels_create
    time_length = 3

    # Start a standup for pub_channel.
    standup_create(token1, pub_channel, time_length)
    assert standup_active(token1, pub_channel)['is_active'] == True
    assert standup_active(token1, pub_channel)['time_finish'] == int(time.time()) + time_length

    # Checking status of standup for priv channel which should be False.
    standup_active(token1, priv_channel)
    assert standup_active(token1, priv_channel)['is_active'] == False
    assert standup_active(token1, priv_channel)['time_finish'] == None

    # Now starting standup for priv_channel.
    standup_create(token2, priv_channel, time_length)
    assert standup_active(token2, priv_channel)['is_active'] == True
    assert standup_active(token2, priv_channel)['time_finish'] == int(time.time()) + time_length

def test_standup_not_active(users, channels_create):
    '''
    Tests for correct output for non active standups
    '''
    user1, user2 = users
    token1 = user1['token']
    token2 = user2['token']
    pub_channel, priv_channel = channels_create
    
    assert standup_active(token1, pub_channel)['is_active'] == False
    assert standup_active(token1, pub_channel)['time_finish'] == None

    assert standup_active(token2, priv_channel)['is_active'] == False
    assert standup_active(token2, priv_channel)['time_finish'] == None

def test_standup_invalid_channelID(users):
    '''
    Tests InputError when channel ID is not a valid channel.
    '''
    user1, user2 = users
    token1 = user1['token']
    token2 = user2['token']

    assert requests.get(config.url + 'standup/active/v1', params = {
        'token': token1,
        'channel_id': 100
    }).status_code == INPUT_ERROR

    assert requests.get(config.url + 'standup/active/v1', params = {
        'token': token2,
        'channel_id': -100
    }).status_code == INPUT_ERROR

def test_standup_active_different_intervals(users, channels_create):
    '''
    Tests for the status of StandUps in different time intervals.
    '''
    user1, user2 = users
    token1 = user1['token']
    token2 = user2['token']
    _, priv_channel = channels_create
    time_length = 1

    # User1 starts a standup of length 1 sec.
    standup_create(token1, priv_channel, time_length)
    # Checking for active status.
    assert standup_active(token1, priv_channel)['is_active'] == True

    # Wait for standup to expire and then check status.
    time.sleep(time_length + 3)
    assert standup_active(token1, priv_channel)['is_active'] == False
    assert standup_active(token1, priv_channel)['time_finish'] == None

    # User2 starts another standup right after.
    standup_create(token2, priv_channel, time_length)
    # Checking for active status.
    assert standup_active(token2, priv_channel)['is_active'] == True

    # Wait for standup to expire and then check status.
    time.sleep(time_length)
    assert standup_active(token2, priv_channel)['is_active'] == False
    assert standup_active(token2, priv_channel)['time_finish'] == None
