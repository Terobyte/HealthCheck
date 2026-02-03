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
    gateway=None
    os_type = platform.system()
    try:
            if os_type == "Darwin":  # MAC OS
                output = subprocess.check_output("route -n get default", shell=True, text=True)
                match = re.search(r"gateway:\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", output)
                if match:
                    gateway = match.group(1)

            elif os_type == "Windows":  # WINDOWS
                # Команда 'ipconfig' (нужна кодировка cp866 для русской винды, но cp1252/utf-8 для английской)
                # Мы используем 'chcp 65001' чтобы заставить винду говорить на UTF-8 временно
                command = "chcp 65001 && ipconfig"
                output = subprocess.check_output(command, shell=True, text=True)

                # Ищем "Default Gateway . . . : 1.2.3.4" или "Основной шлюз . . . : 1.2.3.4"
                # Регулярка ищет паттерн IP после слов Gateway/шлюз
                # Мы берем последний найденный IP, так как ipconfig выводит много адаптеров,
                # но активный шлюз обычно имеет IP, а непустые строки
                matches = re.findall(r"(?:Gateway|шлюз).*?:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", output,
                                     re.IGNORECASE)
                if matches:
                    gateway = matches[-1]  # Часто нужный шлюз последний в блоке активного адаптера

    except Exception:
            pass  # Если что-то сломалось, вернем None

    return gateway

def find_real_interface_offline():
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()

    # 1. ЕДИНЫЙ ЧЕРНЫЙ СПИСОК (Объединили всё в кучу)
    # Если название содержит хоть одно из этих слов - в мусорку.
    stop_words = [
        'loopback', 'virtual', 'pseudo', 'tunnel', 'vmware', 'box',  # Windows мусор
        'bluetooth', 'hyper-v', 'wsl',  # Еще Windows
        'utun', 'awdl', 'llw', 'gif', 'stf', 'ap1',  # Mac мусор
        'docker', 'veth', 'br-', 'bridge'  # Linux мусор
    ]

    candidates = []

    for name, stat in stats.items():
        name_lower = name.lower()

        # --- ФИЛЬТР 1: Включен? ---
        if not stat.isup:
            continue

            # --- ФИЛЬТР 2: Точное совпадение (для коротких имен) ---
        # Исключаем 'lo' и 'lo0' (Linux/Mac Loopback), чтобы не фильтровать "Local Area..."
        if name_lower in ['lo', 'lo0']:
            continue

        # --- ФИЛЬТР 3: Поиск стоп-слов ---
        is_junk = False
        for word in stop_words:
            if word in name_lower:
                is_junk = True
                break
        if is_junk:
            continue

        # --- ФИЛЬТР 4: Наличие IP ---
        # Если интерфейс прошел все проверки, проверяем, есть ли у него IP
        if name in addrs:
            for addr in addrs[name]:
                if addr.family == socket.AF_INET:  # IPv4
                    # Дополнительная защита от 127.0.0.1
                    if not addr.address.startswith('127.'):
                        candidates.append({
                            'IP': addr.address,
                            'Interface': name,
                        })
                    break

                    # Возвращаем первого кандидата (обычно это и есть основной)
    return candidates[0] if candidates else None


