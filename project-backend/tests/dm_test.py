'''
Authors: 
    Justin Wu, z5316037
    Fengyu Wang, z5187561
    Dionne So, z5310329
    William Zheng, z5313015

Date:
    23 March 2021
'''
import pytest

from src.error import InputError, AccessError
from src.other import clear
from src.dm import dm_create, dm_list, dm_details, dm_invite, dm_leave, dm_remove, dm_messages
from src.user import user_profile
from src.auth import auth_register
from src.message import message_senddm, message_sendlaterdm
import time
from datetime import datetime, timedelta, timezone

@pytest.fixture
def users():
    '''
    Fixture that sets up 2 users and returns each of their tokens and u_ids.
    '''
    clear()
    user1 = auth_register("user@email.com", "jaajdfs23", "First", "User")
    user2 = auth_register("test@email.com", "heskjdf23", "Second", "User")
    token1 = user1['token']
    token2 = user2['token']
    u_id1 = user1['auth_user_id']
    u_id2 = user2['auth_user_id']
    return (token1, token2, u_id1, u_id2)

@pytest.fixture
def spare_user():
    user3 = auth_register("test1@email.com", "heskjdf234", "third", "User2")
    token3 = user3['token']
    u_id3 = user3['auth_user_id']

    return (token3, u_id3)

@pytest.fixture
def dm_ids(users):
    '''
    Set up 2 dms:
        - dm_id1: User1 dms to user2
        - dm_id2: User2 dms to user1
    '''
    token1, token2, u_id1, u_id2 = users
    dm_id1 = dm_create(token1, [u_id2])
    dm_id2 = dm_create(token2, [u_id1])
    return (dm_id1, dm_id2)

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for dm_create-------------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_dm_create(dm_ids):
    '''
    Test for correct output 'dm_id' and 'dm_name' upon creating a dm made by user1.
    '''
    dm_id1, dm_id2 = dm_ids
    assert dm_id1 == {
        'dm_id': 1,
        'dm_name': 'firstuser,seconduser'
    }
    assert dm_id2 == {
        'dm_id': 2,
        'dm_name': 'firstuser,seconduser'
    }
def test_dm_create_multiple_users(users):
    '''
    Test for correct output for multiple dms.
    '''
    # Let owner be dm_creator 
    owner, _, _, user2 = users
    # Setting up 2 more users
    user3 = auth_register("user3@email.com", "xcvmncxjdfs23", "Third", "User")['auth_user_id']
    user4 = auth_register("user4@email.com", "asdffs23", "Forth", "User")['auth_user_id']
    assert dm_create(owner, [user2]) == {
        'dm_id': 1,
        'dm_name': 'firstuser,seconduser'
    }
    assert dm_create(owner, [user2, user3]) == {
        'dm_id': 2,
        'dm_name': 'firstuser,seconduser,thirduser'
    }
    assert dm_create(owner, [user2, user3, user4]) == {
        'dm_id': 3,
        'dm_name': 'firstuser,forthuser,seconduser,thirduser' #Alphabetically sorted
    }

def test_dm_create_except(users):
    '''
    Test for InputError when:
        - u_id does not refer to a valid user
        - owner invites themselves to a dm
        - identical dm being created again
    '''
    clear()
    # token1, token2, u_id1, u_id2 = users
    # u_id1 creates dm to u_id2
    user1 = auth_register("user@email.com", "jaajdfs23", "First", "User")
    user2 = auth_register("test@email.com", "heskjdf23", "Second", "User")
    token1 = user1['token']
    token2 = user2['token']
    u_id1 = user1['auth_user_id']
    u_id2 = user2['auth_user_id']
    with pytest.raises(InputError):
        dm_create(token1, [user2, 999]) #u_id does not refer to a valid user.
        dm_create(token2, [user1, 100, 101, 102])
        dm_create(token1, [u_id1]) #owner invites themselves
        dm_create(token1, [u_id1, 999, 199, 299])
        dm_create(token1, [u_id2]) # Same dm being created again

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for dm_list---------------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_dm_list(users, dm_ids):
    '''
    Test for correct output of dms upon listing the dms users are a part of.
    '''
    token1, token2, _, _ = users
    dm1, _ = dm_ids
    # User1 & User2 should be a part of 2 dms
    assert dm_list(token1) == {
        'dms': [
            {
                'dm_id': 1,
                'name': 'firstuser,seconduser'
            },
            {
                'dm_id': 2,
                'name': 'firstuser,seconduser'
            }
        ]
    }
    assert dm_list(token2) == {
        'dms': [
            {
                'dm_id': 1,
                'name': 'firstuser,seconduser'
            },
            {
                'dm_id': 2,
                'name': 'firstuser,seconduser'
            }
        ]
    }
    # Adding 2 additonal users
    user3 = auth_register('user@gmail.com', 'password1234', 'Marc', 'Chee')
    user4 = auth_register('user2@gmail.com', 'pw1234', 'David', 'Chee')
    # User1 invites user3 and user4 to dm1
    dm_invite(token1, dm1['dm_id'], user3['auth_user_id'])
    dm_invite(token1, dm1['dm_id'], user4['auth_user_id'])
    assert dm_list(user3['token']) == {
        'dms':[
            {
                'dm_id': 1,
                'name': 'firstuser,seconduser'
            }
        ]
    }

    assert dm_list(user4['token']) == {
        'dms':[
            {
                'dm_id': 1,
                'name': 'firstuser,seconduser'
            }
        ]
    }

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for dm_details------------------------------------- #
# --------------------------------------------------------------------------------------- #

