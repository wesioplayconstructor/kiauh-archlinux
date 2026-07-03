# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APPLICATION_ROOT = Path(__file__).resolve().parent
# insert at position 0 to prevent shadowing by site-packages/utils.py etc.
sys.path.insert(0, str(APPLICATION_ROOT))
