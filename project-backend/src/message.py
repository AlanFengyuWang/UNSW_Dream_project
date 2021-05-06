'''
Authors:    
    Justin Wu, z5316037
    William Zheng, z5313015
    Alec Dudley-Bestow, z5260201
Date:       

   25 March 2021
'''

from src.error import InputError, AccessError
from src.auth import auth_register, check_token, get_data, write_data, check_u_id
from src.channels import channels_create
from src.channel import channel_id_valid, member_check, get_channel_index, user_is_owner_token, user_is_member, user_is_owner_uid, check_channel_id, check_is_member, update_user
from datetime import datetime, timezone
from src.other import insert_tag_notification
import threading
import time
from src.helper import message_id_exists, message_id_generate, message_is_sender, message_too_long, \
search_message_id, owner_check, already_reacted, edit_react

import jwt

SECRET = 'atotallysecuresecret'
message_id_queue = [] #The reason to have this global variable is for the message_sendlater which requires
#threading.Timer that can't return the variable from message_send


def update_message_stats(func):
    def wrap(*args, **kw):
        resp = func(*args, **kw)
        msgs_exist = 0
        data = get_data()
        for channel in data['channels']:
            msgs_exist += len(channel['messages'])
        data = update_user('messages_exist', msgs_exist, data)
        write_data(data)
        return resp
    return wrap

@update_message_stats
def message_send(token, channel_id, message, **kw):
    '''
        Send a message from authorised_user to the channel specified by channel_id. 
        Note: Each message should have it's own unique ID. 
        I.E. No messages should share an ID with another message, 
        even if that other message is in a different channel.
    Arguments:
        token (string) - JWT token encrypted with user's u_id and session_id.
        channel_id (int) - Id of inputted channel.
        message (string) - User's message to the specified channel.

    Exceptions:
        InputError - Message is more than 1000 characters.
        AccessError - When the authorised user has not joined the channel they are trying to post to.

    Return Value:
        Dictionary containing 'message_id'.
    ''' 
    user_index = check_token(token)

    data = get_data()
    if not channel_id_valid(channel_id, data['channels']):
        raise InputError(description="Invalid channel id!")
    
    message_too_long(message)
    
    # Decode token to get u_id
    token_structure = jwt.decode(token, SECRET, algorithms=['HS256'])
    u_id = token_structure['u_id']
    if not member_check(u_id, channel_id, data['channels']):
        raise AccessError(description="User is not a member of the channel!")

    # Generate unique id for message
    message_id = message_id_generate()

    # Go to the channel and append the message and message_id
    channel_index = get_channel_index(channel_id)
    
    time = int(datetime.now().timestamp())
    data['channels'][channel_index]['messages'].append({
        'message_id': message_id,
        'u_id': u_id,
        'message': message,
        'time_created': time,
        'is_pinned': False,
        'reacts': [{
            'react_id': 1,
            'u_ids': [],
            'is_this_user_reacted': False
        }]
    })

    user = data['users'][user_index]
    num_messages = user['messages_sent'][-1]['num_messages_sent']
    
    data['users'][user_index]['messages_sent'].append({
        'num_messages_sent' : num_messages + 1,
        'time_stamp' : datetime.now().timestamp()
    })
    write_data(data)
    insert_tag_notification(token, channel_id, message)
    #get the message_id for sendlater
    global message_id_queue
    message_id_queue.append(message_id) #For message_sendlater threading.Timer
    return {
        'message_id': message_id,
    }