def ping_host(ip):
    """
    Возвращает True, если IP отвечает.
    Возвращает False, если IP молчит.
    """
    # Определяем параметры для Windows (-n) или Mac/Linux (-c)
    param = '-n' if platform.system().lower() == 'windows' else '-c'

    # Команда: ping -c 1 192.168.1.1
    command = ['ping', param, '1', ip]

    try:
        # check_call запускает команду. Если пинг успешный - возвращает 0 (ОК).
        # stdout=subprocess.DEVNULL скрывает вывод текста в консоль (чтобы не мусорить)
        subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def get_public_data():
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
    Запускает системный пинг и вытаскивает точное время в мс.
    Работает и на Windows, и на Mac.
    """
    host = "8.8.8.8"
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]

    try:
        # Запускаем пинг и ловим его вывод (текст)
        output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode(
            'cp866' if platform.system() == 'Windows' else 'utf-8')

        # Ищем число после "time=" или "время="
        # Регулярка ловит: time=14ms, time=14.5 ms, время=14мс
        match = re.search(r'(?:time|время)[=<]\s*([\d\.]+)', output, re.IGNORECASE)

        if match:
            return float(match.group(1))  # Возвращаем чистое число (например, 14.5)
        else:
            return "N/A"
    except:
        return "Error"


# ... (другие функции выше)

def check_speed():
    """
    Быстрый тест скорости через Cloudflare.
    Добавлена маскировка под браузер (User-Agent) для обхода ошибки 403.
    Добавлен игнор SSL для Mac.
    """
    result = {'Ping': 0, 'Speed_Mbps': 0}

    # 1. ЧЕСТНЫЙ ПИНГ
    result['Ping'] = get_true_ping()

    # 2. ТЕСТ СКОРОСТИ
    try:
        # Настройки для обхода защиты
        url = "https://speed.cloudflare.com/__down?bytes=10485760"  # 10 MB

        # Маскируемся под обычный Chrome на Windows/Mac
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # Игнорируем SSL ошибки (для Mac)
        ssl_context = ssl._create_unverified_context()

        # Создаем запрос с заголовками
        req = urllib.request.Request(url, headers=headers)

        start = time.time()

        # Выполняем запрос
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

        # ЗАПАСНОЙ ВАРИАНТ (Если Cloudflare все равно блокирует)
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
    report={}
    now=datetime.now()
    report["Time"]=now.strftime("%H:%M:%S")
    report['Hostname'] = socket.gethostname()

    report['OS']=platform.system()

    uptimesec=time.time()-psutil.boot_time()
    report["Uptime"]={}
    report["Uptime"]['Hours'] = int(uptimesec // 3600)
    report['Uptime']["Days"] = int((uptimesec // 3600) // 24)
    if report['OS'] == "Windows":
        path = "C://"
    else:
        path = "/System/Volumes/Data" if os.path.exists("/System/Volumes/Data") else "/"
    report['Disk']={
        'Total':round(psutil.disk_usage(path).total/(1024**3),1),
        'Used':round(psutil.disk_usage(path).total/(1024**3)-psutil.disk_usage(path).free/(1024**3),1),
         'Percent':int(psutil.disk_usage(path).percent)

    }
    mem = psutil.virtual_memory()
    report['RAM']={
      "Total":round(mem.total/(1024**3),1),
       "Used":round((mem.total-mem.available)/(1024**3),1),
        "Percent":int(mem.percent)
    }
    report['Network']={}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        report['Network']['Status']=True
        local_ip = s.getsockname()[0]
        report['Network']['IP']=local_ip
        report['Network']['Interface'] = "Unknown"
        addrs = psutil.net_if_addrs()
        for name, addr_list in addrs.items():
            for addr in addr_list:
                # Сравниваем IP интерфейса с тем, который мы получили от сокета
                if addr.address == local_ip:
                    report['Network']['Interface'] = name
                    break  # Нашли! Прерываем внутренний цикл

            # Если нашли (имя уже не Unknown), прерываем внешний цикл
            if report['Network']['Interface'] != "Unknown":
                break


    except OSError:
        report['Network']['Status']=False
        offline_data=find_real_interface_offline()
        if offline_data:
            report['Network'].update(offline_data)
        else:
            report["Network"]["IP"]="Offline"
            report["Network"]["Interface"]="Unknown"
    current_ip = str(report['Network'].get('IP', 'Offline'))
    if current_ip not in ["Offline", "None"]:
        if current_ip.startswith("169.254"):
            report["Network"]['DHCP']=False
        else: report["Network"]['DHCP']=True
    else:
        report["Network"]['DHCP']=False
    if report['Network']["Status"]==False and report['Network']["DHCP"]==True:
        gateway=get_gateway()
        if gateway:
            report["Network"]['Gateway']=gateway
            if ping_host(gateway):
                report['Network']['Gateway_Status'] = True
            else:
                report['Network']['Gateway_Status'] = False
        else:
            report["Network"]['Gateway']='Unknown'
            report["Network"]['Gateway_Status']=False
    else:
        report["Network"]['Gateway']='No Need'
        report["Network"]['Gateway_Status']='No Need'
    if report['Network']["Status"]==True:
        pub_data=(get_public_data())
        if pub_data:
            report['Network']['Public_IP'] = pub_data['IP']
            full_location = f"{pub_data['City']}, {pub_data['State']}, {pub_data['Country']}"
            report['Network']['Location'] = full_location
            report['Network']['ISP'] = pub_data['ISP']
            speed=check_speed()
            report['Network']['Speed'] = speed
        else:
            report['Network']['Public_IP'] = "API Error"
            report['Network']['Location'] = "Unknown"
            report['Network']['ISP'] = "Unknown"
    else:
      report["Network"]['Public_IP']='Unknown'
      report['Network']['Location']='Unknown'
      report["Network"]['ISP']='Unknown'
















    return report

print(quickcheck())
