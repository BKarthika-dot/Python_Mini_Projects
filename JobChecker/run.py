"""Start the backend and open the UI: python run.py"""
import threading, time, urllib.request, webbrowser
import uvicorn

HOST, PORT = "127.0.0.1", 8000


def _open_when_ready():
    for _ in range(120):  # first start may train the model; wait up to ~2 min
        try:
            urllib.request.urlopen(f"http://{HOST}:{PORT}/health", timeout=1)
            webbrowser.open(f"http://{HOST}:{PORT}")
            return
        except Exception:
            time.sleep(1)


if __name__ == "__main__":
    threading.Thread(target=_open_when_ready, daemon=True).start()
    uvicorn.run("app.main:app", host=HOST, port=PORT)
