'''
Authors:
    Alec Dudley-Bestow, z5260201
    
Date:
    16 March 2021
'''

from src.error import InputError, AccessError
from src.auth import check_token, get_data, check_u_id, write_data
from src.channel import check_is_member, notify_user
from flask import Flask
from json import dumps, dump
from src import config
from src.auth import get_data, write_data, check_u_id, check_token
import re
import datetime
OWNER = 1
MEMBER = 2

def clear():
    '''
    Clears the data in data.json file, if the file doesn't exist it creates one
    
    Arguments:
        None
    
    Exceptions:
        None
    
    Return Values:
        None
    '''
    ts = datetime.datetime.now().timestamp()
    with open("data.json", "w+") as f:
        data = {
            "users" : [],
            "channels" : [],
            'channels_exist' : [{'num_channels_exist' : 0, 'time_stamp' : ts}],
            'dms_exist' : [{'num_dms_exist' : 0, 'time_stamp' : ts}],
            'messages_exist' : [{'num_messages_exist' : 0, 'time_stamp' : ts }]
        }
        dump(data, f)
        return dumps({})


def notifications_get(token):
    '''
    This function get the first 20 notifications for a user

    Arguments:
        token(string) - The user's token

    Returns:
        notifications(list of dictioanry) - user's top 20 notifications
    '''

    data = get_data()
    #return the top 20 notifications
    notifications = []
    i = 0

    for notification in data['users'][check_token(token)]['notifications']:
        if i >= 20 or not notification:
            break
        notifications.append(notification)
        i += 1
    return {'notifications' : notifications}


def search(token, query_str):
    '''
        searches through all channels and dms a user is part of and returns 
        all the messages that include the query string

    Arguments:
        token (string) - a user's session jwt token
        query_str (string) - the given search term
        
    Exceptions:
        InputError - when the query_str is longer than a thousand characters
        
    Return Value:
        Returns a list of all the related messages
    '''
    if len(query_str) > 1000:
        raise InputError(description='query_str is above 1000 characters')
    data = get_data()
    u_id = data['users'][check_token(token)]['u_id']
    messages = []
    for channel in data['channels']:
        for message in channel['messages']:
            if (query_str in message['message'] or not query_str) and message['u_id'] == u_id:
                messages.append(
                    {
                        'message_id' : message['message_id'],
                        'u_id' : message['u_id'],
                        'message' : message['message'],
                        'time_created' : message['time_created'],
                    }
                )
    return {
        'messages': messages,
    }

def tagged_info(message):
    data = get_data()
    tagged_names = []
    user_info = []
    if '@' in message:
        names = re.findall(r"@\w+", message)
        for name in names:
            name = name[1:]
            tagged_names.append(name)
        #Find the tagged_name's u_id:
        for tagged_name in tagged_names:
            for user in data['users']:
                if user['handle_str'] == tagged_name:
                    user_info.append({
                        'u_id': user['u_id'],
                        'handle_str': user['handle_str']
                    })
                    break
    return user_info

def valid_tag_target(handle, u_id, channel_id):
    data = get_data()
    #Check the user's handle 
    if data['users'][check_u_id(u_id)]['handle_str'] == handle and \
    check_valid_dm_member(u_id, channel_id):
        return True
    return False

def check_valid_dm_member(u_id, channel_id):
    data = get_data()
    for channel in data['channels']:
        if channel['channel_id'] == channel_id:
            for eachMember in channel['all_members']:
                if u_id == eachMember['u_id']:
                    return True
    return False  

def generate_tag_notification_message(u_id, channel_id, token, message):
    '''
    This function only returns the tag notificatoin

    Arguments:
        u_id(integer)
        token(integer)
        channel_name(string)
        message(string)
    
    Returns:
        Tag notificatoin
    '''
    data = get_data()
    channel_name = ''
    for channel in data['channels']:
        if channel['channel_id'] == channel_id:
            channel_name = channel['name']
    handle_string = data['users'][check_token(token)]['handle_str']
    return f"{handle_string} tagged you in {channel_name}: {message[:20]}"


def insert_tag_notification(token, channel_id, message):
    '''
        searches through all channels and dms a user is part of and returns 
        all the messages that include the query string

    Arguments:
        token (string) - a user's session jwt token
        query_str (string) - the given search term
        
    Exceptions:
        InputError - when the query_str is longer than a thousand characters
        
    Return Value:
        Returns a list of all the related messages
    '''
    if '@' not in message:
        return
    targets_info = tagged_info(message)
    for target_info in targets_info:
        if valid_tag_target(target_info['handle_str'], target_info['u_id'], channel_id):
            notify_user(target_info['u_id'], channel_id, \
            generate_tag_notification_message(target_info['u_id'], channel_id, token, message))


def generate_addedChannel_notification(u_id, token, channel_name):
    data = get_data()
    handle_string = data['users'][check_token(token)]['handle_str']
    return f"{handle_string} added you to {channel_name}"


#returns true if there is only one owner
def only_one_owner():
    data = get_data()
    owner_count = 0
    for user in data['users']:
        if user['permission_id'] == OWNER:
            owner_count += 1
    
    return owner_count == 1

def admin_user_remove(token, u_id):
    '''
        replaces a users first and last name with 'Removed user' 
        along with the contents of all messages they've sent
        they can no longer log in and none of their requests will be fulfilled

    Arguments:
        token (string) - a user's session jwt token
        u_id (int) - the user id of the target of the permission change
        
    Exceptions:
        InputError - when the u_id is invalid
        InputError - when the target user is the only owner
        AccessError - when the token doesn't have owner permissions
        
    Return Value:
        Returns an empty dictionary
    '''
    data = get_data()
    if data['users'][check_token(token)]['permission_id'] != OWNER:
        raise AccessError(description='The authorised user is not an owner')
    user_index = check_u_id(u_id)
    if data['users'][user_index]['permission_id'] == OWNER and only_one_owner():
        raise InputError(description='The user is currently the only owner')
    
    data['users'][user_index]['name_first'] = 'Removed user'
    data['users'][user_index]['name_last'] = 'Removed user'
    
    for channel in data['channels']:
        for message in channel['messages']:
            if message['u_id'] == u_id:
                message['message'] = 'Removed user'
    
    data['users'][user_index]['sessions_list'] = []
    write_data(data)
    return {}


def admin_userpermission_change(token, u_id, permission_id):
    '''
        Changes a users permission

    Arguments:
        token (string) - a user's session jwt token
        u_id (int) - the user id of the target of the permission change
        permission_id(int) - the new permission of the user
        
    Exceptions:
        InputError - when the u_id is invalid
        InputError - when permission_id is invalid, not either 1 or 2
        InputError - when the target user is the only owner
        AccessError - when the token doesn't have owner permissions
        
    Return Value:
        Returns an empty dictionary
    '''
    data = get_data()
    if data['users'][check_token(token)]['permission_id'] != OWNER:
        raise AccessError(description='The authorised user is not an owner')
    user_index = check_u_id(u_id)
    if data['users'][user_index]['permission_id'] == OWNER and only_one_owner():
        raise InputError(description='The user is currently the only owner')
    if permission_id not in [OWNER, MEMBER]:
        raise InputError(description='permission_id does not refer to a value permission')
        
    data['users'][user_index]['permission_id'] = permission_id
    write_data(data)
    return {}
    
