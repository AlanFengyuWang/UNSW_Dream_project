'''
Authors: 
    Justin Wu, z5316037
    Alec Dudley-Bestow, z5260201
    Dionne So, z5310329
    William Zheng, z5313015

Date:
    23 March 2021
'''
from src.error import InputError, AccessError
from src.auth import get_data, write_data, check_u_id, check_token, generate_handle, check_token
from src.channels import channels_create, channels_list
from src.channel import channel_invite, channel_details, channel_messages, get_channel_index
from src.user import user_profile
from src.other import notify_user, generate_addedChannel_notification
from src.helper import find_dm, find_member, is_dm_creator

import jwt

SECRET = 'atotallysecuresecret'

def dm_create(token, u_ids):
    '''
    Given a token, user creates a DM.

    Arguments:
        token (jwt): authorization token
        u_id (int list): A list of user(s) that this DM is directed to, excluding the owner.

    Exceptions:
        InputError - U_id does not refer to a valid user

    Returns:
        Returns a dict containing dm_id and dm_name which is a sorted list of user handles.
   
    '''
    data = get_data()

    # Append creator's u_id to u_id list to set dm name to include the creator
    creator_index = check_token(token)
    u_ids.append(data['users'][creator_index]['u_id'])

    # dm name list is a concatenation of user handles
    handle_list = [data['users'][check_u_id(u_id)]['handle_str'] for u_id in u_ids]
    handle_list.sort()
    dm_name = ','.join(handle_list)

    # Re-using channels_create to generate dm_id 
    # Pass in 4th arg as 'True' for 'is_dm'
    channel = channels_create(token, dm_name, False, True)

    # Need to add the rest of u_ids to all members.
    # First remove owner's u_id from u_ids
    u_ids.remove(data['users'][creator_index]['u_id'])
    for user in u_ids:
        # Re-use channel_invite to append all member details
        channel_invite(token, channel['channel_id'], user)
    
    return {
        'dm_id': channel['channel_id'],
        'dm_name': dm_name
    }

def dm_list(token):
    '''
    Returns the list of DMs that the user is a member of.

    Arguments:
        token (jwt): authorization token.
    
    Exceptions:
        None
    
    Returns:
        A dict containing 'dms' which is a list of dictionaries, 
        where each dictionary contains types { dm_id, name }.
    '''
    channels = channels_list(token, True)
    channels['dms']  = channels.pop('channels')
    for i, _ in enumerate(channels['dms']):
        channels['dms'][i]['dm_id'] = channels['dms'][i].pop('channel_id')
    return channels

def dm_details(token, dm_id):
    '''
    Users that are part of this direct message can view basic 
    information about the DM.

    Arguments:
        token (jwt): authorization token.
        dm_id (int): id of the interested dm. 
    
    Exceptions:
        InputError - DM ID is not a valid DM.
        AccessError - Authorised user is not a member of this DM with dm_id
    
    Returns:
        A dict containing the name of the dm and the members of that dm.
    '''
    channel_det = channel_details(token, dm_id)
    dm_details = {
        'name': channel_det['name'],
        'members': channel_det['all_members']
    }
    return dm_details

def dm_invite(token, dm_id, u_id):
    '''
    This function can invite a user to an existing dm

    Arguments:
        token(string) - The inviter's token
        dm_id(integer) - the dm id number
        u_id(integer) - the invitee's auth_user_id

    Returns:
        None
    '''
    channel_invite(token, dm_id, u_id)

def dm_messages(token, dm_id, start):
    return channel_messages(token, dm_id, start)


def dm_leave(token, dm_id):
    '''
    Given a DM ID, the user is removed as a member of this DM
    
    Paramaters:
        token - token of authorised user
        dm_id - id for dm being left by auth user

    Exceptions: 
        InputError - dm_id is not a valid DM
        AccessError - Authorised user is not a member of DM with dm_id
    
    Returns:
        None
    '''
    data = get_data()
    user_index = check_token(token)
    dm = find_dm(dm_id, data)
    if dm == None:
        raise InputError(description='DM ID is not a valid DM!')

    member = find_member(dm, data['users'][user_index]['u_id'])
    if member == None:
        raise AccessError(description='Authorised user is not a member of this DM with dm_id!')

    dm['all_members'].remove({'u_id': data['users'][user_index]['u_id']})
    
    write_data(data)
    return {}


def dm_remove(token, dm_id):
    '''
    Remove an existing DM. This can only be done by the original creator of the DM.
    
    Paramaters:
        token - token of authorised user
        dm_id - id for dm being removed

    Exceptions: 
        InputError - dm_id does not refer to a valid DM 
        AccessError - the user is not the original DM creator
    
    Returns:
        None
    '''
    data = get_data()

    user_index = check_token(token)

    dm = find_dm(dm_id, data)
    if dm == None:
        raise InputError(description='Dm_id does not refer to a valid DM!')

    if is_dm_creator(dm, data['users'][user_index]['u_id']) == False:
        raise AccessError(description='The user is not the original DM creator!')

    data['channels'].remove(dm)

    write_data(data)
    return {}
