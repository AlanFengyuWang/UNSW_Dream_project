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
from src.user import user_profile
from src.error import InputError, AccessError
from http_tests.channels_http_test import register_users, users, channels_create
from http_tests.helpers_http_test import member_info

ACCESS_ERROR = 403
INPUT_ERROR = 400

# --------------------------------------------------------------------------------------- #
# ----------------------------- Channel Detail Fixtures --------------------------------- #
# --------------------------------------------------------------------------------------- #
@pytest.fixture
def channel_details(users):
    ''' 
    Returns the expected details of 3 channels:
        - Public Channel [User1]
        - Private Channel [User1]
        - Public Channel [User1 & user2]
    '''
    channel1 = {
        'name': 'Public Channel',
        'is_public': True,
        'owner_members':[
            member_info(user_profile(users['user1']['token'], users['user1']['auth_user_id'])['user'])
        ],
        'all_members':[
            member_info(user_profile(users['user1']['token'], users['user1']['auth_user_id'])['user']),
        ]
    }

    channel2 = {
        'name': 'Private Channel',
        'is_public': False,
        'owner_members':[
            member_info(user_profile(users['user1']['token'], users['user1']['auth_user_id'])['user']),
        ],
        'all_members':[
            member_info(user_profile(users['user1']['token'], users['user1']['auth_user_id'])['user']),
        ]
    }

    channel_two_users = {
        'name': 'Public Channel',
        'is_public': True,
        'owner_members':[
            member_info(user_profile(users['user1']['token'], users['user1']['auth_user_id'])['user'])
        ],
        'all_members':[
            member_info(user_profile(users['user1']['token'], users['user1']['auth_user_id'])['user']),
            member_info(user_profile(users['user1']['token'], users['user2']['auth_user_id'])['user']),
        ]
    }
    return (channel1, channel2, channel_two_users)

@pytest.fixture
def create_valid_users():
    requests.delete(config.url + 'clear/v1')
    return {
        'user1' : requests.post(config.url + 'auth/register/v2', json = {
            'email' : 'user1email@email.com',
            'password' : 'password',
            'name_first' : 'firstname',
            'name_last' : 'lastname'
        }).json(),
        'user2' : requests.post(config.url + 'auth/register/v2', json = {
            'email' : 'user2email@email.com',
            'password' : 'password',
            'name_first' : 'firstname',
            'name_last' : 'lastname'
        }).json()
    }

@pytest.fixture
def create_valid_channels(create_valid_users):
    users = create_valid_users
    private = requests.post(config.url + 'channels/create/v2', json = {
        'token' : users['user1']['token'],
        'name' : 'private_channel',
        'is_public' : False
    }).json()
    public = requests.post(config.url + 'channels/create/v2', json = {
        'token' : users['user1']['token'],
        'name' : 'public_channel',
        'is_public' : True
    }).json()
    return {
        'private' : private,
        'public' : public,
    }

@pytest.fixture
def create_invalid(create_valid_users, create_valid_channels):
    users = create_valid_users
    channels = create_valid_channels
    return {
        'valid' : {
            'user' : users['user1'],
            'channel' : channels['public']
        },
        'invalid' : {
            'channel' : {
                'channel_id' : 42
            }
        }
    }

# --------------------------------------------------------------------------------------- #
# ----------------------------- Testing Channels Details -------------------------------- #
# --------------------------------------------------------------------------------------- #

def check_channel_details(user, channel_id, channel_detail):
    assert requests.get(config.url + 'channel/details/v2', \
        params={'token': user['token'], 'channel_id': channel_id}).json() == channel_detail

def test_check_channel_details(users, channels_create, channel_details):
    channel1, channel2 = channels_create
    channel_details1, channel_details2, _ = channel_details
    
    check_channel_details(users['user1'], channel1['channel_id'], channel_details1)
    check_channel_details(users['user1'], channel2['channel_id'], channel_details2)

# --------------------------------------------------------------------------------------- #
# ----------------------------- Testing Channels Invite --------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_check_channel_invite(users, channels_create, channel_details):
    user1 = users['user1']
    user2 = users['user2']
    _, _, channel_details_two_users = channel_details
    # User1 sets up their channel
    channel1, _ = channels_create
    # User1 invites user2 to join their channel
    requests.post(config.url + 'channel/invite/v2', json = {
        'token': user1['token'],
        'channel_id': channel1['channel_id'],
        'u_id': user2['auth_user_id']
    })
    # Check channel details for user2
    check_channel_details(user2, channel1['channel_id'], channel_details_two_users)

