from screeninfo import get_monitors
import webview
from wakepy import keep
from .app import app

app_height = int(min([monitor.height for monitor in get_monitors()])*0.8)
app_width = int(min([monitor.width for monitor in get_monitors()])*0.8)
webview.create_window("aTrain",app,height=app_height,width=app_width)
with keep.running():
    webview.start()