@update_message_stats
def message_remove(token, message_id):
    ''' 
    Given a message_id for a message, this message is removed from the channel/DM
    
    Parameters:
        token - Token for authorised user
        message_id - message id for message being removed

    Exceptions:
        InputError - Message (based on ID) no longer exists.
        AccessError - Message with message_id was sent by the authorised user 
            making this request.
        AccessError - The authorised user is an owner of this channel (if it was sent 
            to a channel) or the **Dreams**.

    Returns:
        None
    '''
    data = get_data()
    user_index = check_token(token)

    # Message doesnt exist
    message, channel = message_id_exists(message_id)
    if message == None:
        raise InputError(description="Invalid message id!")

    # Message not sent by authorised user
    if message_is_sender(data['users'][user_index]['u_id'], message) == False:
        raise AccessError(description="Message with message_id was NOT sent by the authorised user making this request!")

    # Auth user is not owner of channel or dreams
    # NOTE Function is imported from channel so not on this branch
    if user_is_owner_token(token, channel['channel_id']) == False:
        raise AccessError(description="The authorised user is an owner of this channel (if it was sent to a channel) or the **Dreams**!")

    for ch in data['channels']:
        if ch['channel_id'] == channel['channel_id']:
            ch['messages'].remove(message)

    write_data(data)
    return {}

def message_edit(token, message_id, message):
    '''
    Given a message, update its text with new text. 
    If the new message is an empty string, the message is deleted.

    Arguments:
        token (string) - JWT token encrypted with user's u_id and session_id.
        message_id (int) - Id of message to be edited.
        message (string) - Autherised user's message to the specified channel.

    Exceptions:
        InputError - Length of new message is over 1000 characters.
        InputError - Message_id refers to a deleted message.
        AccessError - Different user is trying to edit another user's message.
        AccessError - The user trying to edit their message is not an owner of the channel/dm.
    
    Return:
        None
    '''
    data = get_data()

    # InputError - Length of new message is over 1000 characters.
    message_too_long(message)

    check_token(token)
    token_structure = jwt.decode(token, SECRET, algorithms=['HS256'])
    auth_user_id = token_structure['u_id']

    # InputError - Message_id refers to a deleted message.
    channel_id, msg_index = search_message_id(message_id)
    channel_index = get_channel_index(channel_id)
    check_u_id(auth_user_id)

    # AccessError - The user trying to edit their message is not an owner of the channel/dm.
    owner_check(data['channels'][channel_index]['owner_members'], auth_user_id)

    # AccessError - Different user is trying to edit another user's message.
    u_id = data['channels'][channel_index]['messages'][msg_index]['u_id']
    if auth_user_id != u_id:
        raise AccessError(description="User trying to edit the message is not the auth user who made the message!")

    # If given empty string
    if len(message) == 0:
        message_remove(token, message_id)
    
    # Otherwise edit the old message.
    data['channels'][channel_index]['messages'][msg_index]['message'] = message
    
    write_data(data)
    return {
    }


def message_senddm(token, dm_id, message, **kw):
    '''
    Send a message from authorised_user to the DM specified by dm_id. Note: Each message should 
    have it's own unique ID. I.E. No messages should share an ID with another message, even if 
    that other message is in a different channel or DM.

    Arguments:
        token (string) - JWT token encrypted with user's u_id and session_id.
        dm_id (int) - Id of inputted dm.
        message (string) - User's message to the specified channel.
    
    Exceptions:
        InputError - Length of new message is over 1000 characters.
        AccessError - When the authorised user is not a member of the DM they are trying to post to.
    
    Return Value:
        Dictionary containing 'message_id'.
    '''
    dm_msg_id = message_send(token, dm_id, message)['message_id']

    return {
        'message_id': dm_msg_id
    }

