import network
import time
import machine
import urequests
import socket

# WiFi credentials
WIFI_SSID = "iPhone"
WIFI_PASSWORD = "sulimani"

# Server configuration
SERVER_IP = "172.20.10.7"  # Your computer's IP address
SERVER_PORT = 8000

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
        
    def ping(self, url=None, max_retries=3):
        if not self.is_connected:
            print("Cannot ping: Not connected to WiFi")
            return None
            
        # Use default URL if none provided
        if url is None:
            url = f"http://{SERVER_IP}:{SERVER_PORT}/"
            print(f"Using server at: {url}")
            
        for attempt in range(max_retries):
            try:
                print(f"Pinging {url} (attempt {attempt + 1}/{max_retries})...")
                
                # Create a new request with a timeout
                response = urequests.get(url, timeout=5)
                print(f"Response status: {response.status_code}")
                print(f"Response: {response.text}")
                response.close()
                return response.text
                
            except OSError as e:
                if e.errno == 104:  # ECONNRESET
                    print(f"Connection reset by server (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        print("Retrying in 2 seconds...")
                        time.sleep(2)
                    continue
                else:
                    print(f"Network error: {e}")
                    return None
                    
            except Exception as e:
                print(f"Error pinging server: {e}")
                return None
                
        print("All ping attempts failed")
        return None

    def send_image(self, image_bytes, filename="image.jpg", max_retries=3):
        if not self.is_connected:
            print("Cannot send image: Not connected to WiFi")
            return None
            
        url = f"http://{SERVER_IP}:{SERVER_PORT}/send_picture"
        
        for attempt in range(max_retries):
            try:
                print(f"Sending image to {url} (attempt {attempt + 1}/{max_retries})...")
                
                # Prepare the multipart form data
                boundary = "----WebKitFormBoundary"
                headers = {
                    "Content-Type": f"multipart/form-data; boundary={boundary}"
                }
                
                # Construct the multipart form data
                data = b"--" + boundary.encode() + b"\r\n"
                data += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
                data += b"Content-Type: image/jpeg\r\n\r\n"
                data += image_bytes
                data += b"\r\n--" + boundary.encode() + b"--\r\n"
                
                # Send the request
                response = urequests.post(url, data=data, headers=headers, timeout=10)
                print(f"Response status: {response.status_code}")
                print(f"Response: {response.text}")
                response.close()
                return response.text
                
            except OSError as e:
                if e.errno == 104:  # ECONNRESET
                    print(f"Connection reset by server (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        print("Retrying in 2 seconds...")
                        time.sleep(2)
                    continue
                else:
                    print(f"Network error: {e}")
                    return None
                    
            except Exception as e:
                print(f"Error sending image: {e}")
                return None
                
        print("All send attempts failed")
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
    # Try to connect using the working connection method
    return do_connect(WIFI_SSID, WIFI_PASSWORD)

if __name__ == "__main__":
    conn = connect_to_wifi()
    print("Connection status:", conn)
    if conn.is_connected:
        conn.ping() 