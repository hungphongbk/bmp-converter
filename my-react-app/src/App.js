import React, { useState } from 'react';

const CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || 'YOUR_GOOGLE_CLIENT_ID';
const API_KEY = process.env.REACT_APP_API_KEY;
const SCOPES = 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.file';

function App() {
    const [isSignedIn, setIsSignedIn] = useState(false);
    const [sourceFolder, setSourceFolder] = useState(null);
    const [destFolder, setDestFolder] = useState(null);
    const [status, setStatus] = useState('');

    // Load Google API
    React.useEffect(() => {
      window.gapi.load('client:auth2', () => {
        window.gapi.client.init({
          apiKey: API_KEY,
          clientId: CLIENT_ID,
          scope: SCOPES,
          discoveryDocs: ['https://www.googleapis.com/discovery/v1/apis/drive/v3/rest'],
        }).then(() => {
          setIsSignedIn(window.gapi.auth2.getAuthInstance().isSignedIn.get());
        });
      });
    }, []);

    const signIn = () => {
      window.gapi.auth2.getAuthInstance().signIn().then(() => {
        setIsSignedIn(true);
      });
    };

    const pickFolder = async (setFolder) => {
      const picker = new window.google.picker.PickerBuilder()
        .addView(window.google.picker.ViewId.FOLDERS)
        .setOAuthToken(window.gapi.auth.getToken().access_token)
        .setDeveloperKey(API_KEY)
        .setCallback((data) => {
          if (data.action === window.google.picker.Action.PICKED) {
            setFolder(data.docs[0]);
          }
        })
        .build();
      picker.setVisible(true);
    };

    const handleTransform = async () => {
      setStatus('Processing...');
      const res = await fetch('/api/drive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_url: `https://drive.google.com/drive/folders/${sourceFolder.id}`,
          dest_folder_id: destFolder.id,
          access_token: window.gapi.auth.getToken().access_token,
        }),
      });
      if (res.ok) setStatus('Success! Images are in your destination folder.');
      else setStatus('Error processing images.');
    };

    return (
      <div>
        {!isSignedIn && <button onClick={signIn}>Sign in with Google</button>}
        {isSignedIn && (
          <div>
            <button onClick={() => pickFolder(setSourceFolder)}>
              Choose Source Folder
            </button>
            {sourceFolder && <span>Source: {sourceFolder.name}</span>}
            <br />
            <button onClick={() => pickFolder(setDestFolder)}>
              Choose Destination Folder
            </button>
            {destFolder && <span>Destination: {destFolder.name}</span>}
            <br />
            {sourceFolder && destFolder && (
              <button onClick={handleTransform}>Transform Images</button>
            )}
            <div>{status}</div>
          </div>
        )}
      </div>
    );
}

export default App;