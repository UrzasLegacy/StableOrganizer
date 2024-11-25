#############################################################################################################################################
#                              ________  ___________   __       _______   ___       _______                                                 #
#                             /"       )("     _   ") /""\     |   _  "\ |"  |     /"     "|                                                #
#                            (:   \___/  )__/  \\__/ /    \    (. |_)  :)||  |    (: ______)                                                #
#                             \___  \       \\_ /   /' /\  \   |:     \/ |:  |     \/    |                                                  #
#                              __/  \\      |.  |  //  __'  \  (|  _  \\  \  |___  // ___)_                                                 #
#                             /" \   :)     \:  | /   /  \\  \ |: |_)  :)( \_|:  \(:      "|                                                #
#                            (_______/       \__|(___/    \___)(_______/  \_______)\_______)                                                #
#                                              ._______  .______  ._____  .______  .______  .___ .______ ._______.______                    #
#                                              : .___  \ : __   \ :_ ___\ :      \ :      \ : __|\____  |: .____/: __   \                   #
#                                              | :   |  ||  \____||   |___|   .   ||       || : |/  ____|| : _/\ |  \____|                  #
#                                              |     :  ||   :  \ |   /  ||   :   ||   |   ||   |\      ||   /  \|   :  \                   #
#                                               \_. ___/ |   |___\|. __  ||___|   ||___|   ||   | \__:__||_.: __/|   |___\   v0.7           #
#                                                 :/     |___|     :/ |. |    |___|    |___||___|    :      :/   |___|                      #
#                                                 :                :   :/                            •                                      #
#                                                                                                                                           #
#                                                                                                                         By: UrzasLegacy   #
#############################################################################################################################################

import os
import logging
import tkinter as tk

from GUI import StableOrganizerApp


ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

log_file_path = os.path.join(ROOT_DIRECTORY, "debugging.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    root = tk.Tk()
    app = StableOrganizerApp(root)
    root.mainloop()