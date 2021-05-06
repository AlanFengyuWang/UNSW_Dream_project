'''
Authors: 
    Alec Dudley-Bestow, z5260201
    
Date: 
    20 March 2021
'''

import datetime
import pytest
from src.dm import dm_create
from src.auth import auth_register, get_data
from src.user import user_profile, user_profile_setname, \
    user_profile_setemail, user_profile_sethandle, users_all, user_profile_uploadphoto,\
    user_stats, users_stats
from src.other import clear
from tests.auth_test import invalid_input, invalid_emails
from src.error import InputError, AccessError
from src.channels import channels_create
from src.channel import channel_invite
from src.message import message_send

@pytest.fixture
def users():
    clear()
    user1 = auth_register("email@email.com", "password", "firstname", "lastname")
    user2 = auth_register("email1@email.com", "password", "firstname", "lastname")
    user3 = auth_register("email2@email.com", "password", 'firstname', 'lastname')
    return {'user1' : user1, 'user2' : user2, 'user3' : user3}

@pytest.fixture
def channels(users):
    channel1 = channels_create(users['user1']['token'], 'channelname0', True)
    channel2 = channels_create(users['user1']['token'], 'channelname1', False)
    channel3 = channels_create(users['user3']['token'], 'channelname2', False)
    channel_invite(users['user3']['token'], channel3['channel_id'], users['user1']['auth_user_id'])
    message_send(users['user1']['token'], channel1['channel_id'], 'thisisamessage')
    message_send(users['user1']['token'], channel2['channel_id'], 'alsomessage')

    message_send(users['user3']['token'], channel3['channel_id'], 'alsomessage')
    return {'channel1' : channel1, 'channel2' : channel2, 'channel3' : channel3}

@pytest.fixture
def profiles(users):
    profile1 = {'email' : 'email@email.com',
        'u_id' : users['user1']['auth_user_id'],
        'name_first' : 'firstname',
        'name_last' : 'lastname',
        'handle_str' : 'firstnamelastname'
    }
    
    profile2 = {'email' : 'email1@email.com',
        'u_id' : users['user2']['auth_user_id'],
        'name_first' : 'firstname',
        'name_last' : 'lastname',
        'handle_str' : 'firstnamelastname0'
    }
    return {'profile1' : profile1, 'profile2' : profile2}  

@pytest.fixture
def invalid_user(users):
    clear()
    return {'invalid' : users['user2'], \
        'valid' : auth_register("email@email.com", "password", "firstname", "lastname")}

def member_info(user_profile):
    return {
        'u_id': user_profile['u_id'],
        'email': user_profile['email'],
        'name_first': user_profile['name_first'],
        'name_last': user_profile['name_last'],
        'handle_str': user_profile['handle_str'],
    }

def user_allmember_info(users_all):
    return {
        'u_id': users_all['u_id'],
        'email': users_all['email'],
        'name_first': users_all['name_first'],
        'name_last': users_all['name_last'],
        'handle_str': users_all['handle_str'],
    }

def check_profile(profile, user):
    assert member_info(user_profile(user['token'], user['auth_user_id'])['user']) == profile

#INVALID TOKEN TESTS:
def test_invalid_users_all(invalid_user):
    with pytest.raises(AccessError):
        users_all(invalid_user['invalid']['token'])

def test_invalid_user_setname(invalid_user):
    with pytest.raises(AccessError):
        user_profile_setname(invalid_user['invalid']['token'], "newfirstname", "newlastname")

def test_invalid_user_sethandle(invalid_user):
    with pytest.raises(AccessError):
        user_profile_sethandle(invalid_user['invalid']['token'], "newhandle")
        
def test_invalid_user_setemail(invalid_user):
    with pytest.raises(AccessError):
        user_profile_setemail(invalid_user['invalid']['token'], "email2@email.com")

def test_invalid_user_profile(invalid_user):
    with pytest.raises(AccessError):
        user_profile(invalid_user['invalid']['token'], invalid_user['valid']['auth_user_id'])

#USERS_ALL TESTS:
def test_users_all(users, profiles):
    user_list = users_all(users['user1']['token'])['users']
    assert profiles['profile1'] in [user_allmember_info(user_list[0]), user_allmember_info(user_list[1]), user_allmember_info(user_list[2])]
    assert profiles['profile2'] in [user_allmember_info(user_list[0]), user_allmember_info(user_list[1]), user_allmember_info(user_list[2])]

#USER_PROFILE TESTS:
#test that user can view others profiles
def test_user_profile(users, profiles):
    assert member_info(user_profile(users['user1']['token'], users['user2']['auth_user_id'])['user'])\
        == profiles['profile2']
    assert member_info(user_profile(users['user2']['token'], users['user1']['auth_user_id'])['user'])\
        == profiles['profile1']

#test that user can view their own profile
def test_user_profile_request_self(users, profiles):
    check_profile(profiles['profile2'], users['user2'])
    check_profile(profiles['profile1'], users['user1'])
    
