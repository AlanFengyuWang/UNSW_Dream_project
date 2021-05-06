'''
Authors:
    Alec Dudley-Bestow, z5260201

Date:
    26 March 2021
'''

import json
import re
from src.error import AccessError, InputError
from src.auth import check_token, check_u_id, get_data, write_data, \
    valid_email, valid_name, email_taken, handle_taken, get_data
from src.helper import valid_handle, get_user_dictionary_for_user_profile, get_user_dictionary
import urllib.request
from PIL import Image
import random 
import os
from src.config import url

image_number = 0

def user_profile(token, u_id):
    '''
        returns a dictionary of information on a given user

    Arguments:
        token (jwt)    - authorization token
        u_id (integer)    - specifies the target user

    Exceptions:
        InputError  - Occurs when the given u_id is invalid
        AccessError - Occurs when the token given is invalid

    Return Value:
        Returns user dictionary
    '''
    check_token(token)
    user_index = check_u_id(u_id, True)
    data = get_data()  
    return {'user' : get_user_dictionary_for_user_profile(data['users'][user_index])}

def users_all(token):
    '''
        returns a list of dictionaries of information on all users

    Arguments:
        token (jwt)    - authorization token

    Exceptions:
        AccessError - Occurs when the token given is invalid

    Return Value:
        Returns a list of user dictionaries
    '''
    check_token(token)
    user_list = []
    data = get_data()
    for user in data['users']:
        user_list.append({
            'u_id': user['u_id'],
            'email': user['email'],
            'name_first': user['name_first'],
            'name_last': user['name_last'],
            'handle_str': user['handle_str'],
            'profile_img_url': user['profile_img_url']
        })
    return {'users' : user_list}

def user_profile_setname(token, name_first, name_last):
    '''
        changes a users name in the database

    Arguments:
        token (jwt)    - authorization token
        name_first (string)    - the new first name
        name_last (string)    - the new last name

    Exceptions:
        InputError  - Occurs when either name isn't between 1 and 50 characters
        AccessError - Occurs when the token given is invalid

    Return Value:
        Returns empty dictionary
    '''
    user_index = check_token(token)
    if not valid_name(name_first):
        raise InputError(description=\
            'name_first is not between 1 and 50 characters inclusively in length')
    elif not valid_name(name_last):
        raise InputError(description=\
            'name_last is not between 1 and 50 characters inclusively in length')
    else:
        data = get_data()
        data['users'][user_index]['name_first'] = name_first
        data['users'][user_index]['name_last'] = name_last
        write_data(data)
        
    return {}

def user_profile_setemail(token, email):
    '''
        changes a users email address in the database

    Arguments:
        token (jwt)    - authorization token
        email (string)    - the new email address

    Exceptions:
        InputError  - Occurs when the given email address is of invalid format
        InputError  - Occurs when the given email address is already taken
        AccessError - Occurs when the token given is invalid

    Return Value:
        Returns empty dictionary
    '''
    user_index = check_token(token)
    if not valid_email(email):
        raise InputError(description=\
            'Email entered is not a valid email')
    elif email_taken(email):
        raise InputError(description=\
            'Email address is already being used by another user')
    else:
        data = get_data()
        data['users'][user_index]['email'] = email
        write_data(data)
        
    return {}

def user_profile_sethandle(token, handle_str):
    '''
        changes the user handle of a person in the database

    Arguments:
        token (jwt)    - authorization token
        name_first (string)    - the new first name
        
    Exceptions:
        InputError  - Occurs when the new handle contains an 
                      @ symbol or isn't between 3 and 20 characters
        InputError  - Occurs when the given handle is already taken
        AccessError - Occurs when the token given is invalid

    Return Value:
        Returns empty dictionary
    '''
    user_index = check_token(token)
    if not valid_handle(handle_str):
        raise InputError(description=\
            'Handle is not valid')
    elif handle_taken(handle_str):
        raise InputError(description=\
            'Handle is already used by another user')
    else:
        data = get_data()
        data['users'][user_index]['handle_str'] = handle_str
        write_data(data)
        
    return {}

def user_profile_uploadphoto(token, img_url, x_start, y_start, x_end, y_end):
    '''
    This function allows the user to crops image
    Arguments:
        token(str)
        img_url(str)
        x_start(int)
        y_start(int)
        x_end(int)
        y_end(int)
    Returns:
        None
    '''
    #img_url returns an HTTP status other than 200.
    if urllib.request.urlopen(img_url).getcode() != 200:
        raise InputError(description='img_url returns an HTTP status other than 200')
    if img_url[-3:] != 'jpg':
        raise InputError(description='Image uploaded is not a JPG')

    #getting the u_id and save their image based on their u_id
    user_index = check_token(token)
    data = get_data()
    u_id = data['users'][user_index]['u_id']

    global image_number
    #Download the pic to the local file called "static"
    profile_img_url = f"src/static/image{u_id}-{image_number}.jpg"
    urllib.request.urlretrieve(img_url, profile_img_url)

    #open the image
    imageObject = Image.open(profile_img_url)

    #Get the size
    width, height = imageObject.size
    if x_start > width or y_start > height or x_end > width or y_end > width:
        #delelte the file
        os.remove(profile_img_url)
        raise InputError(description='any of x_start, y_start, x_end, y_end are not within the dimension of the image at the URL')

    cropped = imageObject.crop((x_start, y_start, x_end, y_end))
    cropped.save(profile_img_url)
    
    #update the users' info related to the profile_img_url
    data['users'][user_index]['profile_img_url'] = f"{url}/static/image{u_id}-{image_number}.jpg"
    
    image_number += 1
    write_data(data)
    return {}

    
def get_last_stat(key, user):
    return user[key][-1]['num_' + key]

def user_stats(token):
    '''
    returns a user's activity in channels, dms and messages

Arguments:
    token (string) - A jwt token for authorizing a user

Exceptions:
    AccessError - Occurs when the jwt token is not authorized

Return Value:
    Returns a dictionary containing a users activity information
    '''
    data = get_data()
    user = data['users'][check_token(token)]
    inv_rate = 0

    try:
        inv_rate = ((get_last_stat('dms_joined', user) + 
        get_last_stat('channels_joined', user) + 
        get_last_stat('messages_sent', user)) /
        (len(data['channels']) + get_last_stat('messages_exist', data)))

    except ZeroDivisionError:
        pass
    stats = {
        'channels_joined' : user['channels_joined'],
        'dms_joined' : user['dms_joined'],
        'messages_sent' : user['messages_sent'],
        'involvement_rate' : inv_rate
    }
    return {'user_stats' : stats}

def users_stats(token):
    '''
    returns the activity of all dreams channels, dms and messages

Arguments:
    token (string) - A jwt token for authorizing a user

Exceptions:
    AccessError - Occurs when the jwt token is not authorized

Return Value:
    Returns a dictionary containing all of dreams activities
    '''
    check_token(token)
    data = get_data()

    num_active_users = 0
    for user in data['users']:
        if get_last_stat('channels_joined', user) >= 1 or get_last_stat('dms_joined', user) >= 1:
            num_active_users += 1
    stats = {
        'channels_exist' : data['channels_exist'],
        'dms_exist' : data['dms_exist'],
        'messages_exist' : data['messages_exist'],
        'utilization_rate' : num_active_users / len(data['users'])
    }
    return {'dreams_stats' : stats}
