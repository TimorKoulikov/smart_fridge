import network
import time

# WiFi credentials
WIFI_SSID = "timor_iphone"
WIFI_PASSWORD = "hackthonaiot"
print("in wifi")
def connect_to_wifi():
    # Initialize WiFi
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Connect to WiFi
    print("Connecting to WiFi...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    # Wait for connection with timeout
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print("Waiting for connection...")
        time.sleep(1)

    # Check connection status
    if wlan.status() != 3:
        print("WiFi connection failed!")
        raise RuntimeError("WiFi connection failed")
    else:
        print("Connected to WiFi!")
        print("IP address:", wlan.ifconfig()[0])
        return wlan

if __name__ == "__main__":
    print("in wifi")
    connect_to_wifi() 