def member_info(user_profile):
    return {
        'u_id': user_profile['u_id'],
        'email': user_profile['email'],
        'name_first': user_profile['name_first'],
        'name_last': user_profile['name_last'],
        'handle_str': user_profile['handle_str'],
    }

def test_dm_details(users, dm_ids):
    '''
    Test for correct output of dm details for dms that users are a part of.
    '''
    token1, token2, u_id1, u_id2 = users
    dm1, _ = dm_ids
    assert dm_details(token1, dm1['dm_id']) == {
        'name': 'firstuser,seconduser',
        'members': [
            member_info(user_profile(token1, u_id1)['user']),
            member_info(user_profile(token1, u_id2)['user']),
        ]
    }
    user3 = auth_register('user@gmail.com', 'password1234', 'Marc', 'Chee')['auth_user_id']
    user4 = auth_register('user2@gmail.com', 'pw1234', 'David', 'Chee')['auth_user_id']
    dm_invite(token1, dm1['dm_id'], user3)
    dm_invite(token1, dm1['dm_id'], user4)
    assert dm_details(token2, dm1['dm_id']) == {
        'name': 'firstuser,seconduser',
        'members': [
            member_info(user_profile(token1, u_id1)['user']),
            member_info(user_profile(token1, u_id2)['user']),
            member_info(user_profile(token1, user3)['user']),
            member_info(user_profile(token1, user4)['user']),
        ]
    }
    print(member_info(user_profile(token1, u_id1)['user']))

def test_dm_details_invalid_dm(dm_ids):
    '''
    Test for InputError when:
        - DM ID is not a valid DM.
    '''
    dm1, dm2 = dm_ids
    clear()
    user1 = auth_register("user@email.com", "jaajdfs23", "First", "User")['token']
    user2 = auth_register("test@email.com", "heskjdf23", "Second", "User")['token']
    with pytest.raises(InputError):
        dm_details(user1, dm1['dm_id'])
        dm_details(user1, dm2['dm_id'])
        dm_details(user2, dm1['dm_id'])
        dm_details(user2, dm2['dm_id'])

def test_dm_details_auth_not_member(dm_ids):
    '''
    Test for AccessError when:
        - Authorised user is not a member of this DM with dm_id.
    '''
    dm1, dm2 = dm_ids
    user3 = auth_register('user@gmail.com', 'password1234', 'Marc', 'Chee')['token']
    user4 = auth_register('user2@gmail.com', 'pw1234', 'David', 'Chee')['token']
    with pytest.raises(AccessError):
        dm_details(user3, dm1['dm_id'])
        dm_details(user3, dm2['dm_id'])
        dm_details(user4, dm1['dm_id'])
        dm_details(user4, dm2['dm_id'])

# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for dm_invite-------------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_valid_dm_invite(users, dm_ids, spare_user):
    #User1 and user2 register account, user1 created dm and invited user3
    token1, token2, u_id1, u_id2 = users
    token3, u_id3 = spare_user
    dm_id, _ = dm_ids
    dm_id1 = dm_id['dm_id']
    dm_invite(token1, dm_id['dm_id'], u_id3)
    #Getting user1, user2's, user3's info, their dm details should be the same
    user1_profile = user_profile(token1, u_id1)['user']
    user2_profile = user_profile(token2, u_id2)['user']
    user3_profile = user_profile(token3, u_id3)['user']
    user1_uid = user1_profile['u_id']
    user2_uid = user2_profile['u_id']
    user3_uid = user3_profile['u_id']
    # print(f"user1_uid = {user1_uid}, user2_uid = {user2_uid}")
    assert dm_details(token1, dm_id1) == {
        'name': f"{dm_id['dm_name']}",
        'members': [
            member_info(user_profile(token1, user1_uid)['user']),
            member_info(user_profile(token1, user2_uid)['user']),
            member_info(user_profile(token1, user3_uid)['user']),
        ]
    }
    assert dm_details(token2, dm_id1) == {
        'name': f"{dm_id['dm_name']}",
        'members': [
            member_info(user_profile(token1, user1_uid)['user']),
            member_info(user_profile(token1, user2_uid)['user']),
            member_info(user_profile(token1, user3_uid)['user']),
        ]
    }

def test_nonExisting_dm(users):
    token1, token2, u_id1, u_id2 = users
    with pytest.raises(InputError):
        dm_invite(token1, 10, u_id2)
    with pytest.raises(InputError):
        dm_invite(token2, 2, u_id2)
    with pytest.raises(InputError):
        dm_invite(token2, -1, u_id1)

def test_notValid_user(users, dm_ids):
    _, token2, _, _ = users
    dm_id1, _= dm_ids
    with pytest.raises(InputError):
        dm_invite(token2,  dm_id1['dm_id'], 20)
    with pytest.raises(InputError):
        dm_invite(token2,  dm_id1['dm_id'], 10)   
    with pytest.raises(InputError):
        dm_invite(token2,  dm_id1['dm_id'], 5)

def test_notMember(users, dm_ids):
    #the users that are the member of the DM
    _, _, u_id1_dm_member, u_id2_dm_member = users
    #register as dm
    dm_id1, _= dm_ids
    #Register new users who are not register as dm
    new_user = auth_register("newuser@email.com", "userpassword123", "newUser_first", "newUser_last")
    new_user1 = auth_register("newuser1@email.com", "userpassword1234", "newUser_first1", "newUser_last1")
    #The unregistered new_user invite another unregistered new_user
    with pytest.raises(AccessError):
        dm_invite(new_user['token'], dm_id1['dm_id'], u_id2_dm_member)
    #The unregistered new_user invite another registered new_user
    with pytest.raises(AccessError):
        dm_invite(new_user1['token'], dm_id1['dm_id'], u_id1_dm_member)


# --------------------------------------------------------------------------------------- #
# -------------------------------- Tests for dm_leave ----------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_dm_leave():
    # Reset
    clear()

    # Register users
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname2')

    # Create DM
    dm = dm_create(auth['token'], [user['auth_user_id']])

    # Leave DM
    dm_leave(user['token'], dm['dm_id'])

    assert dm_details(auth['token'], dm['dm_id'])['members'] == [
        member_info(user_profile(auth['token'], auth['auth_user_id'])['user'])
    ]

def test_dm_leave_invalid_dm():
    # Reset
    clear()

    # Register users
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')

    # Leave Dm
    with pytest.raises(InputError):
        dm_leave(auth['token'], -1) 

def test_dm_leave_permission():
    # Reset
    clear()

    # Register users
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')
    user1 = auth_register('email02@email.com', 'password', 'firstname', 'lastname')

    # Create Dm
    dm = dm_create(auth['token'], [user['auth_user_id']])

    # Leave Dm
    with pytest.raises(AccessError):
        dm_leave(user1['token'], dm['dm_id']) 

# --------------------------------------------------------------------------------------- #
# -------------------------------- Tests for dm_remove ---------------------------------- #
# --------------------------------------------------------------------------------------- #

def test_dm_remove():
    # Reset
    clear()

    # Register users
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')

    # Create DM
    dm = dm_create(auth['token'], [user['auth_user_id']])

    # Leave DM
    dm_remove(auth['token'], dm['dm_id'])

    # Get DM list
    all_dms = dm_list(auth['token'])
    
    assert all_dms['dms'] == []

def test_dm_remove_invalid_dm():
    # Reset
    clear()

    # Register users
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    
    # Leave Dm
    with pytest.raises(InputError):
        dm_remove(auth['token'], -1) 

