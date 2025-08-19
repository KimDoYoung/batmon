import platform, socket, uuid, psutil, datetime

def get_system_info():
    info = {}
    # OS / Host
    info["os"] = f"{platform.system()} {platform.release()} ({platform.version()})"
    info["hostname"] = socket.gethostname()
    
    # Network
    info["ip_address"] = socket.gethostbyname(socket.gethostname())
    info["mac_address"] = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                                    for i in range(0, 8*6, 8)][::-1])
    
    # CPU / Memory
    info["cpu"] = platform.processor()
    info["cpu_cores"] = psutil.cpu_count(logical=True)
    info["cpu_usage"] = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    info["memory_total"] = f"{mem.total // (1024**3)} GB"
    info["memory_used"] = f"{mem.used // (1024**3)} GB"
    
    # Disk
    disk = psutil.disk_usage("C:\\")
    info["disk_total"] = f"{disk.total // (1024**3)} GB"
    info["disk_free"] = f"{disk.free // (1024**3)} GB"
    
    # Boot
    info["boot_time"] = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    
    return info

if __name__ == "__main__":
    from pprint import pprint
    pprint(get_system_info())
