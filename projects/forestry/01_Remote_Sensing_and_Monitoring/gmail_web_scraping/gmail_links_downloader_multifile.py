# Extract a link from the email body, visit that link,
# and then download a file from a link on that dynamically generated page 
# Using Gmail - OAuth2 method

from __future__ import print_function #Python2 print() compatibility

import base64
import json
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
SENDER_EMAIL = 'no-reply@maanmittauslaitos.fi'
LINK_PREFIX = 'https://asiointi.maanmittauslaitos.fi/lataukset/'
OUTPUT_FILE = 'metadata.txt'

# Function to authenticate in Gmail
def get_authenticated_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print('An error occurred: %s' % error)
        return None


# Function to create new folder to save downloaded files
def create_output_folder(filename):
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{current_datetime}_{filename.split('.')[0]}"
    os.makedirs(folder_name, exist_ok=True)
    print(f"Created folder {folder_name}.")
    return folder_name


# Function to check for "Downloaded" folder in the email and create it if it doesn't exist
def check_for_label(service):
    print("Checking for 'Downloaded' label...")
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    downloaded_label_id = None
    for label in labels:
        if label['name'] == 'Downloaded':
            downloaded_label_id = label['id']
            print("'Downloaded' label found.")
            break
    if not downloaded_label_id:
        print("Creating 'Downloaded' label...")
        body = {'name': 'Downloaded'}
        result = service.users().labels().create(userId='me', body=body).execute()
        downloaded_label_id = result['id']
        print("'Downloaded' label created.")
    return downloaded_label_id


# Function to processing the message to find the HTML body and the link
def process_message(msg):
    for part in msg['payload']['parts']:
        if part['mimeType'] == 'text/html':
            html_content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            link_in_email = find_link(html_content, LINK_PREFIX)
            if link_in_email:
                print(f"Found link in email: {link_in_email}")
                # Visit the link and find the download link on the page
                download_links, data = find_download_link(link_in_email)
                if download_links:
                    print("Found download links:")
                    for download_link in download_links:
                        print(f"- {download_link}")
                        filename = download_link.split('/')[-1]
                        folder_name = create_output_folder(filename)
                        save_order_metadata(data, folder_name)
                        save_link_metadata(data, folder_name, download_link)
                        success = download_file(download_link, folder_name)
                        if not success:
                            return False
                    return True 
                else:
                    print("No download links found on the download page.")
                    return False 
            else:
                print("No link found in the email body.")
                return


# Function to save order metadata
def save_order_metadata(data, folder_name):
    order_metadata_filename = f"{folder_name}/order_metadata.json"
    with open(order_metadata_filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print(f"Order metadata saved: {order_metadata_filename}")


# Function to save link metadata
def save_link_metadata(data, folder_name, download_links):
    if data and 'files' in data:
        for i, file_data in enumerate(data['files']):
            for j, result in enumerate(file_data['results']['results']):  # Directly access results
                download_url = result.get('path')
                if download_url and download_url in download_links:
                    metadata_filename = f"{folder_name}/link_metadata_{i}_{j}_{download_url.split('/')[-1]}.json"
                    with open(metadata_filename, 'w', encoding='utf-8') as file:
                        json.dump(result, file, ensure_ascii=False, indent=4)
                    print(f"Link metadata saved: {metadata_filename}")
    else:
        print("No data found to save as link metadata.")
        
# Main function to search for letter, find links and download file
def download_file_from_email():
    service = get_authenticated_service()
    if service is None:
        return
    downloaded_label_id = check_for_label(service) # Check for "Downloaded" label and create it if it doesn't exist

    # Search for unread emails from specific sender
    print(f"Searching for unread emails from: {SENDER_EMAIL}")
    results = service.users().messages().list(userId='me', q=f"from:{SENDER_EMAIL} is:unread").execute()
    messages = results.get('messages', [])
    print(f"Found {len(messages)} unread email(s).")

    for message in messages:
        print(f"Processing email ID: {message['id']}")
        msg = service.users().messages().get(userId='me', id=message['id']).execute()

        try: # Mark the email as read immediately
            service.users().messages().modify(userId='me', id=message['id'],
                                              body={'removeLabelIds': ['UNREAD']}).execute()
            print(f"Email ID {message['id']} temporarily marked as read.")
            success = process_message(msg) # Process the message parts to find the HTML body and the link
            
            if success: # Move email to "Downloaded" folder
                service.users().messages().modify(userId='me', id=message['id'], 
                                                    body={'addLabelIds': [downloaded_label_id],
                                                          'removeLabelIds': ['INBOX']}).execute()
                print(f"Email ID {message['id']} labeled as 'Downloaded'.")
            else:
                raise Exception("Download failed.")  # Raise an exception if download fails
                
        except Exception as error:
            print(f"An error occurred: {error}")
            # Mark the email back as unread
            service.users().messages().modify(userId='me', id=message['id'],
                                              body={'addLabelIds': ['UNREAD']}).execute()
            print(f"Email ID {message['id']} marked back as unread due to error.")


# Function to find a link with the specified prefix in HTML content
def find_link(html_content, prefix):
    soup = BeautifulSoup(html_content, 'html.parser')
    for link in soup.find_all('a', href=True):
        if link['href'].startswith(prefix):
            return link['href']
    return None


# Function to visit a webpage and find the download link with the specified prefix
def find_download_link(url):
    order_id = url.split('/')[-1].split('?')[0]  # Extract order ID
    # Construct API URL
    api_url = f"{url.split('/')[0]}//{url.split('/')[2]}/lataukset/api/spatialdatafilesorders/{order_id}"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = json.loads(response.content)
        #print(data)
        download_links = []

        for file_data in data['files']:
            # Iterate through 'results' within each file
            for result in file_data['results']['results']:
                download_link = result.get('path')
                if download_link:
                    download_links.append(download_link)

        if download_links:
            return download_links, data  # Return the list of download URLs and data
        else:
            print("No download links found in the API response.")

    return None, None  # Return None if no valid download URLs are found


# Function to download a laz file
def download_file(url, folder_name):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        filename = url.split('/')[-1]
        file_path = os.path.join(folder_name, filename)
        
        print(f"Downloading file: {file_path}")
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                   f.write(chunk)
        print(f"Downloaded file: {file_path}")
        success = True
        return success
    else:
        print(f"Error downloading file: {url}")
        success = False
        return success


if __name__ == '__main__':
    download_file_from_email()