def test_dm_remove_permission():
    # Reset
    clear()

    # Register users
    auth = auth_register('email0@email.com', 'password', 'firstname', 'lastname')
    user = auth_register('email1@email.com', 'password', 'firstname', 'lastname')

    # Create Dm
    dm = dm_create(auth['token'], [user['auth_user_id']])

    # Leave Dm
    with pytest.raises(AccessError):
        dm_remove(user['token'], dm['dm_id']) 

def test_dm_messages():
    '''
    Tests that dm_messages return correct output
    '''
    user1 = auth_register("user1@email.com", "user1234", "user1", "user1")
    user2 = auth_register("user2@email.com", "user2345", "user2", "user2")
    dm_id = dm_create(user1['token'], [user2['auth_user_id']])['dm_id']
    message_senddm(user1['token'], dm_id, 'amessage')
    resp = dm_messages(user2['token'], dm_id, 0)
    
    assert resp['start'] == 0
    assert resp['end'] == -1
    assert resp['messages'][0]['message'] == 'amessage'

def test_dm_messages_invalid_dm(users):
    '''
    Tests that dm_meessages returns input error if dm_id is invalid
    '''
    token1, _, _, _ = users
    with pytest.raises(InputError):
        dm_messages(token1, '42', 0)

def test_dm_messages_no_access(dm_ids, spare_user):
    '''
    Tests that dm_meessages returns access error if user is not a member
    '''
    token3, _ = spare_user
    dm_id, _ = dm_ids
    new_user = auth_register("markcheese@email.com", "asdf34234", "Mark", "Cheese")
    fake_user1 = auth_register("abc@email.com", "a23432434234", "abc", "123")['auth_user_id']
    fake_user2 = auth_register("xyz@email.com", "xyzasdf2334", "xyz", "123")['auth_user_id']
    with pytest.raises(AccessError):
        dm_messages(token3, dm_id['dm_id'], 0)
        dm_invite(new_user['token'], dm_id['dm_id'], fake_user1)
        dm_invite(new_user['token'], dm_id['dm_id'], fake_user2)

'''
Authors:
    Fengyu Wang z5187561
Date:
    12 April 2021
'''
# --------------------------------------------------------------------------------------- #
# ----------------------------- Tests for message_sendlaterdm --------------------------- #
# --------------------------------------------------------------------------------------- #
@pytest.fixture
def timestamps():
    valid_sending_time = datetime.now() + timedelta(seconds = 1.5)
    valid_timestamp = valid_sending_time.timestamp()
    invalid_sending_time = datetime.now() - timedelta(seconds = 1.5)
    invalid_timestamp = invalid_sending_time.timestamp()
    return (valid_timestamp, invalid_timestamp)

def test_message_sendlaterdm_normal(users, dm_ids, timestamps):
    token1, _, _, _ = users
    dm_id1, _ = dm_ids    #Here used token 1 to create a public channel
    #user 1 send a message that only triggers after 3 seconds
    valid_timestamp, _ = timestamps
    message_sendlaterdm(token1, dm_id1['dm_id'], 'Test Message', valid_timestamp)
    #check the message immediatelly after send, make sure there's no message
    # message = dm_messages(token1, dm_id1['dm_id'], 0)['messages']
    # assert not message
    #check the message after 3 seconds, make sure there's a message
    time.sleep(2)
    message = dm_messages(token1, dm_id1['dm_id'], 0)['messages'][0]['message']
    assert message == 'Test Message'

def test_message_sendlater_inputError(users, dm_ids, timestamps):
    token1, _, _, _ = users
    dm_id1, _ = dm_ids 
    valid_timestamp, invalid_timestamp = timestamps
    with pytest.raises(InputError):
        message_sendlaterdm(token1, 1000, 'Test Message', valid_timestamp)   #invalid channel ID
    with pytest.raises(InputError):
        message_sendlaterdm(token1, dm_id1['dm_id'], 'a'*1001, valid_timestamp) #message is more than 1000 chars
    with pytest.raises(InputError):
        message_sendlaterdm(token1, dm_id1['dm_id'], 'a'*1001, invalid_timestamp) #time send is in the past

def test_message_sendlater_accessError(users, dm_ids, timestamps):
    #user 1 created a channel, but user 2 tried to send the message
    token1, _, _, u_id2 = users
    user3 = auth_register("user3@email.com", "jaajdfs235", "Firstthree", "Userthree")
    dm_id1 = dm_create(token1, [u_id2])
    valid_timestamp, _ = timestamps
    with pytest.raises(AccessError):
        message_sendlaterdm(user3['token'], dm_id1['dm_id'], 'Test Message', valid_timestamp)
