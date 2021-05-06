from src.auth import get_data
from src.error import InputError, AccessError
from src.auth import get_data, write_data, check_token, check_u_id

import jwt
import re

# --------------------------------------------------------------------------------------- #
# ----------------------------- Channel Helpers  ---------------------------------------- #
# --------------------------------------------------------------------------------------- #
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

def user_is_member(user_id, channel):
    """
    Given a list of channel members, loop through and return true if user is a member 
    and false otherwise
    """
    for member in channel['all_members']:
        if user_id == member['u_id']:
            return True
    return False

# --------------------------------------------------------------------------------------- #
# ----------------------------- Channels Helpers  --------------------------------------- #
# --------------------------------------------------------------------------------------- #
def channel_id_generate(all_channels):
    """
    Generates a channel id for a given channel.

    Arguments:
        all_channels (list): Contains a list of existing channels.

    Return Value:
        Available channel_id (int).
    """
    channel_id = 1
    for channel in all_channels:
        if channel['channel_id'] == channel_id:
            # Keep incrementing channel_id by 1 until we get a new channel_id
            channel_id += 1
    return channel_id

def create_channel_details(channel_id, name, token, u_id, is_public, is_dm):
    """
    Adds channel details to the database.

    Paramters:
        channel_id (int): Id of channel being created.
        name (string): Name of the channel.
        u_id (int): The channel creator's id.
        is_public (bool): Whether the channel is public or private.

    Returns:
        Available channel_id (int)
    """
    owner_details = []
    owner_details.append({'u_id': u_id})

    # The only member that exists is the owner
    all_member_details = []
    #Find the information of the members
    all_member_details.append({'u_id': u_id})
    
    standup_details = {
        'is_active': False,
        'time_finish': None,
        'u_id': None,
        'queued_messages:': []
    }
    
    channel_details = {
        'channel_id' : channel_id,
        'name' : name,
        'owner_members' : owner_details,
        'all_members' : all_member_details,
        'is_public' : is_public,
        'is_dm' : is_dm,
        'messages' : [],
        'standup': standup_details
    }
    return channel_details


# --------------------------------------------------------------------------------------- #
# ----------------------------- Dm Helpers ---------------------------------------------- #
# --------------------------------------------------------------------------------------- #
def find_dm(dm_id, data):
    for channel in data['channels']:
        if channel['channel_id'] == dm_id:
            return channel
    return None

def find_member(dm, u_id):
    for member in dm['all_members']:
        if member['u_id'] == u_id:
            return member
    return None

def is_dm_creator(dm, u_id):
    for member in dm['owner_members']:
        if member['u_id'] == u_id:
            return True
    return False

# --------------------------------------------------------------------------------------- #
# ----------------------------- Message Helpers  ---------------------------------------- #
# --------------------------------------------------------------------------------------- #
# Creates a new unique id for message.
def message_id_generate():
    data = get_data()
    message_id = 1
    # Search across all channels and all messages.
    for channels in data['channels']:
        for message in channels['messages']:
            if message['message_id'] == message_id:
                message_id += 1
    return message_id

def message_too_long(message):
    if len(message) > 1000:
        raise InputError(description="Message is more than 1000 characters!")

def search_message_id(message_id):
    '''
    Given a message_id, search the channel database to return channel_id & the index of the message.
    '''
    data = get_data()
    for channel in data['channels']:
        for msg_index, message in enumerate(channel['messages']):
            if message['message_id'] == message_id:
                return (channel['channel_id'], msg_index)
    
    # Message not found.
    raise InputError(description="Message_id is not valid!")

def owner_check(owner_members, u_id):
    for member in owner_members:
        if member['u_id'] == u_id:
            return True
    raise AccessError(description="Authorised user is NOT an owner of this channel!")
    
def message_id_exists(message_id):
    data = get_data()
    for channel in data['channels']:
        for message in channel['messages']:
            if message['message_id'] == message_id:
                return (message, channel)
    return (None, None)

def message_is_sender(u_id, message):
    if u_id == message['u_id']:
        return True
    return False

def already_reacted(react_id, message):
    for reacts in message['reacts']:
        if reacts['react_id'] == react_id:
            if reacts['is_this_user_reacted'] == True:
                return True
    return False

def edit_react(message, react_id, u_id, append_or_remove):
    for reacts in message['reacts']:
        if reacts['react_id'] == react_id:
            if append_or_remove == 'remove':
                reacts['u_ids'].remove(u_id)
                reacts['is_this_user_reacted'] = False
            elif append_or_remove == 'append':
                reacts['u_ids'].append(u_id)
                reacts['is_this_user_reacted'] = True

# --------------------------------------------------------------------------------------- #
# ------------------------------ User Helpers  ------------------------------------------ #
# --------------------------------------------------------------------------------------- #
#checks if a given handle is of a valid type
def valid_handle(handle_str):
    return 3 <= len(handle_str) <= 20 and not bool(re.search(handle_str, r"[-@]"))

#returns the correct information from a user
def get_user_dictionary(user):
    return {
        'u_id': user['u_id'],
        'email': user['email'],
        'name_first': user['name_first'],
        'name_last': user['name_last'],
        'handle_str': user['handle_str']
    }

def get_user_dictionary_for_user_profile(user):
    return {
        'u_id': user['u_id'],
        'email': user['email'],
        'name_first': user['name_first'],
        'name_last': user['name_last'],
        'handle_str': user['handle_str'],
        "profile_img_url": user['profile_img_url']
    }




