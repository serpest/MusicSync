import sys

from musicsync.musicsync_cli import main as cli_main
from musicsync.musicsync_gui import main as gui_main

if (len(sys.argv) > 1):
    cli_main()
else:
    gui_main()