def test_profile_InputError(invalid_user):
    with pytest.raises(InputError):
        user_profile(invalid_user['valid']['token'], invalid_user['invalid']['auth_user_id'])

#USER_PROFILE_SETNAME TESTS:
#test that function throws an error for empty names
def test_setname_small_names(users):
    with pytest.raises(InputError):
        user_profile_setname(users['user1']['token'], "", "lastname")
    with pytest.raises(InputError):
        user_profile_setname(users['user2']['token'], "firsname", "")

#test that function throws an error for too big names        
def test_setname_large_names(users):
    with pytest.raises(InputError):
        user_profile_setname(users['user1']['token'], "x" * 51, "lastname")
    with pytest.raises(InputError):
        user_profile_setname(users['user2']['token'], "firstname", "x" * 51)
  
#tests that function changes name for second user and not first
def test_profile_setname_user(users, profiles):
    user_profile_setname(users['user2']['token'], "newfirstname", "newlastname")
    profiles['profile2']['name_first'] = "newfirstname"
    profiles['profile2']['name_last'] = 'newlastname'
    
    check_profile(profiles['profile1'], users['user1'])
    check_profile(profiles['profile2'], users['user2'])

#test that user can change their name back to original
def test_set_name_back(users, profiles):
    user_profile_setname(users['user1']['token'], 'new', 'new')
    user_profile_setname(users['user1']['token'], \
        profiles['profile1']['name_first'], profiles['profile1']['name_last'])
    
    check_profile(profiles['profile1'], users['user1'])
    
    user_profile_setname(users['user2']['token'], 'new', 'new')
    user_profile_setname(users['user2']['token'],\
        profiles['profile2']['name_first'], profiles['profile2']['name_last'])
        
    check_profile(profiles['profile2'], users['user2']) 
    
#USER_PROFILE_SETEMAIL TESTS:

#tests that function changes name for second user and not first
def test_set_email_user(users, profiles):
    
    user_profile_setemail(users['user2']['token'], "anothernewemail@email.com")
    profiles['profile2']['email'] = "anothernewemail@email.com"
    print(get_data())
    check_profile(profiles['profile1'], users['user1'])
    check_profile(profiles['profile2'], users['user2'])

#test that user can change their email back to original
def test_set_email_back(users, profiles):
    
    user_profile_setemail(users['user1']['token'], "newemail@email.com")
    user_profile_setemail(users['user1']['token'], profiles['profile1']['email'])
    check_profile(profiles['profile1'], users['user1'])

    user_profile_setemail(users['user2']['token'], "newemail@email.com")
    user_profile_setemail(users['user2']['token'], profiles['profile2']['email'])
    check_profile(profiles['profile2'], users['user2'])      
    
#test for two different users with incorrect email format
def test_set_email_InputError(users, invalid_emails):
    
    invalid_input(user_profile_setemail, {'token' : users['user1']['token'], \
        'email' : 'email@email.com'}, 'email', invalid_emails)

#test user cannot set email to an email that already exists
def test_set_preexisting_email(users, profiles):
    
    with pytest.raises(InputError):
        user_profile_setemail(users['user1']['token'], profiles['profile1']['email'])
    with pytest.raises(InputError):
        user_profile_setemail(users['user2']['token'], profiles['profile2']['email'])

#test user cannot set email to a changed email
def test_set_preexisting_email_after_change(users, profiles):
    
    user_profile_setemail(users['user1']['token'], "newemail@email.com")
    user_profile_setemail(users['user2']['token'], "anothernewemail@email.com")
    
    with pytest.raises(InputError):
        user_profile_setemail(users['user1']['token'], "newemail@email.com")
    with pytest.raises(InputError):
        user_profile_setemail(users['user2']['token'], "newemail@email.com")
        
    with pytest.raises(InputError):
        user_profile_setemail(users['user1']['token'], "anothernewemail@email.com")
    with pytest.raises(InputError):
        user_profile_setemail(users['user2']['token'], "anothernewemail@email.com")

#USER_PROFILE_SETHANDLE TESTS:
def test_set_handle(users, profiles):
    user_profile_sethandle(users['user1']['token'], 'newhandle')
    profiles['profile1']['handle_str'] = 'newhandle'
    check_profile(profiles['profile1'], users['user1'])

def test_set_handle_error(users):
    with pytest.raises(InputError):
        user_profile_sethandle(users['user1']['token'], 'x'*21)
    with pytest.raises(InputError):
        user_profile_sethandle(users['user1']['token'], '12')