def message_share(token, og_message_id, message, channel_id, dm_id):
    '''
    Given a message_id, auth_user will share this messageto a channel or dm. 
    If an optional message is given, it is added in addition to the originally shared message.

    Arguments:
        token (string) - JWT token encrypted with user's u_id and session_id.
        og_message_id (int) - Id of the original message. 
        message(string) - Message is the optional message in addition to the shared message, and will be an empty string '' if no message is given
        channel_id (int) - Channel Id that the message is being shared to, and is -1 if it is being sent to a DM.
        dm_id (int) - Dm Id that the message is being shared to, and is -1 if it is being sent to a channel.
    
    Exceptions:
        AccessError - When the authorised user has not joined the channel or DM they are trying to share the message to.
    
    Returns:
        Dicitonaring containing a shared_message_id
    '''
    data = get_data()

    check_token(token)

    token_structure = jwt.decode(token, SECRET, algorithms=['HS256'])
    u_id = token_structure['u_id']

    # First fetch the actual og message from og_msg_id.
    og_channel_id, og_msg_index = search_message_id(og_message_id)
    og_channel_index = get_channel_index(og_channel_id)

    # Get a copy of the message.
    og_message = data['channels'][og_channel_index]['messages'][og_msg_index]['message']

    # Shared message combines the og_message and an optional message.
    shared_msg = og_message + ", " + message

    # Sending to dm.
    if channel_id == -1:
        if not member_check(u_id, dm_id, data['channels']):
            raise AccessError(description="User is not a member of the dm!")
        shared_message_id = message_senddm(token, dm_id, shared_msg)['message_id']

    # Sending to channel
    if dm_id == -1:
        if not member_check(u_id, channel_id, data['channels']):
            raise AccessError(description="User is not a member of the channel!")
        shared_message_id = message_send(token, channel_id, shared_msg)['message_id']

    return {
        'shared_message_id': shared_message_id,
    }

def message_sendlater(token, channel_id, message, time_sent, **kw):
    '''
    This function allows users to send the message only after specify a time
    Arguments:
        token(string)
        channel_id(int)
        message(string)
        time_sent(timestamp) - the specific time that the message will be sent
    Returns:
        message_id(id)
    '''
    #Inputerror: channel ID is not a valid channel
    check_channel_id(channel_id)
    #Inputerror: Message is more than 1000
    if len(message) > 1000:
        raise InputError(description="Message is more than 1000")
    #Inputerror: Time sent is a time in the past
    # timestamp_now = datetime.now().replace(tzinfo=timezone.utc).timestamp()
    timestamp_now = datetime.now().timestamp()
    # print(f"time_sent = {time_sent}")
    # print(f"timestamp_now = {timestamp_now}")
    if time_sent < timestamp_now:
        raise InputError(description="Time sent is a time in the past")
    
    #AccessError: when the authorised user has not joined the channel they are trying to post to
    data = get_data()
    check_is_member(data['users'][check_token(token)]['u_id'], data['channels'][check_channel_id(channel_id)]['all_members'])

    #send the user after the time_sent
    # print()
    time_count = time_sent - timestamp_now
    # t = threading.Timer(time_count, message_send, [token, channel_id, message])
    # .start()
    time.sleep(time_count)
    message_id = message_send(token, channel_id, message)
    # message_id = message_id_queue.pop()
    return {
        'message_id': message_id
    }

def message_sendlaterdm(token, dm_id, message, time_sent, **kw):
    # print(f'token = {token}, dm_id = {dm_id}, message = {message}')
    return message_sendlater(token, dm_id, message, time_sent)['message_id']

def message_pin(token, message_id):
    '''
    Given a message within a channel or DM, mark it as "pinned" to be given 
    special display treatment by the frontend.

    Paramaters:
        token - token of authorised user
        message_id - message id for the message being pinned
    
    Exceptions:
        InputError - message_id is not a valid message.
        InputError - Message with ID message_id is already pinned.
        AccessError - The authorised user is not a member of the channel or DM 
            that the message is within.
        AccessError - The authorised user is not an owner of the channel or DM.

    Returns:
        None
    '''
    data = get_data()
    user_index = check_token(token)

    message, channel = message_id_exists(message_id)
    if message == None:
        raise InputError

    if message['is_pinned'] == True:
        raise InputError

    if user_is_member(data['users'][user_index]['u_id'], channel) == False:
        raise AccessError
    
    if user_is_owner_uid(data['users'][user_index]['u_id'], channel['channel_id']) == False:
        raise AccessError

    for ch in data['channels']:
        if ch['channel_id'] == channel['channel_id']:
            for msg in ch['messages']:
                if msg['message_id'] == message['message_id']:
                    msg['is_pinned'] = True

    write_data(data)
    return {}

