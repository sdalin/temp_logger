import numpy as np
import requests
import simplejson as json
import getpass
import socket


def p2f(x):
    try:
        return float(x.rstrip('%'))
    except Exception:
        return np.nan


def sendEmail(subject=None, text=None):
    url = 'https://api.smtp2go.com/v3/'
    email = {'api_key': 'api-29BC9212AC3F11E78F88F23C91C88F4E',
             'sender': getpass.getuser() + '.at.' + socket.gethostname().replace(' ', '') + '@smtp2go.com',
             'to': ['sandersh6000@gmail.com', 'sdalin@gmail.com'],
             'subject': 'test',
             'text_body': 'This is a test email.'
             }
    if subject is not None:
        email['subject'] = subject
    if text is not None:
        email['text_body'] = text
    response = requests.post(url+'email/send', data=json.dumps(email))
    data = response.json()['data']
    if 'error_code' in data:
        raise Exception("Sending email failed. Response: " + data['error_code'] + ': ' + data['error'])
    return True
