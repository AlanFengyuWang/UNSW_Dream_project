'''
Authors:
    Justin Wu, z5316037

Date:
    12 April 2021
'''

import time

from src.auth import check_token, get_data, write_data, check_u_id, check_token
from src.error import InputError, AccessError
from src.helper import check_channel_id, user_is_member, get_user_dictionary
from src.message import message_send
from threading import Timer

def standup_start(token, channel_id, length):
    '''
    For a given channel, start the standup period whereby for the next "length" seconds 
    if someone calls "standup_send" with a message, it is buffered during the X second 
    window then at the end of the X second window a message will be added to the message 
    queue in the channel from the user who started the standup. X is an integer that 
    denotes the number of seconds that the standup occurs for

    Arguments:
        token (string) - JWT token encrypted with user's u_id and session_id.
        channel_id (int) - Id of inputted channel.
        length (int) - Standup duration in seconds.

    Exceptions:
        InputError - Channel ID is not a valid channel.
        InputError - An active standup is currently running in this channel.
        AccessError - Authorised user is not in the channel.

    Return Value:
        Dictionary containing 'time_finish'.
    '''
    data = get_data()

    user_index = check_token(token)
    user_id = data['users'][user_index]['u_id']
    channel_index = check_channel_id(channel_id)

    # Raise InputError if an active standup is already occurring.
    if data['channels'][channel_index]['standup']['time_finish'] != None:
        if int(time.time()) < data['channels'][channel_index]['standup']['time_finish']:
            raise InputError(description="Active standup already occurring!")
    
    # Raise AccessError is user is not part of the channel.
    if not user_is_member(user_id, data['channels'][channel_index]):
        raise AccessError(description="Auth user is not a member of this channel!")   

    # Starting the standup
    end_time = int(time.time()) + length
    data['channels'][channel_index]['standup'] = {
        'is_active': True,
        'time_finish': end_time,
        'u_id': user_id,
        'queued_messages': []
    }

    write_data(data)

    # Reset the StandUp Dict after 'length' seconds.
    Timer(length, standUp_reset, args=(token, channel_id)).start()

    return {
        'time_finish': data['channels'][channel_index]['standup']['time_finish']
    }

def standup_active(token, channel_id):
    '''
    For a given channel, return whether a standup is active in it, and what time 
    the standup finishes. If no standup is active, then time_finish returns None.

    Arguments:
        token (string) - JWT token encrypted with user's u_id and session_id.
        channel_id (int) - Id of inputted channel.

    Exceptions:
        InputError - Channel ID is not a valid channel.

    Return Value:
        Dictionary containing 'is_active' & 'time_finish'.
    '''
    data = get_data()

    channel_index = check_channel_id(channel_id)

    is_active = data['channels'][channel_index]['standup']['is_active']
    time_finish = data['channels'][channel_index]['standup']['time_finish']
    
    return {
        'is_active': is_active,
        'time_finish': time_finish
    }

def standup_send(token, channel_id, message):
    '''
    Sending a message to get buffered in the standup queue, 
    assuming a standup is currently active.

    Arguments:
        token (string) - JWT token encrypted with user's u_id and session_id.
        channel_id (int) - Id of inputted channel.
        message (string) - Message to be buffered in the standup queue.

    Exceptions:
        InputError - Channel ID is not a valid channel.
        InputError - Message is more than 1000 characters (not including the username and colon).
        InputError - An active standup is not currently running in this channel.
        AccessError - The authorised user is not a member of the channel that the message is within

    Return Value:
        None
    '''
    data = get_data()
    
    user_index = check_token(token)
    user_id = data['users'][user_index]['u_id']
    channel_index = check_channel_id(channel_id)

    # Raise InputError when message is over 1000 characters.
    if len(message) > 1000:
        raise InputError(description="Message is over 1000 characters!")

    # Raise InputError when an active standup is not occurring in the channel.
    if not standup_active(token, channel_id)['is_active']:
        raise InputError(description="There is no standup occurring in this channel!")

    # Raise AccessError is user is not part of the channel.
    if not user_is_member(user_id, data['channels'][channel_index]):
        raise AccessError(description="Auth user is not a member of this channel!") 
    
    username = get_user_dictionary(data['users'][user_index])['handle_str']
    formatted_msg = username + ": " + message
    data['channels'][channel_index]['standup']['queued_messages'].append(formatted_msg)

    write_data(data)

    return {
    }

def standUp_reset(token, channel_id):
    '''
    Resets the StandUp dict after 'length' seconds have passed since
    the starting of a StandUp. Also directs all queued messages from 
    the stand up into the channel.
    '''
    
    channel_index = check_channel_id(channel_id)
    # Takes buffered messages and inserts them into channel "messages"
    unqueue_messages(token, channel_id, channel_index)

    # Reset StandUp Items after 'length' seconds.
    standUp_clear(channel_index)

def unqueue_messages(token, channel_id, channel_index):
    '''
    Sends queued messages from standup into the actual messages list in channel.
    '''
    data = get_data()

    standup_message = '\n'.join(data['channels'][channel_index]['standup']['queued_messages'])
    message_send(token, channel_id, standup_message)

def standUp_clear(channel_index):
    '''
    Clears standup dict after length seconds.
    '''
    data = get_data()

    data['channels'][channel_index]['standup'] = {
        'is_active': False,
        'time_finish': None,
        'u_id': None,
        'queued_messages': []
    }

    write_data(data)
