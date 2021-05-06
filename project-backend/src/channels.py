'''
Authors: 
    William Zheng, z5313015
    Justin Wu, z5316037

Date:
    01 March 2021
'''

from src.auth import get_data, write_data, check_token, check_u_id
from src.channel import channel_stats_update
from src.error import InputError, AccessError
from src.user import user_profile
from src.helper import channel_id_generate, create_channel_details

import datetime
import jwt

SECRET = 'atotallysecuresecret'

def channels_list(token, is_dm=False):
    '''
    Given a user ID, if the ID is valid, this function returns a list of channels 
    the user is a part of (and their associated details).

    Arguments:
        token - Token of current user.

    Exceptions:
        AccessError - Occurs when user  ID is not authorised or when user is not a 
        member of the specified channel

    Returns:
        Returns channel_dict(dictionary) which contains a list of dictionaries.
   
    '''
    # Check if auth_user exists in the database
    data = get_data()
    
    check_token(token)

    token_structure = jwt.decode(token, SECRET, algorithms=['HS256'])
    u_id = token_structure['u_id']
    
    channel_dict = {'channels' : []}

    # Loop through all channels stored in data file.
    for channel in data['channels']:
        if is_dm == channel['is_dm']:
            # Get details of the current channel.
            curr_channel = {
                'channel_id': channel['channel_id'],
                'name': channel['name']
            }
            for member in channel['all_members']:
                if member["u_id"] == u_id:
                    channel_dict['channels'].append(curr_channel)
    return channel_dict

def channels_listall(token, is_dm=False):
    '''
    Given a user ID, if the ID is valid, this function returns
    a list of all channels in the database (and their associated details).

    Arguments:
        token - Token of current user.

    Exceptions:
        AccessError - Occurs when user  ID is not authorised or when user is not a 
        member of the specified channel

    Returns:
        Returns channel_dict(dictionary) which contains a list of dictionaries.
   
    '''
    data = get_data()
    
    check_token(token)

    channel_dict = {
        'channels': []
    }

    channel_list = channel_dict['channels']
    
    # Loop through all channels stored in data file.
    for channel in data['channels']:
        if is_dm == channel['is_dm']: 
            # Get channel details and append it to the list
            curr_channel = {
                'channel_id': channel['channel_id'],
                'name': channel['name']
            }
            channel_list.append(curr_channel)

    return channel_dict


# Creates a new channel with that name that is either a public or private channel

@channel_stats_update
def channels_create(token, name, is_public, is_dm=False):
    """
    Creates a new channel with that name that is either a public or private channel.

    Arguments:
        token(string): Id of user in a certain session.
        name (string): Name of the channel.
        is_public (bool): Whether the channel is public or private.

    Exceptions:
        InputError - Invalid auth_user_id.
        InputError - Channel name is longer than 20 chars or is 0 chars.

    Return Value:
        Dictionary with item "channel_id".
    """
    data = get_data()

    # Validate token
    check_token(token)

    # Name is longer than 20 chars long.
    if not is_dm and len(name) > 20:
        raise InputError(description="Channel name is longer than 20 characters")

    # Name is empty.
    if len(name) == 0:
        raise InputError(description="Invalid channel name!")

    # Decode token to get the u_id
    token_structure = jwt.decode(token, SECRET, algorithms=['HS256'])
    u_id = token_structure['u_id']

    # Look into the database to find a new channel_id.
    channel_id = channel_id_generate(data['channels'])

    # Decode token to get the u_id
    token_structure = jwt.decode(token, SECRET, algorithms=['HS256'])
    u_id = token_structure['u_id']

    # Add channel details to the database.
    channel_details = create_channel_details(channel_id, name, token, u_id, is_public, is_dm)
    data['channels'].append(channel_details)
    write_data(data)

    return {
        'channel_id': channel_id,
    }
