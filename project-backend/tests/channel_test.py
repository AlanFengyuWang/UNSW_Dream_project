'''
Authors:    
    Alec Dudley-Bestow, z5260201
    Justin Wu, z5316037
    Dionne So, z5310329
Date:       
    7 March 2021
'''

import pytest

from src.error import InputError, AccessError
from src.auth import auth_register
from src.other import clear
from src.channels import channels_list, channels_create
from src.channel import channel_messages, channel_invite, channel_details, channel_join, channel_addowner, channel_removeowner
from src.user import user_profile
from src.message import message_send

@pytest.fixture(name='create_users_channels')
def fixture_create_users_channels():
    ''' 
    Clears data, sets up two fresh new users and two new channels

    Arguments:
        None

    Returns:
        (dict) : containing two users, their tokens and user IDs and the channel IDs of 
            a private and a public channel
    '''
    clear()
    user1 = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    return {
        'user1' : user1,
        'user2' : auth_register('email1@email.com', 'password', 'firstname', 'lastname'),
        'pub_channel' : channels_create(user1['token'], 'public channel', True)['channel_id'],
        'priv_channel' : channels_create(user1['token'], 'private channel', False)['channel_id'],
    }

@pytest.fixture(name='create_invalid')
def fixture_create_invalid():
    '''
    Clears data and sets up a valid and invalid user and channel
    
    Arguments:
        None
    
    Returns:
        (dict) : containing a valid and invalid key which each contain user details (dict) 
            (contains user IDs (int) and token (int)), and channel IDs (int)
    '''
    clear()
    valid_user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')
    return{
        'valid' : {
            'user' : valid_user,
            'channel': channels_create(valid_user['token'], 'public channel', True)['channel_id'],
        },
        'invalid' : {
            'channel' : 42,
        },
    }

def member_info(user_profile):
    return {
        'u_id': user_profile['u_id'],
        'email': user_profile['email'],
        'name_first': user_profile['name_first'],
        'name_last': user_profile['name_last'],
        'handle_str': user_profile['handle_str'],
    }

def test_channel_details_owner_public(create_users_channels):
    '''
    Tests that given a valid user as owner of a valid public channel, return channel details
    '''
    channels = create_users_channels

    user1_profile = user_profile(channels['user1']['token'], channels['user1']['auth_user_id'])['user']
    expected_details = {
        'name' : 'public channel', 
        'is_public' : True,
        'owner_members' : [member_info(user1_profile)],
        'all_members' : [member_info(user1_profile)],
    }
    assert channel_details(channels['user1']['token'], channels['pub_channel']) == expected_details
    
def test_channel_details_owner_private(create_users_channels):
    '''
    Tests that given a valid owner of private channel, channel details returns details
    '''   
    channels = create_users_channels

    user1_profile = user_profile(channels['user1']['token'], channels['user1']['auth_user_id'])['user']
    expected_details = {
        'name' : 'private channel', 
        'is_public' : False,
        'owner_members' : [member_info(user1_profile)],
        'all_members' : [member_info(user1_profile)],
    }
    assert channel_details(channels['user1']['token'], channels['priv_channel']) == expected_details

def test_channel_details_member_public(create_users_channels):
    '''
    Tests that given a valid member of public channel, returns correct channel details
    '''   
    channels = create_users_channels
    channel_join(channels['user2']['token'], channels['pub_channel'])

    user1_profile = user_profile(channels['user1']['token'], channels['user1']['auth_user_id'])['user']
    user2_profile = user_profile(channels['user2']['token'], channels['user2']['auth_user_id'])['user']
    expected_details = {
        'name' : 'public channel', 
        'is_public' : True,
        'owner_members' : [member_info(user1_profile)],
        'all_members' : [member_info(user1_profile), member_info(user2_profile)],
    }
    assert channel_details(channels['user2']['token'], channels['pub_channel']) == expected_details

def test_channel_details_member_private(create_users_channels):
    '''
    Tests that given a valid member of private channel, returns correct channel details
    '''   
    channels = create_users_channels

    user1_profile = user_profile(channels['user1']['token'], channels['user1']['auth_user_id'])['user']
    expected_details = {
        'name' : 'private channel', 
        'is_public' : False,
        'owner_members' : [member_info(user1_profile)],
        'all_members' : [member_info(user1_profile)],
    }
    assert channel_details(channels['user1']['token'], channels['priv_channel']) == expected_details

