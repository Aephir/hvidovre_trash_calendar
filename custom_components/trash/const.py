

DOMAIN = "trash"
URL = "https://hvidovre.renoweb.dk/Legacy/selvbetjening/mit_affald.aspx"

ATTR_ADDR = "address"
ATTR_LAST_UPDATE = "last_updated"
ATTR_NEXT_PICKUP = "next_pickup"  # Do date as state. Have trash types in ATTR
ATTR_TRASH_DATES = "trash_pickup_dates"
STARTUP = """
 _   _            _       _
| | | |          |_|     | |
| |_| |  _     _  _    __| |   __    _    _   _  __     _____
|  _  | \ \  / / | | /  _  | /  _ \ \ \  / / | `´__`| / /__\_\ 
| | | |  \ \/ /  | | | |_| | | |_| | \ \/ /  | |      | |_____
|_| |_|   \__/   |_|  \____|  \___/   \__/   |_|       \_____/

 ____                                                    _     _
|  _  \                                                 | |   |_|
| |_| /    –––––   _  __      __    _    _   ____  _   _| |_   _    __    _  __  
|  _ \   / /__\_\ | '´–  \  /  _ \ \ \  / / /  _ `| | |_   _| | | /  _ \ | '´–  \ 
| | \ \  | |_____ | |  | |  | |_| | \ \/ /  | |_|   |   | |_  | | | |_| || |  | | 
|_|  \_\  \_____/ |_|  |_|   \___/   \__/    \___/|_|   \__/  |_|  \___/ |_|  |_|

Hvidovre Renovations Affaldskalender integration, version: %s
This is a custom integration
If you have any issues with this you need to open an issue here:
https://github.com/Aephir/HvidovreAffaldskalender/issues
-----------------------------------------------------------------
"""