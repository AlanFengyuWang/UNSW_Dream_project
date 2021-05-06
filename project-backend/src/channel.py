"""
Authors:
    Alec Dudley-Bestow, z5260201
    Dionne So, z5310329
    Justin Wu, z5316037
    William Zheng, z5313015

Date:
    01 March 2021
"""

from src.error import InputError, AccessError
from src.auth import get_data, write_data, check_token, check_u_id
from src.user import user_profile
from src.helper import get_user_dictionary 

import datetime
import jwt

SECRET = 'atotallysecuresecret'

def notify_user(u_id, channel_id, notification_message):
    data = get_data()
    channel_index = get_channel_index(channel_id)
    notification = {
        'channel_id' : -1 if data['channels'][channel_index]['is_dm'] else channel_id,
        'dm_id' : channel_id if data['channels'][channel_index]['is_dm'] else -1,
        'notification_message' : notification_message
    }
    data['users'][check_u_id(u_id)]['notifications'].insert(0, notification)
    write_data(data)

def generate_addedChannel_notification(u_id, token, channel_name):
    data = get_data()
    handle_string = data['users'][check_token(token)]['handle_str']
    return f"{handle_string} added you to {channel_name}"

def update_user(key, num_channels, user):
    if user[key][-1]['num_' + key] != num_channels:
        user[key].append(
            {
                'num_' + key : num_channels, 
                'time_stamp' : datetime.datetime.now().timestamp()
            }
        )
    return user
   

def channel_stats_update(func):
    def wrap(*args, **kw):
        resp = func(*args, **kw)
        data = get_data()

        for i, user in enumerate(data['users']):
            num_dms = 0
            num_channels = 0
            for channel in data['channels']:
                if user_is_member(user['u_id'], channel):
                    if channel['is_dm']:
                        num_dms += 1
                    else:
                        num_channels += 1
            user = update_user('channels_joined', num_channels, user)  
            user = update_user('dms_joined', num_dms, user)
            data['users'][i] = user
        data = update_user('channels_exist', 
            len([channel for channel in data['channels'] if not channel['is_dm']]), data)
        data = update_user('dms_exist',
            len([dm for dm in data['channels'] if dm['is_dm']]), data)
        write_data(data)
        return resp
    return wrap

@channel_stats_update
def channel_invite(token, channel_id, u_id, is_dm = False):
    """
    Invites a user (with user id u_id) to join a channel with ID channel_id.
    Once invited the user is added to the channel immediately.

    Arguments:
        token(string): Id of user in a certain session.
        channel_id (int): Id to the channel u_id is being invited to.
        u_id (int): Id of user to be invited.

    Exceptions:
        InputError - Invalid auth_user_id or u_id or channel_id.
        InputError - User being invited is already a channel member.
        AccessError - When auth_user is not a member of the channel.
c
    Return Value:
        None
    """
    data = get_data()
    # Decode token to get the u_id
    auth_user_id = data['users'][check_token(token)]['u_id']

    # Check if auth_user_id and/or u_id exists in the database.
    check_u_id(u_id)

    # Check if channel_id exists.
    if not channel_id_valid(channel_id, data['channels']):
        raise InputError(description="Invalid channel id!")

    # Authorised user is not a member of the channel
    is_auth_a_member = member_check(auth_user_id, channel_id, data['channels'])
    if not is_auth_a_member:
        raise AccessError(description="Auth user is not a member of the channel!")

    # Check if u_id is already a member of the channel
    is_user_a_member = member_check(u_id, channel_id, data['channels'])
    if is_user_a_member:
        raise InputError(description="User has already been added!")
    
    for valid_channel in data['channels']:
        if valid_channel['channel_id'] == channel_id:
            channel_name = valid_channel['name']
            # Add user details to the all_members key.
            valid_channel['all_members'].append({'u_id': u_id})
    '''
    if not is_dm:
        num_channels_joined = data['users'][user_index]['channels_joined'][-1]['num_channels_joined'] + 1
        data['users'][user_index]['channels_joined'].append({'num_channels_joined' : num_channels_joined})
    else:
        num_dms_joined = data['users'][users_index]['dms_joined'][-1]['num_dms_joined'] + 1
        data['users'][user_index]['channels_joined'].append({'num_channels_joined' : num_channels_joined})
    '''
    write_data(data)
        
    notification_message = generate_addedChannel_notification(u_id, token, channel_name)
    notify_user(u_id, channel_id, notification_message)
    return {}

