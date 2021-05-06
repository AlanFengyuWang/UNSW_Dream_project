'''
Authors: 
    William Zheng, z5313015
    Justin Wu, z5316037

Date:
    07 March 2021
'''

import pytest
from src.channels import channels_list, channels_listall, channels_create
from src.channel import channel_join, channel_invite
from src.auth import auth_register
from src.other import clear
from src.error import InputError

def test_channels_list_public():
    '''
    Testing channels_list when the user has only joined a public channel.

    Parameters:

    Returns:
    '''
    # Clear and create new channels.
    clear()
    token = auth_register('firstlast@gmail.com', 'password', "Marc","Chee")['token']
    public_channel = channels_create(token, 'Public Channel', True)

    # Join channel with a new user.
    user_id1 = auth_register('first1last1@gmail.com', 'password1', "first","last")
    channel_join(user_id1['token'], public_channel['channel_id'])
    channels_joined =  {
        'channels': [
            {   
        		'channel_id': public_channel['channel_id'], 
                'name': 'Public Channel'
        	}
        ]
    }
    assert channels_list(token) == channels_joined

def test_channels_list_private():
    '''
    Testing channels_list when the user has only joined a private channel.

    Parameters:

    Returns:
    '''
    # Clear and create new channels.
    clear()
    token = auth_register('firstlast@gmail.com', 'password', "Marc","Chee")['token']
    private_channel = channels_create(token, 'Private Channel', False)

    # Invite new user to the channel.
    user_id1 = auth_register('first1last1@gmail.com', 'password1', "first","last")['auth_user_id']
    channel_invite(token, private_channel['channel_id'], user_id1)
    channels_joined = {
        'channels': [
        	{
        		'channel_id': private_channel['channel_id'],
        		'name': 'Private Channel',
        	}
        ]
    }
    assert channels_list(token) == channels_joined

def test_channels_list_both():
    '''
    Testing channels_list when the user has joined both private and public channels.

    Parameters:

    Returns:
    '''
    # Clear and create new channels.
    clear()
    token1 = auth_register('firstlast@gmail.com', 'password', "Marc","Chee")['token']
    public_channel = channels_create(token1, 'Public Channel', True)
    private_channel = channels_create(token1, 'Private Channel', False)

    # Invite new user to the private channel and join public channel.
    user2 = auth_register('first1last1@gmail.com', 'password1', "first","last")
    token2 = user2['token']
    u_id2 = user2['auth_user_id']
    channel_join(token2, public_channel['channel_id'])
    channel_invite(token1, private_channel['channel_id'], u_id2)
    channels_joined = {
        'channels': [
        	{
        		'channel_id': public_channel['channel_id'],
        		'name': 'Public Channel',
        	},
            {
                'channel_id': private_channel['channel_id'],
        		'name': 'Private Channel',
            }
        ]
    }
    assert channels_list(token2) == channels_joined

def test_channels_list_none():
    '''
    Testing channels_list when the user hasn't joined any channels.

    Parameters:

    Returns:
    '''
    clear()
    user_id1 = auth_register('first1last1@gmail.com', 'password1', "first","last")['token']
    channels_joined = {'channels': []}
    assert channels_list(user_id1) == channels_joined

def test_channels_listall_both():
    '''
    Testing if channels_listall returns a list of all channels (both public and private)

    Parameters:

    Returns:
    '''
    # Clear and create new channels.
    clear()
    auth_user_id = auth_register('firstlast@gmail.com', 'password', "Marc","Chee")['token']
    public_channel = channels_create(auth_user_id, 'Public Channel', True)
    public_channel1 = channels_create(auth_user_id, 'Public Channel 1', True)
    private_channel = channels_create(auth_user_id, 'Private Channel', False)
    private_channel1 = channels_create(auth_user_id, 'Private Channel 1', False)

    user_id1 = auth_register('first1last1@gmail.com', 'password1', "first","last")['token']
    
    channels_all = {
        'channels': [
            {
        		'channel_id':  public_channel['channel_id'],
        		'name': 'Public Channel',
        	},
            {
                'channel_id': public_channel1['channel_id'],
                'name': 'Public Channel 1'
            },
        	{
        		'channel_id': private_channel['channel_id'],
        		'name': 'Private Channel',
        	},
            {
                'channel_id': private_channel1['channel_id'],
                'name': 'Private Channel 1'
            }
        ]
    }
    assert channels_listall(user_id1) == channels_all

def test_channels_listall_none():
    '''
    Testing channels_listall when no channels have been created.

    Parameters:

    Returns:
    '''
    clear()
    user_id1 = auth_register('first1last1@gmail.com', 'password1', "first","last")['token']
    channels = {'channels': []}
    assert channels_list(user_id1) == channels

def test_create_public_channel():
    clear()
    # Channels_create requires an auth_id
    auth_id1 = auth_register('user@gmail.com', 'password1234', 'Marc', 'Chee')['token']
    auth_id2 = auth_register('user2@gmail.com', 'pw1234', 'David', 'Chee')['token']
    # Because this is the 1st channel created, id should be 1
    assert channels_create(auth_id1, "Marc's Channel", True) == {'channel_id' : 1}
    # 2nd channel created, hence id should be 2
    assert channels_create(auth_id2, "David's Channel", True) == {'channel_id' : 2}

def test_create_private_channel():
    clear()
    auth_id1 = auth_register('hello@gmail.com', 'asdfadf', 'Mike', 'Wang')['token']
    auth_id2 = auth_register('hello1@gmail.com', 'pw12345678', 'Beau', 'Ryan')['token']
    auth_id3 = auth_register('hello2@gmail.com', '235678', 'Ian', 'Jacobs')['token']
    assert channels_create(auth_id1, "Mikey", False) == {'channel_id' : 1}
    assert channels_create(auth_id2, "Beau's", False) == {'channel_id' : 2}
    assert channels_create(auth_id3, "Ian", False) == {'channel_id' : 3}

def test_identical_channel_id_public():
    clear()
    auth_id1 = auth_register('Mat@gmail.com', 'password1234', 'Mat', 'Nuggen')['token']
    auth_id2 = auth_register('Paul@gmail.com', 'asdfadsf', 'Paul', 'Smith')['token']
    channel_id1 = channels_create(auth_id1, "COMP1531", True)
    channel_id2 = channels_create(auth_id2, "COMP1531", True)
    assert channel_id1 != channel_id2 #Assert if channel_ids are the same

# Same channel names but one is public and the other is private.
def test_identical_channel_id_private():
    clear()
    auth_id1 = auth_register('Mat@gmail.com', 'password1234', 'Mat', 'Nuggen')['token']
    channel_id1 = channels_create(auth_id1, "COMP1531", True)
    channel_id2 = channels_create(auth_id1, "COMP1531", False)
    assert channel_id1 != channel_id2 #Assert if channel_ids are the same

def test_channels_create_except():
    clear()
    auth_id = auth_register('user3@gmail.com', 'password1234', 'Marc', 'Chee')['token']
    with pytest.raises(InputError):
        channels_create(auth_id, "adf" * 20, True) # Name is over 20 characters.

    with pytest.raises(InputError):
        channels_create(auth_id, "adf" * 20, False)

    with pytest.raises(InputError):
        channels_create(auth_id, '', True) #Invalid channel name

    with pytest.raises(InputError):
        channels_create(auth_id, '', False)
