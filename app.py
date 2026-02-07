import streamlit as st
import base64
import requests
from feedgen.feed import FeedGenerator

# --- CONFIGURATION ---
# Store these in Streamlit's "Secrets" management for security
TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "yourusername/my-podcast-storage"
BRANCH = "main"
BASE_URL = f"https://yourusername.github.io/my-podcast-storage"

def get_github_file_sha(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    res = requests.get(url, headers={"Authorization": f"token {TOKEN}"})
    return res.json().get('sha') if res.status_code == 200 else None

def upload_to_github(path, content, message):
    sha = get_github_file_sha(path)
    encoded = base64.b64encode(content).decode("utf-8")
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    payload = {"message": message, "content": encoded, "branch": BRANCH}
    if sha: payload["sha"] = sha
    return requests.put(url, json=payload, headers={"Authorization": f"token {TOKEN}"})

# --- UI ---
st.title("📻 Personal Podcast Hub")
file = st.file_uploader("Upload an MP3", type=["mp3"])

if file and st.button("Publish to Feed"):
    # 1. Upload the MP3
    with st.spinner("Uploading audio..."):
        upload_to_github(f"audio/{file.name}", file.getvalue(), f"Add audio: {file.name}")
    
    # 2. Get all files to rebuild the feed
    with st.spinner("Updating RSS feed..."):
        res = requests.get(f"https://api.github.com/repos/{REPO}/contents/audio", 
                           headers={"Authorization": f"token {TOKEN}"})
        files = res.json()
        
        fg = FeedGenerator()
        fg.load_extension('podcast')
        fg.title('My Personal Audio Sync')
        fg.description('Personal files via Streamlit')
        fg.link(href=BASE_URL, rel='alternate')
        
        for f in files:
            if f['name'].endswith('.mp3'):
                fe = fg.add_entry()
                fe.title(f['name'])
                # Direct link via GitHub Pages
                fe.enclosure(f"{BASE_URL}/audio/{f['name']}", 0, 'audio/mpeg')
        
        # 3. Push the new feed.xml
        upload_to_github("feed.xml", fg.rss_str(), "Update feed.xml")
        st.success("Success! Overcast will pick this up shortly.")
