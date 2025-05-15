print("START PROGRAM")

from wifi_connect import connect_to_wifi
from utils import debug_print

loop = True
DEBUG = True

#connect to WIFI
conn = connect_to_wifi()

if conn.is_connected:
    # Use default URL (localhost:8000/ping)
    conn.ping()
    
    # Or specify a different URL
    conn.ping("http://192.168.1.100:8000/ping")

#while loop:
    
    # here the taking pictures stuff - DAR
#    debug_print(DEBUG,"LOOP")
    
    
    
    #here calling to api
    
    

#if here some BUG occured