def test_channel_invite_invalid_channel_id(users, channels_create):
    invalid_channel, _ = channels_create
    # Delete the channel to make it invalid
    requests.delete(config.url + 'clear/v1')
    # Re-register users
    user1 = requests.post(config.url + 'auth/register/v2', json = register_users()['user1']).json()
    user2 = requests.post(config.url + 'auth/register/v2', json = register_users()['user2']).json()
    assert requests.post(config.url + 'channel/invite/v2', json = {
        'token': user1['token'],
        'channel_id': invalid_channel['channel_id'],
        'u_id': user2['auth_user_id']
    }).status_code == INPUT_ERROR

def test_channel_invite_invalid_u_id(users, channels_create):
    user2 = users['user2']
    # Delete the user2 to make them invalid
    requests.delete(config.url + 'clear/v1')
    # Have user1 attempt to invite user2
    user1 = requests.post(config.url + 'auth/register/v2', json = register_users()['user1']).json()
    channel1, _ = channels_create
    assert requests.post(config.url + 'channel/invite/v2', json = {
        'token': user1['token'],
        'channel_id': channel1['channel_id'],
        'u_id': user2['auth_user_id']
    }).status_code == INPUT_ERROR

def test_channel_invite_auth_not_member(users, channels_create):
    user1 = users['user1']
    user2 = users['user2']
    # User1's channel
    channel1, _ = channels_create
    # Have user2 who isn't part of the channel, invite user1
    assert requests.post(config.url + 'channel/invite/v2', json = {
        'token': user2['token'],
        'channel_id': channel1['channel_id'],
        'u_id': user1['auth_user_id']
    }).status_code == ACCESS_ERROR

def test_channel_details_invalid_channel(create_invalid):
    invalid = create_invalid
    assert requests.get(config.url + 'channel/details/v2', params={
        'token' : invalid['valid']['user']['token'],
        'channel_id' : invalid['invalid']['channel']['channel_id']
    }).status_code == INPUT_ERROR

def test_channel_details_not_member_public(create_valid_users, create_valid_channels):
    users = create_valid_users
    channels = create_valid_channels
    assert requests.get(config.url + 'channel/details/v2', params={
        'token' : users['user2']['token'],
        'channel_id' : channels['public']['channel_id']
    }).status_code == ACCESS_ERROR

def test_channel_details_not_member_private(create_valid_users, create_valid_channels):
    users = create_valid_users
    channels = create_valid_channels
    assert requests.get(config.url + 'channel/details/v2', params={
        'token' : users['user2']['token'],
        'channel_id' : channels['private']['channel_id']
    }).status_code == ACCESS_ERROR

def test_channel_messages_invalid_channel(create_invalid):
    invalid = create_invalid
    assert requests.get(config.url + 'channel/messages/v2', params={
        'token' : invalid['valid']['user']['token'],
        'channel_id' : invalid['invalid']['channel']['channel_id'],
        'start' : 0
    }).status_code == INPUT_ERROR

def test_channel_messages_not_member(create_valid_users, create_valid_channels):
    users = create_valid_users
    channels = create_valid_channels
    assert requests.get(config.url + 'channel/messages/v2', params={
        'token' : users['user2']['token'],
        'channel_id' : channels['private']['channel_id'],
        'start' : 0
    }).status_code == ACCESS_ERROR

def test_channel_messages_member(create_valid_users, create_valid_channels):
    users = create_valid_users
    channels = create_valid_channels
    resp = requests.get(config.url + 'channel/messages/v2', params={
        'token' : users['user1']['token'],
        'channel_id' : channels['private']['channel_id'],
        'start' : 0
    }).json()
    expected = {
        'messages' : [],
        'start' : 0,
        'end' : -1
    }
    assert resp == expected

def test_channel_join_invalid_channel(create_invalid):
    invalid = create_invalid
    assert requests.post(config.url + 'channel/join/v2', json = {
        'token' : invalid['valid']['user']['token'],
        'channel_id' : invalid['invalid']['channel']['channel_id']
    }).status_code == INPUT_ERROR

def test_channel_join_private(create_valid_users, create_valid_channels):
    users = create_valid_users
    channels = create_valid_channels
    assert requests.post(config.url + 'channel/join/v2', json = {
        'token' : users['user2']['token'],
        'channel_id' : channels['private']['channel_id']
    }).status_code == ACCESS_ERROR

def test_channel_join_private_global(create_valid_users, create_valid_channels):
    users = create_valid_users
    new_channel = requests.post(config.url + 'channels/create/v2', json = {
        'token' : users['user2']['token'],
        'name' : 'new_channel',
        'is_public' : False
    }).json()
    requests.post(config.url + 'channel/join/v2', json = {
        'token' : users['user1']['token'],
        'channel_id' : new_channel['channel_id']
    }).json()

    expected = requests.get(config.url + 'user/profile/v2', params={
        'token' : users['user1']['token'],
        'u_id' : users['user1']['auth_user_id']
    }).json()['user']
    expected = member_info(expected)
    details = requests.get(config.url + 'channel/details/v2', params={
        'token' : users['user2']['token'],
        'channel_id' : new_channel['channel_id']
    }).json()
    assert expected in details['all_members']

