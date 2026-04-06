# Scout Download Bridge

Load this folder as an unpacked extension in Chrome or Edge:

1. Open `chrome://extensions` or `edge://extensions`
2. Enable `Developer mode`
3. Click `Load unpacked`
4. Select this folder

The extension reports completed PDF downloads to the local Scout bridge at:

`http://127.0.0.1:8765/download-event`

Keep the Scout Streamlit app open while testing so the local bridge stays active.
