import network
import time
import machine
import urequests

# WiFi credentials
WIFI_SSID = "iPhone"
WIFI_PASSWORD = "sulimani"

class WiFiConnection:
    def __init__(self, wlan=None, ip=None, ssid=None, status=None):
        self.wlan = wlan
        self.ip = ip
        self.ssid = ssid
        self.status = status
        self.is_connected = wlan is not None and wlan.isconnected() if wlan else False

    def __str__(self):
        if self.is_connected:
            return f"Connected to {self.ssid} with IP: {self.ip}"
        return f"Not connected. Status: {self.status}"
        
    def ping(self, url="http://localhost:8000/ping"):
        if not self.is_connected:
            print("Cannot ping: Not connected to WiFi")
            return None
            
        try:
            print(f"Pinging {url}...")
            response = urequests.get(url)
            print(f"Response status: {response.status_code}")
            print(f"Response: {response.text}")
            response.close()
            return response.text
        except Exception as e:
            print(f"Error pinging server: {e}")
            return None

def init_wifi():
    print("Initializing WiFi...")
    wlan = network.WLAN(network.STA_IF)
    
    # First deactivate
    wlan.active(False)
    time.sleep(1)
    
    # Then activate
    wlan.active(True)
    time.sleep(2)  # Give it more time to initialize
    
    # Check status
    status = wlan.status()
    print("WiFi status after init:", status)
    
    # Status codes:
    # 1000: STATION_IDLE
    # 1001: STATION_CONNECTING
    # 1010: STATION_GOT_IP
    # 202: STATION_NO_AP_FOUND
    # 201: STATION_CONNECT_FAIL
    # 0: STAT_IDLE
    # 1: STAT_CONNECTING
    # 2: STAT_WRONG_PASSWORD
    # 3: STAT_NO_AP_FOUND
    # 4: STAT_CONNECT_FAIL
    # 5: STAT_GOT_IP
    
    if status == 1001:  # STATION_CONNECTING
        print("WiFi is in connecting state, waiting...")
        time.sleep(5)  # Wait longer for connection
        status = wlan.status()
        print("WiFi status after wait:", status)
    
    return wlan

def scan_networks():
    print("Initializing WiFi for scanning...")
    wlan = init_wifi()
    
    print("Current WiFi status:", wlan.status())
    print("Scanning for networks...")
    
    try:
        networks = wlan.scan()
        if not networks:
            print("No networks found in first scan, retrying...")
            time.sleep(2)
            networks = wlan.scan()
            
        if networks:
            print("\nFound", len(networks), "networks:")
            print("SSID\t\t\tSignal\t\tChannel")
            print("-" * 50)
            for ssid, bssid, channel, rssi, authmode, hidden in networks:
                try:
                    ssid_str = ssid.decode('utf-8')
                    print(f"{ssid_str:<20}\t{rssi} dBm\t\t{channel}")
                except:
                    print(f"<binary ssid>\t\t{rssi} dBm\t\t{channel}")
            print("-" * 50)
        else:
            print("No networks found after retry!")
            print("WiFi status:", wlan.status())
            
    except Exception as e:
        print("Error during scan:", e)
        print("WiFi status:", wlan.status())
        return None
        
    return networks

def do_connect(ssid, password):
    wlan = init_wifi()
    
    # Disconnect if already connected
    if wlan.isconnected():
        print("Already connected, disconnecting first...")
        wlan.disconnect()
        time.sleep(1)
    
    print('Trying to connect to %s...' % ssid)
    try:
        wlan.connect(ssid, password)
    except Exception as e:
        print("Error during connect:", e)
        return WiFiConnection(status=wlan.status())
        
    # Wait for connection with status updates
    max_wait = 20  # 20 seconds timeout
    while max_wait > 0:
        status = wlan.status()
        if status == 1010:  # STATION_GOT_IP
            print('\nConnected successfully!')
            ip = wlan.ifconfig()[0]
            print('Network config:', ip)
            return WiFiConnection(wlan=wlan, ip=ip, ssid=ssid, status=status)
        elif status == 202:  # STATION_NO_AP_FOUND
            print('\nAP not found')
            return WiFiConnection(status=status)
        elif status == 201:  # STATION_CONNECT_FAIL
            print('\nConnection failed')
            return WiFiConnection(status=status)
        elif status == 2:  # STAT_WRONG_PASSWORD
            print('\nWrong password')
            return WiFiConnection(status=status)
            
        max_wait -= 1
        time.sleep(1)
        print('.', end='')
        
    print('\nConnection timeout')
    return WiFiConnection(status=wlan.status())

def connect_to_wifi():
    # First scan for available networks
    networks = scan_networks()
    if not networks:
        print("Could not scan networks, aborting connection attempt")
        return WiFiConnection(status=0)  # STAT_IDLE
        
    # Try to connect using the working connection method
    return do_connect(WIFI_SSID, WIFI_PASSWORD)

if __name__ == "__main__":
    conn = connect_to_wifi()
    print("Connection status:", conn)
    if conn.is_connected:
        conn.ping() 