def test_channel_details_not_member_public(create_users_channels):
    '''
    Tests that given a token of a user that is not a member or a global owner of a public channel,
    return AccessError
    '''
    channels = create_users_channels

    with pytest.raises(AccessError):
        channel_details(channels['user2']['token'], channels['pub_channel'])

def test_channel_details_not_member_private(create_users_channels):
    '''
    Tests that given a token of a user that is not a member or a global owner of a private channel,
    return AccessError
    '''
    channels = create_users_channels

    with pytest.raises(AccessError):
        channel_details(channels['user2']['token'], channels['priv_channel'])
    
def test_channel_details_invalid_channel(create_invalid):
    '''
    Tests that given an invalid channel ID, returns InputError
    '''
    channels = create_invalid

    with pytest.raises(InputError):
        channel_details(channels['valid']['user']['token'], channels['invalid']['channel'])

def test_channel_messages_empty(create_users_channels):
    '''
    Tests that given the token of a member of channel, returns channel messages
    '''
    channels = create_users_channels

    expected = {
        'messages' : [],
        'start' : 0,
        'end' : -1,
    }
    assert channel_messages(channels['user1']['token'], channels['pub_channel'], 0) == expected

def test_channel_messages_single(create_users_channels):
    '''
    Tests that correct channel message details are returned
    '''
    channels = create_users_channels

    message_id = message_send(channels['user1']['token'], channels['pub_channel'], 'message')['message_id']

    expected = {
        'messages' : [{
            'message_id' : message_id,
            'u_id' : channels['user1']['auth_user_id'],
            'message' : 'message',
        }],
        'start' : 0,
        'end' : -1,
    }
    resp = channel_messages(channels['user1']['token'], channels['pub_channel'], 0)
    assert len(resp['messages']) == 1
    assert resp['messages'][0]['message_id'] == expected['messages'][0]['message_id']
    assert resp ['start'] == expected['start']
    assert resp ['end'] == expected['end']

def test_channel_messages_multiple(create_users_channels):
    '''
    Tests that when messages are added, returns correct number of channel messages, capping at 50
    '''
    channels = create_users_channels

    num_messages = 0
    while num_messages <= 50:
        message_send(channels['user1']['token'], channels['pub_channel'], str(num_messages))
        num_messages += 1

    returned_messages = channel_messages(channels['user1']['token'], channels['pub_channel'], 0)

    assert len(returned_messages['messages']) == 50
    assert returned_messages['messages'][0]['message'] == '50'
    assert returned_messages['messages'][len(returned_messages['messages']) - 1]['message'] == '1'
    assert returned_messages['start'] == 0 
    assert returned_messages['end'] == 50
    
def test_channel_messages_invalid_index(create_users_channels):
    ''' 
    Tests that channel_messages returns an Input error with an invalid index in both public and 
    private channels
    '''
    channels = create_users_channels
    channel_invite(channels['user1']['token'], channels['pub_channel'], channels['user2']['auth_user_id'])

    with pytest.raises(InputError):
        channel_messages(channels['user1']['token'], channels['pub_channel'], 10)
        channel_messages(channels['user2']['token'], channels['pub_channel'], 10)
        channel_messages(channels['user1']['token'], channels['priv_channel'], 2)

def test_channel_messages_no_access(create_users_channels):
    ''' 
    Tests that channel_messages returns an Access error when a user tries to access a channel they're not part of
    '''
    channels = create_users_channels

    with pytest.raises(AccessError):
        channel_messages(channels['user2']['token'], channels['priv_channel'], 0)

def test_channel_messages_invalid_token(create_users_channels):
    ''' 
    Tests that channel_messages returns AccessError if token is not valid
    '''
    channels = create_users_channels
    clear()
    new_user = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    new_pub_channel = channels_create(new_user['token'], 'public channel', True)
    with pytest.raises(AccessError):
        channel_messages(channels['user2']['token'], new_pub_channel['channel_id'], 0)

def test_channel_join_public(create_users_channels):
    '''
    Tests channel_join adds a user to a channel
    '''
    channels = create_users_channels
    new_channel = {
        'channel_id' : channels['pub_channel'],
        'name' : 'public channel',
    }
    assert new_channel not in channels_list(channels['user2']['token'])['channels']

    assert channel_join(channels['user2']['token'], channels['pub_channel']) == {}
    
    assert new_channel in channels_list(channels['user2']['token'])['channels']
    