def channel_details(token, channel_id):
    '''
    Given a token and channel ID, checks both are valid and if user has access, 
    then returns channel details

    Arguments:
        token (str) - session specific user ID
        channel_id (int) - ID of channel user is requesting details of

    Exceptions:
        InputError  - Occurs when channel ID is not a valid ID
        AccessError - Occurs when token is invalid or when user does not have permissions
            required for accessing channel
        
    Returns:
        Returns (dict) on valid user_id, channel_id and permissions which contains: 
            channel name (str), owner_members (list) and all_members (list).
            The member lists contain dictionaries of: user IDs and first and last names
    '''

    user_index = check_token(token)

    data = get_data()

    channel_index = check_channel_id(channel_id)

    check_is_member(data['users'][user_index]['u_id'], data['channels'][channel_index]['all_members'])
    return get_channel_details(data['channels'][channel_index])

def channel_messages(token, channel_id, start):
    '''
    Index the list of channels in data and return the messages from the start index to 
    the end as well as a new end

    Arguments:
        token (str) - session specific user ID
        channel_id (int) - ID of channel of which messages are requested

    Exceptions:
        InputError  - Occurs when channel ID is not a valid ID
        AccessError - Occurs when token is not valid or when user is not a 
            member of the specified channel

    Returns:
        Returns (dict) which contains the messages, the starting index and the end index
    '''
    
    user_index = check_token(token)

    data = get_data()

    # check user is not a removed user
    try:
        check_u_id(data['users'][user_index]['u_id'])
    except InputError:
       raise AccessError(description='User ID is not valid') from None

    channel_index = check_channel_id(channel_id)

    check_is_member(data['users'][user_index]['u_id'], data['channels'][channel_index]['all_members'])
    
    num_messages= len(data['channels'][channel_index]['messages'])
    if start > num_messages:
        raise InputError('Start is greater than the total number of messages in the channel')
    
    end = start + 50 
    if end > num_messages:
        end = -1
    
    channel_messages = []
    
    if end == -1:
        for message in data['channels'][channel_index]['messages'][-start - 1::-1]:
            channel_messages.append(message)
    else:
        for message in data['channels'][channel_index]['messages'][-start - 1:-end - 1:-1]:
            channel_messages.append(message)
    
    return {'messages' : channel_messages, 'start' : start, 'end' : end}


@channel_stats_update
def channel_leave(token, channel_id):
    ''' 
    Given a channel ID, the user removed as a member of this channel. Their  
    messages should remain in the channel.

    Arguments:
        token - Token for auth user
        channel_id - Channel identification 

    Exceptions:
        InputError - Channel ID is not a valid channel
        AccessError - Authorised user is not a member of channel with channel_id

    Returns:
        None
    '''
    user_index = check_token(token)
    if not channel_is_valid(channel_id):
        raise InputError(description="Invalid channel_id")
    
    data = get_data()
    channel_index = get_channel_index(channel_id)
    user_id = data['users'][user_index]['u_id']
    
    #if user is the only owner and there are other members, ask them to promote another user
    if data['channels'][channel_index]['owner_members'] == [{'u_id' : user_id}]\
    and data['channels'][channel_index]['all_members'] != [{'u_id' : user_id}]:
        raise InputError(description="User is only owner, please promote another user")
        
    if not user_is_member(user_id, data['channels'][channel_index]):
        raise AccessError(description="Auth user is not a member")   
            
    data['channels'][channel_index]['all_members'].remove({'u_id' : user_id})
    try:
        data['channels'][channel_index]['owner_members'].remove({'u_id' : user_id})
    except:
        pass
        
    write_data(data)
    return {}


