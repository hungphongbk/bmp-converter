from flask import Flask, request, send_file, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image
import pickle
import os
import io
import zipfile
from datetime import datetime

app = Flask(__name__)
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_google_drive_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def get_folder_id(folder_url):
    if 'folders' in folder_url:
        return folder_url.split('folders/')[1].split('?')[0]
    return None

def collect_images(service, folder_id):
    images = []
    def process_folder(fid, path_prefix=''):
        results = service.files().list(
            q=f"'{fid}' in parents and trashed = false",
            pageSize=1000,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        items = results.get('files', [])
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                process_folder(item['id'], os.path.join(path_prefix, item['name']))
            elif item['name'].lower().endswith('.bmp'):
                request = service.files().get_media(fileId=item['id'])
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                fh.seek(0)
                img = Image.open(fh)
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='TIFF', compression='none')
                img_bytes.seek(0)
                zip_path = os.path.join(path_prefix, os.path.splitext(item['name'])[0] + '.tiff')
                images.append((zip_path, img_bytes.read()))
    process_folder(folder_id)
    return images

@app.route('/api/drive', methods=['POST'])
def drive_zip():
    data = request.get_json()
    folder_url = data.get('folder_url')
    folder_id = get_folder_id(folder_url)
    if not folder_id:
        return jsonify({'error': 'Invalid folder URL'}), 400
    service = get_google_drive_service()
    images = collect_images(service, folder_id)
    if not images:
        return jsonify({'error': 'No BMP images found'}), 404
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename, filedata in images:
            zipf.writestr(filename, filedata)
    zip_buffer.seek(0)
    zip_name = datetime.now().strftime('%d-%m-%Y.zip')
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_name
    )

if __name__ == '__main__':
    app.run(port=5000)