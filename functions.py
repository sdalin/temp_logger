import numpy as np
import requests
import json
import getpass
import socket
import time
import sys
import subprocess


def p2f(x):
    try:
        return float(x.rstrip('%'))
    except Exception:
        return np.nan


def tailgrep(filename, searchterm):
    # also try checking out file_read_backwards
    if sys.platform == 'linux2':
        p1 = subprocess.Popen(['tac', filename], stdout=subprocess.PIPE)
    elif sys.platform == 'darwin':
        p1 = subprocess.Popen(['tail', '-r', filename], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', '-m1', searchterm], stdin=p1.stdout, stdout=subprocess.PIPE)
    text = p2.communicate()[0]
    p1.terminate()
    return text


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
        text = unicode(text, errors='replace')
        text = text.encode('ascii', 'replace')
        email['text_body'] = time.asctime() + "\n" + text
    response = requests.post(url+'email/send', data=json.dumps(email))
    data = response.json()['data']
    if 'error_code' in data:
        raise Exception("Sending email failed. Response: " + data['error_code'] + ': ' + data['error'])
    return True