@channel_stats_update
def channel_join(token, channel_id):
    '''
    Given a user ID and channel ID, check if both are valid and whether the user has appropriate
    permissions (i.e. is a member of channel or a global owner). If they do, add the member to the channel
    
    Arguments:
        auth_user_id (int): ID of user trying to join channel
        channel_id (int): ID of channel user is trying to join

    Exceptions:
        InputError  - Occurs when channel ID is not a valid ID
        AccessError - Occurs when user ID is not authorised or when user does not have the required 
            permissions to join the channel (i.e. channel is not public and user is not global)

    Returns:
        None
    '''
    user_index = check_token(token)

    data = get_data()

    # check user is not a removed user
    try:
        check_u_id(data['users'][user_index]['u_id'])
    except InputError:
        raise AccessError(description='User ID is not valid') from None

    channel_index = check_channel_id(channel_id)

    try:
        check_is_member(data['users'][user_index]['u_id'], data['channels'][channel_index]['all_members'])
        raise InputError(description='User is already a member of channel')
    except AccessError:
        if not data['channels'][channel_index]['is_public']:
            check_global_owner(data['users'][user_index]['permission_id'])
        data['channels'][channel_index]['all_members'].append({'u_id' : data['users'][user_index]['u_id']})
        write_data(data)
        return {}

def channel_addowner(token, channel_id, u_id):
    ''' Add user with user id u_id as an owner of channel with channel id channel_id

    Arguments:
        token - Token for auth user
        channel_id - Channel identification 
        u_id - User identification of the user being added to channel
   
    Exceptions:
        InputError - Invalid channel id
        InputError - User is already an owner of the channel
        AccessError - Auth user is not an owner of Dreams or this channel

    Returns:
        None
    '''
    data = get_data()

    check_token(token)

    if channel_is_valid(channel_id) == False:
        raise InputError(description="Invalid channel_id")

    if user_is_owner_uid(u_id, channel_id) == True:
        raise InputError(description="User is already an owner of the channel")

    if user_is_owner_token(token, channel_id) == False:
        raise AccessError(description="Auth is not owner of Dreams or this channel")
    
    
    
    # Append user id to the owner list
    for channel in data['channels']:
        if channel['channel_id'] == channel_id:
            channel['owner_members'].append({'u_id' : u_id})   
            channel['all_members'].append({'u_id' : u_id})         
    
    write_data(data)

    return {}


def channel_removeowner(token, channel_id, u_id):
    ''' Remove user with user id u_id as an owner of channel with channel id channel_id

    Arguments:
        token - Token for auth user
        channel_id - Channel identification 
        u_id - User identification of the user being removed from channel

    Exceptions:
        InputError - Invalid channel id
        InputError - User is not a channel owner
        InputError - User is the only owner of the channel
        AccessError - Auth user is not an owner of Dreams or this channel

    Returns:
        None
    '''
    data = get_data()
    
    auth_user_id = data['users'][check_token(token)]['u_id']
    if not channel_is_valid(channel_id):
        raise InputError(description="Invalid channel_id")
    
    if not user_is_owner_uid(auth_user_id, channel_id):
        raise InputError(description="User is already an owner of the channel")
    for i, channel in enumerate(data['channels']):
        if channel['channel_id'] == channel_id:
            if len(channel['owner_members']) <= 1:
                raise InputError(description="User is the only owner of the channel")
            data['channels'][i]['owner_members'].remove({'u_id' : u_id})

    write_data(data)
    return {}
    
    
    

#------------------------------------------------------------------------------------#
#------------------------------- Helper functions -----------------------------------#
#------------------------------------------------------------------------------------#

def channel_id_valid(channel_id, channels):
    """
    Validates whether or not a given channel exists in the database.

    Arguments:
        channel_id: id of channel being validated.
        channels: list of dictionaries, with each dict containing channel info.

    Return value:
        (bool): Whether or not channel_id could be found.
    """
    for valid_channel in channels:
        if channel_id == valid_channel['channel_id']:
            return True
    return False

def user_is_member(user_id, channel):
    """
    Given a list of channel members, loop through and return true if user is a member 
    and false otherwise
    """
    for member in channel['all_members']:
        if user_id == member['u_id']:
            return True
    return False

def get_channel_details(channel):
    """
    Get channel details of a given channel ID

    Arguments:
        channel_id (int): ID of channel user is requesting details of

    Exceptions:
        None

    Returns:
        Returns details (dictionary) containing name of channel, whether
        it is public and list of owner members and a list of all members
    """
    details = {
        'name' : channel['name'],
        'is_public' : channel['is_public'],
        'owner_members' : get_member_details(channel['owner_members']),
        'all_members' : get_member_details(channel['all_members']),
    }
    return details