def test_channel_join_private_global(create_users_channels):
    '''
    Tests that a global owner can join a private channel
    '''
    channels = create_users_channels
    new_channel_id = channels_create(channels['user2']['token'], 'new private channel', False)['channel_id']
    channel_join(channels['user1']['token'], new_channel_id)

    new_channel = {
        'channel_id' : new_channel_id,
        'name' : 'new private channel',
        }
    assert new_channel in channels_list(channels['user1']['token'])['channels']

def test_channel_join_private_not_global(create_users_channels):
    '''
    Tests that a non global user trying to join a private channel raises an AccessError
    '''
    channels = create_users_channels
    with pytest.raises(AccessError):
        channel_join(channels['user2']['token'], channels['priv_channel'])

def test_channel_join_invalid_channel(create_invalid):
    '''
    Tests that if an invalid channel ID is passed to channel join it raises an InputError
    '''
    channels = create_invalid
    with pytest.raises(InputError):
        channel_join(channels['valid']['user']['token'], channels['invalid']['channel'])

def test_channel_join_already_member(create_users_channels):
    '''
    Tests that a user that is already a member of a channel cannot join again
    '''
    channels = create_users_channels
    with pytest.raises(InputError):
        channel_join(channels['user1']['token'], channels['pub_channel'])

def test_channel_invite_already_member(create_users_channels):
    '''
    Tests that a user that is already a member of a channel cannot be invited again.
    '''
    channels = create_users_channels
    user1 = channels['user1']['token']
    user2 = channels['user2']['auth_user_id']
    channel_invite(user1, channels['pub_channel'], user2)
    with pytest.raises(InputError):
        channel_invite(user1, channels['pub_channel'], user2)

def test_channel_addowner(create_users_channels):
    channels = create_users_channels
    channel_invite(channels['user1']['token'], channels['pub_channel'], channels['user2']['auth_user_id'])
    channel_addowner(channels['user1']['token'], channels['pub_channel'], channels['user2']['auth_user_id'])

def test_channel_addowner_not_in_channel(create_users_channels):
    channels = create_users_channels
    channel_addowner(channels['user1']['token'], channels['pub_channel'], channels['user2']['auth_user_id'])

def test_channel_addowner_already_owner(create_users_channels):
    channels = create_users_channels
    with pytest.raises(InputError):
        channel_addowner(channels['user1']['token'], channels['pub_channel'], channels['user1']['auth_user_id'])

def test_channel_addowner_not_owner(create_users_channels):
    channels = create_users_channels
    with pytest.raises(AccessError):
        channel_addowner(channels['user2']['token'], channels['pub_channel'], channels['user2']['auth_user_id'])

def test_channel_addowner_not_channel(create_users_channels):
    channels = create_users_channels
    with pytest.raises(InputError):
        channel_addowner(channels['user1']['token'], 42, channels['user2']['auth_user_id'])

def test_channel_removeowner(create_users_channels):
    channels = create_users_channels
    channel_addowner(channels['user1']['token'], channels['pub_channel'], channels['user2']['auth_user_id'])
    channel_removeowner(channels['user2']['token'], channels['pub_channel'], channels['user1']['auth_user_id'])

def test_channel_removeowner_target_notowner(create_users_channels):
    channels = create_users_channels
    channel_invite(channels['user1']['token'], channels['pub_channel'], channels['user2']['auth_user_id'])
    with pytest.raises(InputError):
        channel_removeowner(channels['user1']['token'], channels['pub_channel'], channels['user2']['auth_user_id'])

def test_channel_removeowner_notonwer(create_users_channels):
    channels = create_users_channels
    channel_invite(channels['user1']['token'], channels['pub_channel'], channels['user2']['auth_user_id'])
    
    with pytest.raises(InputError):
        channel_removeowner(channels['user1']['token'], channels['pub_channel'], channels['user2']['auth_user_id'])


def test_channel_removeowner_onlyowner(create_users_channels):
    channels = create_users_channels
    with pytest.raises(InputError):
        channel_removeowner(channels['user1']['token'], channels['pub_channel'], channels['user1']['auth_user_id'])

def test_channel_removeowner_not_channel(create_users_channels):
    channels = create_users_channels
    with pytest.raises(InputError):
        channel_removeowner(channels['user1']['token'], 42, channels['user2']['auth_user_id'])
