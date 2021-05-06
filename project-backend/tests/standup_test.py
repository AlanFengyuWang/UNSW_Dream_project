'''
Authors:    
    Justin Wu, z5316037

Date:       
    12 April 2021
'''

import pytest
import time

from src.auth import check_token
from src.error import InputError, AccessError
from src.standup import standup_start, standup_active, standup_send
from src.helper import check_channel_id
from src.user import user_profile
from src.channel import channel_messages
from tests.setup_test import users, spare_user, channel_id


# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for StandUp-Start --------------------------------- #
# --------------------------------------------------------------------------------------- #
def test_standup_start_valid(users, channel_id):
    '''
    Tests for a working standup in a channel.
    '''
    user1, user2, _, _ = users
    pub_channel, priv_channel = channel_id
    time_length = 5

    end_time1 = standup_start(user1, pub_channel, time_length)['time_finish']
    start_time1 = int(time.time())

    end_time2 = standup_start(user2, priv_channel, time_length)['time_finish']
    start_time2 = int(time.time())

    assert end_time1 == start_time1 + time_length
    assert end_time2 == start_time2 + time_length

def test_standup_back_to_back(users, channel_id):
    '''
    Tests if a standup is created immediately after another standup has finished
    in the same channel.
    '''
    user1, _, _, _ = users
    pub_channel, _ = channel_id
    time_length = 3

    end_time1 = standup_start(user1, pub_channel, time_length)['time_finish']
    start_time1 = int(time.time())

    # Wait 3 secs before making second standup
    time.sleep(3)

    end_time2 = standup_start(user1, pub_channel, time_length)['time_finish']
    start_time2 = int(time.time())

    assert end_time1 == start_time1 + time_length
    assert end_time2 == start_time2 + time_length

def test_standup_start_invalid_channelID(users):
    '''
    Tests for InputError when Channel ID is not a valid channel.
    '''
    user1, user2, _, _ = users
    time_length = 1

    with pytest.raises(InputError):
        standup_start(user1, 99, time_length)
        standup_start(user2, -99, time_length)

def test_standup_already_active(users, channel_id):
    '''
    Tests for InputError when an active standup is currently running in this channel.
    '''
    user1, user2, _, _ = users
    _, priv_channel = channel_id
    time_length = 5

    standup_start(user1, priv_channel, time_length)

    with pytest.raises(InputError):
        standup_start(user1, priv_channel, time_length)
        standup_start(user2, priv_channel, time_length)

def test_standup_auth_not_member(users, spare_user, channel_id):
    '''
    Tests for AccessError when authorised user is not in the channel.
    '''
    _, user2, _, _ = users
    user3, _ = spare_user
    pub_channel, priv_channel = channel_id
    time_length = 10

    with pytest.raises(AccessError):
        standup_start(user2, pub_channel, time_length)
        standup_start(user3, pub_channel, time_length)
        standup_start(user3, priv_channel, time_length)

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for StandUp-Active -------------------------------- #
# --------------------------------------------------------------------------------------- #
def test_standup_is_active(users, channel_id):
    '''
    Tests where a standup is active or not. If it is active, test for the correct time
    that the standup finishes. Otherwise, return None.
    '''
    user1, user2, _, _ = users
    pub_channel, priv_channel = channel_id
    time_length = 5
    end_time = int(time.time()) + time_length

    # Starting a standup for pub_channel
    standup_start(user1, pub_channel, time_length)
    resp = standup_active(user1, pub_channel)
    assert resp == {
        'is_active': True,
        'time_finish': end_time
    }

    # Priv_channel standup should be non-active.
    resp = standup_active(user2, priv_channel)
    assert resp == {
        'is_active': False,
        'time_finish': None
    }

    # Now start a standup for priv_channel
    standup_start(user2, priv_channel, time_length)
    resp = standup_active(user2, priv_channel)
    assert resp == {
        'is_active': True,
        'time_finish': end_time
    }

def test_standup_not_active(users, channel_id):
    '''
    Tests for correct output for non active standups
    '''
    user1, user2, _, _ = users
    pub_channel, priv_channel = channel_id
    
    resp1 = standup_active(user1, pub_channel)
    assert resp1 == {
        'is_active': False,
        'time_finish': None
    }

    resp2 = standup_active(user2, priv_channel)
    assert resp2 == {
        'is_active': False,
        'time_finish': None
    }

def test_standup_invalid_channelID(users, channel_id):
    '''
    Tests InputError when channel ID is not a valid channel.
    '''
    user1, user2, _, _ = users
    with pytest.raises(InputError):
        standup_active(user1, 99)
        standup_active(user2, -99)