def get_member_details(member_list):
    """
    Gives details of members of a channel

    Arguments:
        member_list (list): a list of members in a channel

    Exceptions:
        None

    Returns:
        Returns details (list) on 
    """
    details = []

    for member in member_list:
        details.append(get_user_details(member['u_id']))
    return details


def get_channel_index(channel_id):
    """
    Index the list of channels in data and return the index of the given channel

    Arguments:
        channel_id (int): ID of channel being searched for

    Exceptions:
        None

    Returns:
        Returns i (int) which is the index of the given channel
    """
    data = get_data()
    i = 0
    for channel in data['channels']:
        if channel['channel_id'] == channel_id:
            return i
        i += 1
        
def member_check(user_id, channel_id, channels):
    """
    Validates whether or not a given user is a part of a given channel.

    Parameters:
        user_id: id of user being validated.
        channel_id: id of channel being validated.
        channels: list of dictionaries, with each dict containing channel info.

    Returns:
        (bool): Whether or not user could be found in the given channel.
    """
    for valid_channel in channels:
        if valid_channel['channel_id'] == channel_id:
            # Check if auth_user is a part of members
            for members in valid_channel['all_members']:
                if members['u_id'] == user_id:
                    return True
    return False

def get_user_details(u_id):
    """
    Given a valid user and list of members, loop through users and return user details

    Arguments:
        auth_user_id (int): ID of user being searched for
        users (list): list of dictionaries containing user details

    Exceptions:
        None

    Returns:
        Return details (dictionary) containing user ID and first and last names
    """
    data = get_data()
    user_index = check_u_id(u_id)
    details = {
        'u_id' : data['users'][user_index]['u_id'],
        'email' : data['users'][user_index]['email'],
        'name_first' : data['users'][user_index]['name_first'],
        'name_last' : data['users'][user_index]['name_last'],
        'handle_str' : data['users'][user_index]['handle_str'],
    }
    return details

def check_is_member(user_id, members):
    '''
    Validates whether or not a given user is a part of a given channel.

    Parameters:
        user_id (int): ID of user being validated.
        members (list): list of dictionaries containing user details of members of channel

    Returns:
        (bool): True is user is member of channel
    '''
    for member in members:
        if member['u_id'] == user_id:
            return True
    raise AccessError(description='User is not member of channel')

def check_channel_id(channel_id):
    '''
    Validates whether or not a given channel exists in the database.

    Arguments:
        channel_id (int): id of channel being validated.
        channels (list): list of dictionaries, with each dict containing channel info.

    Return value:
        i (int): index of channel 
    '''
    data = get_data()
    for i, channel in enumerate(data['channels']):
        if channel['channel_id'] == channel_id:
            return i
    raise InputError(description='Channel ID not valid')

def user_is_owner_token(token, channel_id):
    ''' Checks if auth user is an owner of a channel given a 
        channel id and token. 

        Arguments:
            token - Token for auth user
            channel_id - Channel identification 

        Returns:
            True if auth is an owner, false otherwise.
    '''

    user_index = check_token(token)
    data = get_data()
    for channel in data['channels']:
        if channel['channel_id'] == channel_id:
            for owner in channel['owner_members']:
                if owner['u_id'] == data['users'][user_index]['u_id']:
                    return True
    return False

def user_is_owner_uid(u_id, channel_id):
    ''' Checks if user is an owner of a channel given a 
        channel id and user id. 
        
        Arguments:
            u_id - user id for auth user
            channel_id - Channel identification 

        Returns:
            True if user is an owner, false otherwise.
    '''
    
    data = get_data()
    for channel in data['channels']:
        if channel['channel_id'] == channel_id:
            for owner in channel['owner_members']:
                if owner['u_id'] == u_id:
                    return True
    return False

def channel_is_valid(channel_id):
    ''' Checks weather a channel is valid given a channel id. 

        Arguments:
            channel_id - Channel identification.

        Returns:
            Returns True if a channel is found in the data, False otherwise. 
    '''

    data = get_data()
    for channel in data['channels']:
        if channel['channel_id'] == channel_id:
            return True
    return False

def check_global_owner(permission_id):
    '''
    Check if user has permission ID 1 which indicates global owner
    '''
    if permission_id == 1:
        return True
    raise AccessError(description='User does not have access to a private channel')

