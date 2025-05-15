print("START PROGRAM")

from wifi_utils import connect_to_wifi
from utils import debug_print

loop = True
DEBUG = True

#connect to WIFI
conn = connect_to_wifi()

#if conn.is_connected:
    
    # Or specify a different URL
#    conn.send_image(bytes([0,0,1,1]))


while loop:
    
    # here the taking pictures stuff - DAR
    debug_print(DEBUG,"LOOP")
    
    
    
    #here calling to api
    
    

#if here some BUG occured