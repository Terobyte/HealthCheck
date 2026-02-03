import psutil
import socket
import ssl
import platform
import os
import time
import subprocess
import re
from datetime import datetime
import urllib.request
import json

def get_gateway():
    """
    Get the default gateway IP address.
    Works on both Windows and macOS.
    """
    gateway = None
    os_type = platform.system()
    try:
        if os_type == "Darwin":  # MAC OS
            output = subprocess.check_output("route -n get default", shell=True, text=True)
            match = re.search(r"gateway:\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", output)
            if match:
                gateway = match.group(1)

        elif os_type == "Windows":  # WINDOWS
            # The 'ipconfig' command (needs cp866 encoding for Russian Windows, but cp1252/utf-8 for English)
            # We use 'chcp 65001' to force Windows to speak UTF-8 temporarily
            command = "chcp 65001 && ipconfig"
            output = subprocess.check_output(command, shell=True, text=True)

            # Search for "Default Gateway . . . : 1.2.3.4" or "Основной шлюз . . . : 1.2.3.4"
            # Regex finds IP pattern after Gateway/шлюз words
            # We take the last found IP, as ipconfig outputs many adapters,
            # but the active gateway usually has an IP
            matches = re.findall(r"(?:Gateway|шлюз).*?:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", output,
                                 re.IGNORECASE)
            if matches:
                gateway = matches[-1]  # Often the needed gateway is last in the active adapter block

    except Exception:
        pass  # If something breaks, return None

    return gateway

def find_real_interface_offline():
    """
    Find the real network interface when offline.
    Filters out virtual, loopback, and other non-physical interfaces.
    """
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()

    # 1. UNIFIED BLACKLIST (Combined everything)
    # If the name contains any of these words - discard it.
    stop_words = [
        'loopback', 'virtual', 'pseudo', 'tunnel', 'vmware', 'box',  # Windows junk
        'bluetooth', 'hyper-v', 'wsl',  # More Windows
        'utun', 'awdl', 'llw', 'gif', 'stf', 'ap1',  # Mac junk
        'docker', 'veth', 'br-', 'bridge'  # Linux junk
    ]

    candidates = []

    for name, stat in stats.items():
        name_lower = name.lower()

        # --- FILTER 1: Is it up? ---
        if not stat.isup:
            continue

        # --- FILTER 2: Exact match (for short names) ---
        # Exclude 'lo' and 'lo0' (Linux/Mac Loopback) to avoid filtering "Local Area..."
        if name_lower in ['lo', 'lo0']:
            continue

        # --- FILTER 3: Search for stop words ---
        is_junk = False
        for word in stop_words:
            if word in name_lower:
                is_junk = True
                break
        if is_junk:
            continue

        # --- FILTER 4: Has IP? ---
        # If interface passed all checks, check if it has an IP
        if name in addrs:
            for addr in addrs[name]:
                if addr.family == socket.AF_INET:  # IPv4
                    # Extra protection against 127.0.0.1
                    if not addr.address.startswith('127.'):
                        candidates.append({
                            'IP': addr.address,
                            'Interface': name,
                        })
                    break

                    # Return first candidate (usually the main one)
    return candidates[0] if candidates else None


def ping_host(ip):
    """
    Returns True if IP responds.
    Returns False if IP is silent.
    """
    # Determine parameters for Windows (-n) or Mac/Linux (-c)
    param = '-n' if platform.system().lower() == 'windows' else '-c'

    # Command: ping -c 1 192.168.1.1
    command = ['ping', param, '1', ip]

    try:
        # check_call runs the command. If ping is successful - returns 0 (OK).
        # stdout=subprocess.DEVNULL hides text output to console (to avoid clutter)
        subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def get_public_data():
    """
    Get public IP and location data from ip-api.com
    """
    try:
        with urllib.request.urlopen("http://ip-api.com/json/", timeout=3) as url:
            data = json.loads(url.read().decode())
            return {
                'IP': data.get('query', 'Unknown'),
                'City': data.get('city', 'Unknown'),
                'State': data.get('regionName', 'Unknown'),
                'Country': data.get('country', 'Unknown'),
                'ISP': data.get('isp', 'Unknown')
            }
    except:
        return None


def get_true_ping():
    """
    Run system ping and extract exact time in ms.
    Works on both Windows and Mac.
    """
    host = "8.8.8.8"
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]

    try:
        # Run ping and capture its output (text)
        output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode(
            'cp866' if platform.system() == 'Windows' else 'utf-8')

        # Search for number after "time=" or "время="
        # Regex catches: time=14ms, time=14.5 ms, время=14мс
        match = re.search(r'(?:time|время)[=<]\s*([\d\.]+)', output, re.IGNORECASE)

        if match:
            return float(match.group(1))  # Return pure number (e.g., 14.5)
        else:
            return "N/A"
    except:
        return "Error"