def test_channel_join_public(create_valid_users, create_valid_channels):
    users = create_valid_users
    channels = create_valid_channels
    requests.post(config.url + 'channel/join/v2', json = {
        'token' : users['user2']['token'],
        'channel_id' : channels['public']['channel_id']
    }).json()

    expected = requests.get(config.url + 'user/profile/v2', params={
        'token' : users['user2']['token'],
        'u_id' : users['user2']['auth_user_id']
    }).json()['user']
    expected = member_info(expected)
    details = requests.get(config.url + 'channel/details/v2', params={
        'token' : users['user2']['token'],
        'channel_id' : channels['public']['channel_id']
    }).json()
    assert expected in details['all_members']

# --------------------------------------------------------------------------------------- #
# ----------------------------- Testing Channel addowner -------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_channel_addowner_public(users, channels_create):
    # Get user profiles
    auth_profile = requests.get(config.url + 'user/profile/v2', params = {
        'token': users['user1']['token'],
        'u_id': users['user1']['auth_user_id']
    }).json()['user']

    user_profile = requests.get(config.url + 'user/profile/v2', params = {
        'token': users['user2']['token'],
        'u_id': users['user2']['auth_user_id']
    }).json()['user']
    
    # Create channels
    payload_public, _ = channels_create

    # Test Adding user as owner (public)
    requests.post(config.url + 'channel/addowner/v1', json = {
        'token': users['user1']['token'],
        'channel_id': payload_public['channel_id'],
        'u_id': users['user2']['auth_user_id']
    })

    channel_details = requests.get(config.url + 'channel/details/v2', params = {
        'token': users['user1']['token'],
        'channel_id': payload_public['channel_id']
    })

    payload_channel_details = channel_details.json()
    assert payload_channel_details['owner_members'] == [
        {
            'u_id': users['user1']['auth_user_id'],
            'email': auth_profile['email'],
            'name_first': auth_profile['name_first'],
            'name_last': auth_profile['name_last'],
            'handle_str': auth_profile['handle_str']
        },
        {
            'u_id': users['user2']['auth_user_id'],
            'email': user_profile['email'],
            'name_first': user_profile['name_first'],
            'name_last': user_profile['name_last'],
            'handle_str': user_profile['handle_str']        
        },
    ]



def test_channel_addowner_private(users, channels_create):
    # Get user profiles
    auth_profile = requests.get(config.url + 'user/profile/v2', params = {
        'token': users['user1']['token'],
        'u_id': users['user1']['auth_user_id']
    }).json()['user']

    user_profile = requests.get(config.url + 'user/profile/v2', params = {
        'token': users['user2']['token'],
        'u_id': users['user2']['auth_user_id']
    }).json()['user']
    
    # Create channels
    _, payload_private = channels_create  
    
    # Test Adding user as owner (private)
    requests.post(config.url + 'channel/addowner/v1', json = {
        'token': users['user1']['token'],
        'channel_id': payload_private['channel_id'],
        'u_id': users['user2']['auth_user_id']
    })

    channel_details = requests.get(config.url + 'channel/details/v2', params = {
        'token': users['user1']['token'],
        'channel_id': payload_private['channel_id']
    })
    
    payload_channel_details = channel_details.json()
    assert payload_channel_details['owner_members'] == [
        {
            'u_id': users['user1']['auth_user_id'],
            'email': auth_profile['email'],
            'name_first': auth_profile['name_first'],
            'name_last': auth_profile['name_last'],
            'handle_str': auth_profile['handle_str']
        },
        {
            'u_id': users['user2']['auth_user_id'],
            'email': user_profile['email'],
            'name_first': user_profile['name_first'],
            'name_last': user_profile['name_last'],
            'handle_str': user_profile['handle_str']        
        },
    ]

# --------------------------------------------------------------------------------------- #
# ----------------------------- Testing Channel removeowner ----------------------------- #
# --------------------------------------------------------------------------------------- #

