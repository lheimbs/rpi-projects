#!/usr/bin/env python3

from google_auth_oauthlib.flow import InstalledAppFlow

"""
import pickle
import os.path


from google.auth.transport.requests import Request
from oauth2client import file as oauth_file, client, tools
"""
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def authenticate():
    """creds = None
    store = oauth_file.Storage('token.json')
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or creds.invalid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('/home/pi/client_secret_cli.json', SCOPES)
            creds = flow.run_console()
            #service = build('sheets', 'v4', http=creds.authorize(Http()))
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)"""
    flow = InstalledAppFlow.from_client_secrets_file('/home/pi/client_secret_cli.json', SCOPES)
    creds = flow.run_console()
    return creds