def check_speed():
    """
    Quick speed test via Cloudflare.
    Added browser masking (User-Agent) to bypass 403 error.
    Added SSL ignore for Mac.
    """
    result = {'Ping': 0, 'Speed_Mbps': 0}

    # 1. REAL PING
    result['Ping'] = get_true_ping()

    # 2. SPEED TEST
    try:
        # Settings to bypass protection
        url = "https://speed.cloudflare.com/__down?bytes=10485760"  # 10 MB

        # Mask as regular Chrome on Windows/Mac
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # Ignore SSL errors (for Mac)
        ssl_context = ssl._create_unverified_context()

        # Create request with headers
        req = urllib.request.Request(url, headers=headers)

        start = time.time()

        # Execute request
        with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
            data = resp.read()
            size = len(data)

        duration = time.time() - start

        if duration > 0.1:
            speed_mbps = (size * 8) / (1024 * 1024) / duration
            result['Speed_Mbps'] = round(speed_mbps, 2)
        else:
            result['Speed_Mbps'] = "> 1000"

    except Exception as e:
        print(f"Cloudflare Speedtest Error: {e}")

        # BACKUP OPTION (If Cloudflare still blocks)
        try:
            print("Trying backup server...")
            url_backup = "http://ipv4.download.thinkbroadband.com/10MB.zip"
            start = time.time()
            with urllib.request.urlopen(url_backup, timeout=20) as resp:
                size = len(resp.read())
            duration = time.time() - start
            result['Speed_Mbps'] = round((size * 8) / (1024 * 1024) / duration, 2)
        except Exception as e2:
            print(f"Backup Error: {e2}")
            result['Speed_Mbps'] = "Error"

    return result

def quickcheck():
    """
    Perform quick system check and generate report.
    """
    report = {}
    now = datetime.now()
    report["Time"] = now.strftime("%H:%M:%S")
    report['Hostname'] = socket.gethostname()

    report['OS'] = platform.system()

    uptimesec = time.time() - psutil.boot_time()
    report["Uptime"] = {}
    report["Uptime"]['Hours'] = int(uptimesec // 3600)
    report['Uptime']["Days"] = int((uptimesec // 3600) // 24)
    
    if report['OS'] == "Windows":
        path = "C://"
    else:
        path = "/System/Volumes/Data" if os.path.exists("/System/Volumes/Data") else "/"
        
    report['Disk'] = {
        'Total': round(psutil.disk_usage(path).total/(1024**3), 1),
        'Used': round(psutil.disk_usage(path).total/(1024**3)-psutil.disk_usage(path).free/(1024**3), 1),
         'Percent': int(psutil.disk_usage(path).percent)
    }
    
    mem = psutil.virtual_memory()
    report['RAM'] = {
      "Total": round(mem.total/(1024**3), 1),
       "Used": round((mem.total-mem.available)/(1024**3), 1),
        "Percent": int(mem.percent)
    }
    
    report['Network'] = {}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        report['Network']['Status'] = True
        local_ip = s.getsockname()[0]
        report['Network']['IP'] = local_ip
        report['Network']['Interface'] = "Unknown"
        addrs = psutil.net_if_addrs()
        for name, addr_list in addrs.items():
            for addr in addr_list:
                # Compare interface IP with the one we got from socket
                if addr.address == local_ip:
                    report['Network']['Interface'] = name
                    break  # Found! Break inner loop

            # If found (name is not Unknown), break outer loop
            if report['Network']['Interface'] != "Unknown":
                break

    except OSError:
        report['Network']['Status'] = False
        offline_data = find_real_interface_offline()
        if offline_data:
            report['Network'].update(offline_data)
        else:
            report["Network"]["IP"] = "Offline"
            report["Network"]["Interface"] = "Unknown"
            
    current_ip = str(report['Network'].get('IP', 'Offline'))
    if current_ip not in ["Offline", "None"]:
        if current_ip.startswith("169.254"):
            report["Network"]['DHCP'] = False
        else: 
            report["Network"]['DHCP'] = True
    else:
        report["Network"]['DHCP'] = False
        
    if report['Network']["Status"] == False and report['Network']["DHCP"] == True:
        gateway = get_gateway()
        if gateway:
            report["Network"]['Gateway'] = gateway
            if ping_host(gateway):
                report['Network']['Gateway_Status'] = True
            else:
                report['Network']['Gateway_Status'] = False
        else:
            report["Network"]['Gateway'] = 'Unknown'
            report["Network"]['Gateway_Status'] = False
    else:
        report["Network"]['Gateway'] = 'No Need'
        report["Network"]['Gateway_Status'] = 'No Need'
        
    if report['Network']["Status"] == True:
        pub_data = get_public_data()
        if pub_data:
            report['Network']['Public_IP'] = pub_data['IP']
            full_location = f"{pub_data['City']}, {pub_data['State']}, {pub_data['Country']}"
            report['Network']['Location'] = full_location
            report['Network']['ISP'] = pub_data['ISP']
            speed = check_speed()
            report['Network']['Speed'] = speed
        else:
            report['Network']['Public_IP'] = "API Error"
            report['Network']['Location'] = "Unknown"
            report['Network']['ISP'] = "Unknown"
    else:
        report["Network"]['Public_IP'] = 'Unknown'
        report['Network']['Location'] = 'Unknown'
        report["Network"]['ISP'] = 'Unknown'

    return report

# Test code (commented out in production)
# print(quickcheck())