'''
Authors:
    Alec Dudley-Bestow, z5260201
    
Date:
    24 March 2021
'''

import pytest
from src.auth import auth_login, auth_register, get_data, \
    auth_logout, auth_request_reset, auth_reset_password
from src.other import clear
from src.error import InputError

@pytest.fixture
def register_input():
    clear()
    return {'email' : 'validemail@email.com',
        'password' : 'validpassword',
        'name_first' : 'thisisalongfirstname',
        'name_last' : 'lastname'}

@pytest.fixture
def login_input(register_input):
    token1 = auth_register(**register_input)['token']
    user2 = {
        'email' : 'anothervalidemail@email.com',
        'password' : 'adifferentvalidpassword',
        'name_first' : 'hayden',
        'name_last' : 'smith'
    }
    token2 = auth_register(**user2)['token']
    return {    
        'user1' : {
            'email' : register_input['email'],
            'password' : register_input['password'],
        },
        'user2' : {
            'email' : user2['email'],
            'password' : user2['password'],
        },
        'token1' : token1,
        'token2' : token2
    }

@pytest.fixture
def invalid_emails():
    return [
        'invalidemail@.com',
        'invalidemail.com',
        '@invalid.com',
        '',
        'invalidemail',
        '@invalid.com',
        'asdf@asdf@gmail.com',
    ]
    
def invalid_input(function, dictionary, key, invalid_list):
    for elem in invalid_list:
        with pytest.raises(InputError):
            dictionary[key] = elem
            function(**dictionary)

#test too long and too short first name
def test_auth_register_invalid_firstname(register_input):
    invalid_input(auth_register, register_input, 'name_first', ['', 'x'*51])

#test too long and too short last name        
def test_auth_register_invalid_lastname(register_input):
    invalid_input(auth_register, register_input, 'name_last', ['', 'x'*51])

#test all invalid email types
def test_auth_register_invalid_email(register_input, invalid_emails):
    invalid_input(auth_register, register_input, 'email', invalid_emails)
    
#test function rejects repeated email
def test_auth_register_repeated_email(register_input):
    auth_register(**register_input)
    with pytest.raises(InputError):
        auth_register(**register_input)

#test function rejects invalid passwords
def test_auth_register_invalid_password(register_input):
    invalid_input(auth_register, register_input, 'password', ['', '1234', 'passw'])

#test works for correct inputs
def test_auth_register_valid_inputs(register_input):
    user1 = auth_register(**register_input)
    register_input['email'] = 'user2email@gmail.com'
    user2 = auth_register(**register_input)
    register_input['email'] = 'user3email@gmail.com'
    user3 = auth_register(**register_input)
    assert user1['token'] != user2['token'] != user3['token']
    assert user1['auth_user_id'] != user2['auth_user_id'] != user3['auth_user_id']

#test can't login with incorrect password
def test_auth_login_incorrect_password(login_input):
    invalid_passwords = ['asdf', '12345', 'this is wrong']
    invalid_input(auth_login, login_input['user1'], 'password', invalid_passwords) 
    invalid_input(auth_login, login_input['user2'], 'password', invalid_passwords) 

#test can't login with invalid email type
def test_auth_login_invalid_email(login_input, invalid_emails):
    invalid_input(auth_login, login_input['user1'], 'email', invalid_emails)
    invalid_input(auth_login, login_input['user2'], 'email', invalid_emails)

#test can't login with invalid email of correct type
def test_auth_login_incorrect_emails(login_input):
    incorrect_emails = [
        'asdf@gmail.com',
        'notanemail@email.com.au',
        'yetanotheremail@exemail.com'
    ]
    invalid_input(auth_login, login_input['user1'], 'email', incorrect_emails)
    invalid_input(auth_login, login_input['user2'], 'email', incorrect_emails)

#test that auth login works correctly for multiple sessions
def test_auth_login_correct_input(login_input):
    
    sessions_list = [auth_login(**login_input['user1']),
        auth_login(**login_input['user1']),
        auth_login(**login_input['user1']),
        auth_login(**login_input['user1']),
        auth_login(**login_input['user1']),
        auth_login(**login_input['user2']),
        auth_login(**login_input['user2']),
        auth_login(**login_input['user2']),
    ]
    token_list = [session['token'] for session in sessions_list]
    #check that all tokens are unique
    assert len(set(token_list)) == len(token_list)
    
#test that logout works with correct input
def test_auth_logout(login_input):
    assert auth_logout(login_input['token1'])['is_success']

#test that logout works with correct input
def test_auth_logout_with_clear(login_input):
    clear()
    assert not auth_logout(login_input['token1'])['is_success']

#test that logging out the same session twice fails
def test_auth_logout_fail(login_input):
    assert auth_logout(login_input['token1'])['is_success']
    assert not auth_logout(login_input['token1'])['is_success']

#test that user can be logged back in after logging out
def test_auth_logout_log_back_in(login_input):
    assert auth_logout(login_input['token2'])['is_success']
    token = auth_login(**login_input['user2'])['token']
    assert auth_logout(token)['is_success']

#test that logout works an all sessions
def test_auth_logout_multiple(login_input):
    token_list = [login_input['token1']]
    for _ in range(50):
        token_list.append(auth_login(**login_input['user2'])['token'])
    
    #reverse to test logging out non last session
    token_list.reverse()
    for token in token_list:
        assert auth_logout(token)['is_success']

def test_auth_logout_middle(login_input):
    token = auth_login(**login_input['user2'])['token']
    auth_login(**login_input['user2'])
    auth_logout(token)
    auth_login(**login_input['user2'])

def test_request_reset(login_input):
    auth_request_reset(login_input['user1']['email'])

def test_request_reset_unused_email(login_input):
    with pytest.raises(InputError):
        auth_request_reset('unused@email.com')

def test_password_reset_invalid_code(login_input):
    with pytest.raises(InputError):
        auth_reset_password('notavalidcode', 'validpassword')

def test_password_reset_invalid_password(login_input):
    reset_code = auth_request_reset(login_input['user1']['email'])
    with pytest.raises(InputError):
        auth_reset_password(reset_code, '')

def test_password_reset(login_input):
    reset_code = auth_request_reset(login_input['user1']['email'])
    auth_reset_password(reset_code, 'newpassword')
    with pytest.raises(InputError):
        auth_login(**login_input['user1'])
    login_input['user1']['password'] = 'newpassword'
    auth_login(**login_input['user1'])