def message_unpin(token, message_id):
    '''
    Given a message within a channel or DM, remove it's mark as unpinned.
    
    Paramaters:
        token - Token of authorised user
        message_id - Message id for the message being unpinned
    
    Exceptions:
        InputError - message_id is not a valid message.
        InputError - Message with ID message_id is already unpinned.
        AccessError - The authorised user is not a member of the channel or DM 
            that the message is within.
        AccessError - The authorised user is not an owner of the channel or DM.

    Returns:
        None
    '''
    data = get_data()
    user_index = check_token(token)

    message, channel = message_id_exists(message_id)
    if message == None:
        raise InputError

    if message['is_pinned'] == False:
        raise InputError

    if user_is_member(data['users'][user_index]['u_id'], channel) == False:
        raise AccessError
    
    if user_is_owner_uid(data['users'][user_index]['u_id'], channel['channel_id']) == False:
        raise AccessError

    for ch in data['channels']:
        if ch['channel_id'] == channel['channel_id']:
            for msg in ch['messages']:
                if msg['message_id'] == message['message_id']:
                    msg['is_pinned'] = False

    write_data(data)
    return {}


def message_react(token, message_id, react_id):
    '''
    Given a message within a channel or DM the authorised user is part of, 
    add a "react" to that particular message.

    Parameters:
        token - Token for authorised user
        message_id - Message id of message being reacted
        react_id - Id for the specific react type
    
    Exceptions:
        InputError - message_id is not a valid message within a channel or 
            DM that the authorised user has joined.
        InputError - react_id is not a valid React ID. The only valid react 
            ID the frontend has is 1.
        InputError - Message with ID message_id already contains an active 
            React with ID react_id from the authorised user.
        AccessError - The authorised user is not a member of the channel or 
            DM that the message is within.
    
    Returns:
        None
    '''
    data = get_data()
    user_index = check_token(token)
    
    message, channel = message_id_exists(message_id)
    if message == None:
        raise InputError
    
    if react_id != 1:
        raise InputError

    if already_reacted(react_id, message) == True:
        raise InputError
    
    if user_is_member(data['users'][user_index]['u_id'], channel) == False:
        raise AccessError

    for ch in data['channels']:
        if ch['channel_id'] == channel['channel_id']:
            for msg in ch['messages']:
                if msg['message_id'] == message['message_id']:
                    edit_react(msg, react_id, data['users'][user_index]['u_id'], 'append')

    write_data(data)
    return {}


def message_unreact(token, message_id, react_id):
    '''
    Given a message within a channel or DM the authorised user is part of, 
    remove a "react" to that particular message
    
    Parameters:
        token - Token for authorised user
        message_id - Message id of message being unreacted
        react_id - Id for the specific react type
    
    Exceptions:
        InputError - message_id is not a valid message within a channel or 
            DM that the authorised user has joined.
        InputError - react_id is not a valid React ID. The only valid react 
            ID the frontend has is 1.
        InputError - Message with ID message_id does not contain an active 
            React with ID react_id from the authorised user.
        AccessError - The authorised user is not a member of the channel or 
            DM that the message is within.
    
    Returns:
        None
    '''
    data = get_data()
    user_index = check_token(token)
    
    message, channel = message_id_exists(message_id)
    if message == None:
        raise InputError

    if react_id != 1:
        raise InputError

    if already_reacted(react_id, message) == False:
        raise InputError
    
    if user_is_member(data['users'][user_index]['u_id'], channel) == False:
        raise AccessError

    for ch in data['channels']:
        if ch['channel_id'] == channel['channel_id']:
            for msg in ch['messages']:
                if msg['message_id'] == message['message_id']:
                    edit_react(msg, react_id, data['users'][user_index]['u_id'], 'remove')

    write_data(data)
    return {}

