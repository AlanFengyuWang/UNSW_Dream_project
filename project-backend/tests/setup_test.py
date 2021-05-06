'''
Authors:    
    Justin Wu, z5316037

Date:       
    12 April 2021
'''

import pytest

from src.auth import auth_register
from src.channels import channels_create
from src.channel import channel_invite
from src.other import clear

@pytest.fixture
def users():
    '''
    Fixture that sets up 2 users and returns each of their tokens and u_ids.
    '''
    clear()
    user1 = auth_register("userz@email.com", "jaajdfs23", "First", "User1")
    user2 = auth_register("test@email.com", "heskjdf23", "Second", "User2")
    token1 = user1['token']
    token2 = user2['token']
    u_id1 = user1['auth_user_id']
    u_id2 = user2['auth_user_id']
    return (token1, token2, u_id1, u_id2)

@pytest.fixture
def spare_user():
    '''
    Fixture that sets up a spare additional user.
    '''
    user3 = auth_register("test1@email.com", "heskjdf234", "third", "User3")
    token3 = user3['token']
    u_id3 = user3['auth_user_id']

    return (token3, u_id3)

@pytest.fixture
def channel_id(users):
    '''
    Returns the channel id of a public and private channel created by registered user1.
    '''
    user1, _, _ , u_id2 = users
    pub_id = channels_create(user1, 'public channel', True)['channel_id']
    priv_id = channels_create(user1, 'private channel', False)['channel_id']
    channel_invite(user1, priv_id, u_id2) 
    return (pub_id, priv_id)