def test_channel_removeowner_public(users, channels_create):
    # Get auth profile
    auth_profile = requests.get(config.url + 'user/profile/v2', params = {
        'token': users['user1']['token'],
        'u_id': users['user1']['auth_user_id']
    }).json()['user']
    
    # Create channels
    payload_public, _ = channels_create
    # Add user as owner to public channel 
    requests.post(config.url + 'channel/addowner/v1', json = {
        'token': users['user1']['token'],
        'channel_id': payload_public['channel_id'],
        'u_id': users['user2']['auth_user_id']
    })
    # Test removing owner
    requests.post(config.url + 'channel/removeowner/v1', json = {
        'token': users['user1']['token'],
        'channel_id': payload_public['channel_id'],
        'u_id': users['user2']['auth_user_id']    
    })
    channel_details = requests.get(config.url + 'channel/details/v2', params = {
        'token': users['user1']['token'],
        'channel_id': payload_public['channel_id']
    })

    payload_channel_details = channel_details.json()
    assert payload_channel_details['owner_members'] == [
        {
            'u_id': users['user1']['auth_user_id'],
            'email': auth_profile['email'],
            'name_first': auth_profile['name_first'],
            'name_last': auth_profile['name_last'],
            'handle_str': auth_profile['handle_str']
        }
    ]

def test_channel_removeowner_private(users, channels_create):
    # Get auth profile
    auth_profile = requests.get(config.url + 'user/profile/v2', params = {
        'token': users['user1']['token'],
        'u_id': users['user1']['auth_user_id']
    }).json()['user']

    # Create channels
    _, payload_private = channels_create

    # Add user as owner to private channel 
    requests.post(config.url + 'channel/addowner/v1', json = {
        'token': users['user1']['token'],
        'channel_id': payload_private['channel_id'],
        'u_id': users['user2']['auth_user_id']
    })

    # Test removing owner
    requests.post(config.url + 'channel/removeowner/v1', json = {
        'token': users['user1']['token'],
        'channel_id': payload_private['channel_id'],
        'u_id': users['user2']['auth_user_id']    
    })

    channel_details = requests.get(config.url + 'channel/details/v2', params = {
        'token': users['user1']['token'],
        'channel_id': payload_private['channel_id']
    })

    payload_channel_details = channel_details.json()

    assert payload_channel_details['owner_members'] == [
        {
            'u_id': users['user1']['auth_user_id'],
            'email': auth_profile['email'],
            'name_first': auth_profile['name_first'],
            'name_last': auth_profile['name_last'],
            'handle_str': auth_profile['handle_str']
        }
    ]

# --------------------------------------------------------------------------------------- #
# ----------------------------- Testing Channel leave ----------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_channelleave_public(users, channels_create):
    # Get auth profile
    auth_profile = requests.get(config.url + 'user/profile/v2', params = {
        'token': users['user1']['token'],
        'u_id': users['user1']['auth_user_id']
    }).json()['user']
    
    # Create channels
    payload_public, _ = channels_create

    # Join channel
    requests.post(config.url + 'channel/join/v2', json = {
        'token': users['user2']['token'],
        'channel_id': payload_public['channel_id'],
    })

    # Leave channel
    requests.post(config.url + 'channel/leave/v1', json = {
        'token': users['user2']['token'],
        'channel_id': payload_public['channel_id']
    })

    # Check details
    channel_details = requests.get(config.url + 'channel/details/v2', params = {
        'token': users['user1']['token'],
        'channel_id': payload_public['channel_id']
    })
    payload_channel_details = channel_details.json()
    assert payload_channel_details['all_members'] == [
        {
            'u_id': users['user1']['auth_user_id'],
            'email': auth_profile['email'],
            'name_first': auth_profile['name_first'],
            'name_last': auth_profile['name_last'],
            'handle_str': auth_profile['handle_str']
        }
    ]

def test_channelleave_private(users, channels_create):

    
    # Get auth profile
    auth_profile = requests.get(config.url + 'user/profile/v2', params = {
        'token': users['user1']['token'],
        'u_id': users['user1']['auth_user_id']
    }).json()['user']
    # Create channels
    _, payload_private = channels_create

    # Invite to channel
    requests.post(config.url + 'channel/invite/v2', json = {
        'token': users['user1']['token'],
        'channel_id': payload_private['channel_id'],
        'u_id': users['user2']['auth_user_id'],
    })

    # Leave channel
    requests.post(config.url + 'channel/leave/v1', json = {
        'token': users['user2']['token'],
        'channel_id': payload_private['channel_id']
    })

    # Check details
    channel_details = requests.get(config.url + 'channel/details/v2', params = {
        'token': users['user1']['token'],
        'channel_id': payload_private['channel_id']
    })
    payload_channel_details = channel_details.json()
    assert payload_channel_details['all_members'] == [
        {
            'u_id': users['user1']['auth_user_id'],
            'email': auth_profile['email'],
            'name_first': auth_profile['name_first'],
            'name_last': auth_profile['name_last'],
            'handle_str': auth_profile['handle_str']
        }
    ]
    

