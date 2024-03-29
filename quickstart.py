from __future__ import print_function
import pickle
import os.path
import base64
import email
from apiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    #if not labels:
    #    print('No labels found.')
    #else:
    #    print('Labels:')
    #    for label in labels:
    #        print(label['name'])

    # savish
    print('Savish')
    msgs = ListMessagesMatchingQuery(service, 'me')
    print('Meassages:')
    #ind = 0
    for ind,msg in enumerate(msgs):
        #ind = ind + 1
        print('INDEX %i -' %(ind))
        GetMessage(service, 'me', msg[u'id'])
        if ind == 20:
            #GetMessage(service, 'me', msg[u'id'])
            break



"""Get a list of Messages from the user's mailbox.
"""




def ListMessagesMatchingQuery(service, user_id, query=''):
  """List all Messages of the user's mailbox matching the query.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: String used to filter messages returned.
    Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

  Returns:
    List of Messages that match the criteria of the query. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate ID to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               q=query).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id, q=query,
                                         pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError, error:
    print ('An error occurred:')


def ListMessagesWithLabels(service, user_id, label_ids=[]):
  """List all Messages of the user's mailbox with label_ids applied.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    label_ids: Only return Messages with these labelIds applied.

  Returns:
    List of Messages that have all required Labels applied. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate id to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               labelIds=label_ids).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id,
                                                 labelIds=label_ids,
                                                 pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError, error:
    print ('An error occurred:')



def GetMessageBody(service, user_id, msg_id):
    try:
            message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
            msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
            mime_msg = email.message_from_string(msg_str)
            messageMainType = mime_msg.get_content_maintype()
            if messageMainType == 'multipart':
                    for part in mime_msg.get_payload():
                            if part.get_content_maintype() == 'text':
                                    return part.get_payload()
                    return ""
            elif messageMainType == 'text':
                    return mime_msg.get_payload()
    except errors.HttpError, error:
            print ('An error occurred:' + error)

def GetMessage(service, user_id, msg_id):
  """Get a Message with given ID.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id ).execute()

    #msg_sb = message['payload']['parts'][0]['parts'][0]['body']['data']
    #print(message)
    #return message
    #msg_str = base64.urlsafe_b64decode(msg_sb.encode('ASCII'))
    #print("yo")
    #print(msg_str)
    attachments_email = []
    text_plain_msg = ''
    text_html_msg = ''
    msg_body = message["payload"]["parts"]
    for msg_part in msg_body:
      if msg_part['mimeType'] == 'multipart/alternative':
        for msg_subpart in msg_part['parts']:
          if msg_subpart['mimeType'] == 'text/plain':
            text_plain_msg = base64.urlsafe_b64decode(msg_subpart['body']['data'].encode('ASCII'))
          elif msg_subpart['mimeType'] == 'text/html':
            text_html_msg = base64.urlsafe_b64decode(msg_subpart['body']['data'].encode('ASCII'))
      elif msg_part['mimeType'] == 'text/plain':
        text_plain_msg = base64.urlsafe_b64decode(msg_part['body']['data'].encode('ASCII'))
      elif msg_part['mimeType'] == 'text/html':
        text_html_msg = base64.urlsafe_b64decode(msg_part['body']['data'].encode('ASCII'))
      else:
        attachments_email.append(msg_part)
    
    headers=message["payload"]["headers"]
    subject = [i['value'] for i in headers if i["name"]=="Subject"]
    from_mail = [i['value'] for i in headers if i["name"]=="From"]
    to_mail = [i['value'] for i in headers if i["name"]=="To"]
    cc_mail = [i['value'] for i in headers if i["name"]=="Cc"]
    date_mail = [i['value'] for i in headers if i["name"]=="Date"]
    print('DATE - ' + str(date_mail))
    print('FROM  - ' + str(from_mail))
    print('TO  - ' + str(to_mail))
    print('Cc  - ' + str(cc_mail))
    print('Subject  - ' + str(subject[0]))
    print('Message - ' + text_plain_msg)
    print('Html Message - ' + text_html_msg)
    print('Attachments List - ' + str(attachments_email))
    return message
  except errors.HttpError, error:
    print ('An error occurred:')



def GetMimeMessage(service, user_id, msg_id):
  """Get a Message and use it to create a MIME Message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A MIME Message, consisting of data from Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id,
                                             format='raw').execute()

    #print ('Message snippet: %s' % (message['snippet']))

    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
    print(msg_str)
    mime_msg = email.message_from_string(msg_str)

    return mime_msg
  except errors.HttpError, error:
    print ('An error occurred:')


if __name__ == '__main__':
    main()