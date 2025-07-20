from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pickle
import os
import io
from PIL import Image
from tkinter import Tk, filedialog
import mimetypes

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def get_google_drive_service():
    creds = None
    while not os.path.exists('token.pickle'):
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            print('Saving credentials to token.pickle...')
            pickle.dump(creds, token)

    with open('token.pickle', 'rb') as token:
        print('Loading credentials from token.pickle...')
        creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.

    print('Checking credentials validity...')

    if not creds or not creds.valid:
        print('Credentials are invalid or expired.')
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)


def get_folder_id(folder_url):
    # Extract folder ID from URL
    if 'folders' in folder_url:
        return folder_url.split('folders/')[1].split('?')[0]
    return None


def process_folder(service, folder_id, output_dir):
    # List all files and folders in the current folder
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        pageSize=1000,
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])

    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            # Create subdirectory for the folder
            subfolder_path = os.path.join(output_dir, item['name'])
            os.makedirs(subfolder_path, exist_ok=True)
            # Recurse into subfolder
            process_folder(service, item['id'], subfolder_path)
        elif item['name'].lower().endswith('.bmp'):
            print(f"Processing {item['name']} in {output_dir}...")
            request = service.files().get_media(fileId=item['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            fh.seek(0)
            with Image.open(fh) as img:
                output_path = os.path.join(output_dir, os.path.splitext(item['name'])[0] + '.tiff')
                img.save(output_path, format='TIFF', compression='none')
            print(f"Saved as {output_path}")

def list_and_convert_files():
    folder_url = input("Please enter Google Drive folder URL: ")
    folder_id = get_folder_id(folder_url)
    if not folder_id:
        print("Invalid folder URL")
        return

    service = get_google_drive_service()

    root = Tk()
    root.withdraw()
    output_dir = filedialog.askdirectory(title='Select Output Directory')
    if not output_dir:
        print('No output directory selected.')
        return

    print("Starting recursive download and conversion...")
    process_folder(service, folder_id, output_dir)


if __name__ == '__main__':
    list_and_convert_files()
