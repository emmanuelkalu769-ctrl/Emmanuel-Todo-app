"""Start Little List and open your browser once the server is ready."""
from pathlib import Path
import threading
import time
import urllib.request
import webbrowser
import uvicorn

URL = 'http://127.0.0.1:8000'
def open_browser():
    for _ in range(60):
        try:
            with urllib.request.urlopen(URL+'/api/items',timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(URL)
                    return
        except Exception:
            time.sleep(0.5)

if __name__ == '__main__':
    if not (Path(__file__).parent/'frontend'/'dist'/'index.html').exists():
        raise SystemExit('The frontend build is missing. See README.md for build instructions.')
    print('Little List is starting. Keep this window open. Press Ctrl+C to stop.')
    threading.Thread(target=open_browser,daemon=True).start()
    uvicorn.run('backend.main:app',host='127.0.0.1',port=8000)