def test_set_handle_taken(users, profiles):
    with pytest.raises(InputError):
        user_profile_sethandle(users['user1']['token'], profiles['profile1']['handle_str'])

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for uploadPhoto ----------------------------------- #
# --------------------------------------------------------------------------------------- #
def test_uploadphoto_inputError(users):
    #get token
    user_profile_uploadphoto(users['user1']['token'], "https://images.all-free-download.com/images/graphicthumb/default_profile_picture_117087.jpg", 1,1,200,200)
    #try to access the image, this requires manually check the src/static file
    user_profile_uploadphoto(users['user2']['token'], "https://images.all-free-download.com/images/graphicthumb/default_profile_picture_117087.jpg", 1,1,200,200)
    # result = user_profile(users['user1']['token'], users['user1']['auth_user_id'])
    # result2 = user_profile(users['user2']['token'], users['user2']['auth_user_id'])
#     #check the input error, x_start/end, y_start/end are not within the dimensions of the image at the URL
    with pytest.raises(InputError):
        user_profile_uploadphoto(users['user2']['token'], "http://site.meishij.net/r/58/25/3568808/a3568808_142682562777944.jpg", 1,1,5000,5000)
    with pytest.raises(InputError):
        user_profile_uploadphoto(users['user3']['token'], "http://site.meishij.net/r/58/25/3568808/a3568808_142682562777944.jpg", 5000,5000,50,50)
    
    #Check img_url returns an HTTP status other than 200
    # with pytest.raises(InputError):
    #     user_profile_uploadphoto('1', "http://site.invalid.jpg", 5000,5000,50,50)
    
    # Check the image uploaded is not a JPG
    with pytest.raises(InputError):
        user_profile_uploadphoto(users['user3']['token'], "https://s29843.pcdn.co/blog/wp-content/uploads/sites/2/2020/11/TechSmith-Blog-JPGvsPNG.png", 1,1,50,50)

#USER_STATS_TESTS:
def test_no_involvement(users):
    resp = user_stats(users['user1']['token'])['user_stats']
    assert resp['involvement_rate'] == 0

def check_timestamp(time1, time2):
    TOLERANCE = 500
    assert time1 - TOLERANCE < time2 < time1 + TOLERANCE

def test_stats_with_channels(users):
    timestamp = datetime.datetime.now().timestamp()
    token = users['user1']['token']
    channels_create(token, 'name', True)['channel_id']
    resp = user_stats(token)['user_stats']
    assert resp['channels_joined'][-1]['num_channels_joined'] == 1
    check_timestamp(resp['channels_joined'][-1]['time_stamp'], timestamp)

def test_stats_multiple_channels(users, channels):
    token = users['user1']['token']
    resp = user_stats(token)['user_stats']
    assert resp['channels_joined'][-1]['num_channels_joined'] == 3 

def test_stats_messages(users, channels):
    token = users['user1']['token']
    resp = user_stats(token)['user_stats']
    assert resp['messages_sent'][-1]['num_messages_sent'] == 2

def test_stats_dms(users):
    token = users['user1']['token']
    dm_create(token, [users['user2']['auth_user_id']])
    resp = user_stats(token)['user_stats']
    assert resp['dms_joined'][-1]['num_dms_joined'] == 1
    dm_create(token, [users['user2']['auth_user_id']])
    resp = user_stats(token)['user_stats']
    assert resp['dms_joined'][-1]['num_dms_joined'] == 2

def test_stats_involvment(users, channels):
    token = users['user1']['token']
    resp = user_stats(token)['user_stats']
    assert resp['involvement_rate'] == (3 + 2)/(3 + 3)
    dm_create(token, [users['user3']['auth_user_id']])
    resp = user_stats(token)['user_stats']
    assert resp['involvement_rate'] == (1 + 3 + 2)/(1 + 3 + 3)
    
#DREAMS_STATS_TESTS:
def test_dreams_stats_with_channels(users):
    timestamp = datetime.datetime.now().timestamp()
    token = users['user1']['token']
    channels_create(token, 'name', True)
    resp = users_stats(token)['dreams_stats']
    assert resp['channels_exist'][-1]['num_channels_exist'] == 1
    check_timestamp(resp['channels_exist'][-1]['time_stamp'], timestamp)

def test_dreams_multiple_channels(users, channels):
    token = users['user3']['token']
    resp = users_stats(token)['dreams_stats']
    assert resp['channels_exist'][-1]['num_channels_exist'] == 3

def test_dreams_messages(users, channels):
    token = users['user1']['token']
    resp = users_stats(token)['dreams_stats']
    assert resp['messages_exist'][-1]['num_messages_exist'] == 3

def test_dreams_stats_dms(users):
    token = users['user1']['token']
    dm_create(token, [users['user2']['auth_user_id']])
    resp = users_stats(token)['dreams_stats']
    assert resp['dms_exist'][-1]['num_dms_exist'] == 1
    dm_create(token, [users['user2']['auth_user_id']])
    resp = users_stats(token)['dreams_stats']
    assert resp['dms_exist'][-1]['num_dms_exist'] == 2
    
def test_dreams_utilizations(users, channels):
    token = users['user1']['token']
    resp = users_stats(token)['dreams_stats']
    assert resp['utilization_rate'] == 2/3