def test_standup_active_different_intervals(users, channel_id):
    '''
    Tests for the status of StandUps in different time intervals.
    '''
    user1, user2, _, _ = users
    _, priv_channel = channel_id

    # StandUp length 1 sec
    standup_start(user1, priv_channel, 1)
    # Run standup_active after 2 secs
    time.sleep(2)
    resp = standup_active(user1, priv_channel)
    assert resp == {
        'is_active': False,
        'time_finish': None
    }

    # StandUp length 3 secs
    standup2 = standup_start(user2, priv_channel, 3)
    # Run standup_active after 1 sec
    time.sleep(1)
    resp = standup_active(user2, priv_channel)

    assert resp == {
        'is_active': True,
        'time_finish': standup2['time_finish']
    }

    # Check status after 5 secs.
    time.sleep(5)
    resp = standup_active(user2, priv_channel)
    assert resp == {
        'is_active': False,
        'time_finish': None
    }

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for StandUp-Send ---------------------------------- #
# --------------------------------------------------------------------------------------- #
def test_standup_single_send(users, channel_id):
    '''
    Tests for the successful implementation of standup_send where a sent message
    gets buffered in a standup queue.
    '''
    user1, _, u_id1, _ = users
    pub_channel, _ = channel_id

    # User1 starts a standup in pub_channel
    standup_start(user1, pub_channel, 3)['time_finish']

    # User1 sends message to standup.
    user1_msg = 'COMP1531'
    standup_send(user1, pub_channel, user1_msg)

    # Wait until standup period is over.
    time.sleep(4)

    # Format expected message.
    username1 = user_profile(user1, u_id1)['user']['handle_str']
    expected_msg = f"{username1}: {user1_msg}"

    # Check expected message against output.
    resp = channel_messages(user1, pub_channel, 0)['messages'][0]['message']
    assert resp == expected_msg

def test_standup_multiple_send(users, channel_id):
    '''
    Tests for the successful implementation of standup_send where multiple sent
    messages get buffered in a standup queue.
    '''
    user1, user2, u_id1, u_id2 = users
    _, priv_channel = channel_id

    # User1 starts a standup in priv_channel
    standup_start(user1, priv_channel, 3)['time_finish']

    # User1 & User 2 send messages to standup.
    user1_msg1 = 'abc'
    standup_send(user1, priv_channel, user1_msg1)
    user2_msg1 = 'xyz'
    standup_send(user2, priv_channel, user2_msg1)
    user1_msg2 = '123'
    standup_send(user1, priv_channel, user1_msg2)

    # Wait until standup period is over.
    time.sleep(3)

    # Format expected messages.
    username1 = user_profile(user1, u_id1)['user']['handle_str']
    username2 = user_profile(user2, u_id2)['user']['handle_str']
    nl = '\n'
    expected_msg = f"{username1}: {user1_msg1}{nl}" + \
    f"{username2}: {user2_msg1}{nl}" + \
    f"{username1}: {user1_msg2}"

    # Check expected message against output.
    resp = channel_messages(user1, priv_channel, 0)['messages'][0]['message']
    assert resp == expected_msg

def test_standup_send_invalid_channelID(users, channel_id):
    '''
    Tests for InputError when channel ID is not a valid channel.
    '''
    user1, user2, _, _ = users
    _, priv_channel = channel_id

    # User1 starts a standup in priv_channel
    standup_start(user1, priv_channel, 3)['time_finish']

    with pytest.raises(InputError):
        standup_send(user1, 99, 'Test1')
        standup_send(user2, -99, 'Test2')

def test_standup_send_message_too_long(users, channel_id):
    '''
    Tests for InputError when message is more than 
    1000 characters (not including the username and colon).
    '''
    user1, _, _, _ = users
    pub_channel, _ = channel_id

    # User1 starts a standup in pub_channel
    standup_start(user1, pub_channel, 3)['time_finish']

    with pytest.raises(InputError):
        standup_send(user1, pub_channel, 'a'*1001)

def test_standup_send_standup_not_active(users, channel_id):
    '''
    Tests for InputError when an active standup is not 
    currently running in this channel.
    '''
    user1, _, _, _ = users
    pub_channel, _ = channel_id

    # User1 starts a standup in pub_channel
    standup_start(user1, pub_channel, 3)['time_finish']

    # Let standup finish so that it's inactive
    time.sleep(4)

    with pytest.raises(InputError):
        standup_send(user1, pub_channel, 'hello')

def test_standup_send_auth_not_member(users, channel_id, spare_user):
    '''
    Tests for AccessError when the authorised user is not 
    a member of the channel that the message is within.
    '''
    user1, user2, _, _ = users
    user3, _ = spare_user
    pub_channel, _ = channel_id

    # User1 starts a standup in pub_channel
    standup_start(user1, pub_channel, 3)['time_finish']

    with pytest.raises(AccessError):
        standup_send(user2, pub_channel, '123')
        standup_send(user3, pub_channel, 'xyz')

    