'''
Authors:
    Alec Dudley-Bestow, z5260201

Date:
    24 March 2021
'''
import pytest
import requests
import json
from src import config
from src.error import InputError, AccessError

ACCESS_ERROR = 403
INPUT_ERROR = 400

REGISTER = 'auth/register/v2'
LOGIN = 'auth/login/v2'
LOGOUT = 'auth/logout/v1'

@pytest.fixture
def register_input():
    requests.delete(config.url + 'clear/v1')
    return {
        'user1' : {'email' : 'validemail@email.com',
            'password' : 'validpassword',
            'name_first' : 'thisisalongfirstname',
            'name_last' : 'lastname'
        },
        'user2' : {'email' : 'anothervalidemail@email.com',
            'password' : 'adifferentvalidpassword',
            'name_first' : 'thisisalongfirstname',
            'name_last' : 'lastname'
        },
    }
    
@pytest.fixture
def login_input(register_input):

    resp1 = requests.post(config.url + REGISTER, json = register_input['user1']).json()
    resp2 = requests.post(config.url + REGISTER, json = register_input['user2']).json()
    
    return {
        'user1' : {'email' : 'validemail@email.com',
            'password' : 'validpassword',
        },
        'user2' : {'email' : 'anothervalidemail@email.com',
            'password' : 'adifferentvalidpassword',
        },
        'token1' : {'token' : resp1['token']},
        'token2' : {'token' : resp2['token']},
    }
    
def input_error(url, invalid_data):
    assert requests.post(config.url + url, json=invalid_data).status_code == INPUT_ERROR

def test_auth_register(register_input):
    requests.post(config.url + REGISTER, json = register_input['user1'])
    requests.post(config.url + REGISTER, json = register_input['user2'])

def test_auth_register_email(register_input):
    register_input['user1']['email'] = '@@email.com'
    input_error(REGISTER, register_input['user1'])

def test_auth_register_reapeated(register_input):
    requests.post(config.url + REGISTER, json = register_input['user1'])
    input_error(REGISTER, register_input['user1'])

def test_auth_register_password(register_input):
    register_input['user1']['password'] = 'asdf'
    input_error(REGISTER, register_input['user1'])

def test_auth_register_firstname(register_input):
    register_input['user1']['name_first'] = ''
    input_error(REGISTER, register_input['user1'])
    register_input['user1']['name_first'] = 'x'*51
    input_error(REGISTER, register_input['user1'])

def test_auth_register_lastname(register_input):
    register_input['user1']['name_last'] = ''
    input_error(REGISTER, register_input['user1'])
    register_input['user1']['name_last'] = 'x'*51
    input_error(REGISTER, register_input['user1'])

def test_auth_login(login_input):
    resp1 = requests.post(config.url + LOGIN, json = login_input['user1']).json()
    resp2 = requests.post(config.url + LOGIN, json = login_input['user1']).json()
    assert resp1 != resp2

def test_auth_login_email(login_input):
    login_input['user1']['email'] = 'emailnotused@gmail.com'
    input_error(LOGIN, login_input['user1'])

def test_auth_login_password(login_input):
    login_input['user1']['password'] = 'nottherightpassword'
    input_error(LOGIN, login_input['user1'])

def test_auth_logout_single(login_input):
    assert requests.post(config.url + LOGOUT, json = login_input['token1']).json()['is_success']

def test_auth_logout(login_input):
    token2 = requests.post(config.url + LOGIN, json = login_input['user1']).json()['token']
    assert requests.post(config.url + LOGOUT, json = login_input['token1']).json()['is_success']
    assert requests.post(config.url + LOGOUT, json = {'token' : token2}).json()['is_success']
    assert not requests.post(config.url + LOGOUT, json = login_input['token1']).json()['is_success']
