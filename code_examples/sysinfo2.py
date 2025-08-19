import platform
import socket
import uuid
import psutil
import datetime
import json
import argparse
import sys
import os

class SystemInfoCollector:
    def __init__(self):
        self.info = {}
    
    def get_basic_info(self):
        """기본 시스템 정보 수집"""
        try:
            self.info["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.info["python_version"] = platform.python_version()
            
            # OS 정보
            self.info["os"] = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "architecture": platform.architecture()[0],
                "platform": platform.platform()
            }
            
            # 호스트 정보
            self.info["hostname"] = socket.gethostname()
            
        except Exception as e:
            self.info["basic_info_error"] = str(e)
    
    def get_network_info(self):
        """네트워크 정보 수집"""
        try:
            # IP 주소
            self.info["network"] = {}
            self.info["network"]["local_ip"] = socket.gethostbyname(socket.gethostname())
            
            # MAC 주소
            mac_num = uuid.getnode()
            mac_hex = '{:012x}'.format(mac_num)
            self.info["network"]["mac_address"] = ':'.join(mac_hex[i:i+2] for i in range(0, 12, 2))
            
            # 네트워크 인터페이스 정보
            if hasattr(psutil, 'net_if_addrs'):
                interfaces = {}
                for interface_name, interface_addresses in psutil.net_if_addrs().items():
                    addresses = []
                    for address in interface_addresses:
                        addresses.append({
                            'family': str(address.family),
                            'address': address.address,
                            'netmask': address.netmask,
                            'broadcast': address.broadcast
                        })
                    interfaces[interface_name] = addresses
                self.info["network"]["interfaces"] = interfaces
            
        except Exception as e:
            self.info["network_error"] = str(e)
    
    def get_cpu_info(self):
        """CPU 정보 수집"""
        try:
            self.info["cpu"] = {
                "processor": platform.processor(),
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "current_frequency": psutil.cpu_freq().current if psutil.cpu_freq() else "N/A",
                "max_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else "N/A",
                "min_frequency": psutil.cpu_freq().min if psutil.cpu_freq() else "N/A",
                "usage_percent": psutil.cpu_percent(interval=1),
                "usage_per_core": psutil.cpu_percent(interval=1, percpu=True)
            }
        except Exception as e:
            self.info["cpu_error"] = str(e)
    
    def get_memory_info(self):
        """메모리 정보 수집"""
        try:
            # 가상 메모리
            mem = psutil.virtual_memory()
            self.info["memory"] = {
                "virtual": {
                    "total_gb": round(mem.total / (1024**3), 2),
                    "available_gb": round(mem.available / (1024**3), 2),
                    "used_gb": round(mem.used / (1024**3), 2),
                    "percentage": mem.percent
                }
            }
            
            # 스왑 메모리
            swap = psutil.swap_memory()
            self.info["memory"]["swap"] = {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "free_gb": round(swap.free / (1024**3), 2),
                "percentage": swap.percent
            }
        except Exception as e:
            self.info["memory_error"] = str(e)
    
    def get_disk_info(self):
        """디스크 정보 수집"""
        try:
            self.info["disks"] = []
            
            # 모든 디스크 파티션 검사
            for partition in psutil.disk_partitions():
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    disk_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "filesystem": partition.fstype,
                        "total_gb": round(partition_usage.total / (1024**3), 2),
                        "used_gb": round(partition_usage.used / (1024**3), 2),
                        "free_gb": round(partition_usage.free / (1024**3), 2),
                        "percentage": round((partition_usage.used / partition_usage.total) * 100, 1)
                    }
                    self.info["disks"].append(disk_info)
                except PermissionError:
                    # 일부 시스템 파티션은 접근 권한이 없을 수 있음
                    continue
            
            # 디스크 I/O 통계
            if hasattr(psutil, 'disk_io_counters'):
                io_counters = psutil.disk_io_counters()
                if io_counters:
                    self.info["disk_io"] = {
                        "read_count": io_counters.read_count,
                        "write_count": io_counters.write_count,
                        "read_bytes": io_counters.read_bytes,
                        "write_bytes": io_counters.write_bytes
                    }
        except Exception as e:
            self.info["disk_error"] = str(e)
    
    def get_system_stats(self):
        """시스템 통계 정보"""
        try:
            self.info["system_stats"] = {
                "boot_time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
                "uptime": str(datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())).split('.')[0]
            }
            
            # 로드 애버리지 (Linux/macOS)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                self.info["system_stats"]["load_average"] = {
                    "1min": load_avg[0],
                    "5min": load_avg[1],
                    "15min": load_avg[2]
                }
        except Exception as e:
            self.info["system_stats_error"] = str(e)
    
    def get_process_info(self):
        """프로세스 정보"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # CPU 사용량 기준 상위 5개 프로세스
            top_cpu = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:5]
            # 메모리 사용량 기준 상위 5개 프로세스
            top_memory = sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)[:5]
            
            self.info["processes"] = {
                "total_count": len(processes),
                "top_cpu_usage": top_cpu,
                "top_memory_usage": top_memory
            }
        except Exception as e:
            self.info["process_error"] = str(e)
    
    def get_battery_info(self):
        """배터리 정보 (노트북의 경우)"""
        try:
            if hasattr(psutil, 'sensors_battery'):
                battery = psutil.sensors_battery()
                if battery:
                    self.info["battery"] = {
                        "percentage": battery.percent,
                        "plugged_in": battery.power_plugged,
                        "time_left": str(datetime.timedelta(seconds=battery.secsleft)) if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Unlimited"
                    }
        except Exception as e:
            self.info["battery_error"] = str(e)
    
    def collect_all_info(self):
        """모든 시스템 정보 수집"""
        print("시스템 정보를 수집하는 중...")
        
        self.get_basic_info()
        self.get_network_info()
        self.get_cpu_info()
        self.get_memory_info()
        self.get_disk_info()
        self.get_system_stats()
        self.get_process_info()
        self.get_battery_info()
        
        return self.info
    
    def save_to_file(self, filename, format_type='json'):
        """정보를 파일로 저장"""
        try:
            if format_type.lower() == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.info, f, indent=2, ensure_ascii=False)
            elif format_type.lower() == 'txt':
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.format_output())
            print(f"시스템 정보가 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"파일 저장 중 오류 발생: {e}")
    
    def format_output(self):
        """사람이 읽기 쉬운 형태로 출력 포맷"""
        output = []
        output.append("="*60)
        output.append("시스템 정보 보고서")
        output.append("="*60)
        output.append(f"수집 시간: {self.info.get('timestamp', 'N/A')}")
        output.append("")
        
        # 기본 정보
        if "os" in self.info:
            output.append("📋 운영체제 정보")
            output.append(f"  시스템: {self.info['os']['system']}")
            output.append(f"  릴리즈: {self.info['os']['release']}")
            output.append(f"  아키텍처: {self.info['os']['architecture']}")
            output.append(f"  호스트명: {self.info.get('hostname', 'N/A')}")
            output.append("")
        
        # CPU 정보
        if "cpu" in self.info:
            output.append("🖥️ CPU 정보")
            output.append(f"  프로세서: {self.info['cpu']['processor']}")
            output.append(f"  물리 코어: {self.info['cpu']['physical_cores']}")
            output.append(f"  논리 코어: {self.info['cpu']['logical_cores']}")
            output.append(f"  현재 사용률: {self.info['cpu']['usage_percent']}%")
            output.append("")
        
        # 메모리 정보
        if "memory" in self.info:
            mem = self.info['memory']['virtual']
            output.append("💾 메모리 정보")
            output.append(f"  총 메모리: {mem['total_gb']} GB")
            output.append(f"  사용 중: {mem['used_gb']} GB ({mem['percentage']}%)")
            output.append(f"  사용 가능: {mem['available_gb']} GB")
            output.append("")
        
        # 디스크 정보
        if "disks" in self.info:
            output.append("💿 디스크 정보")
            for disk in self.info['disks']:
                output.append(f"  장치: {disk['device']}")
                output.append(f"    총 용량: {disk['total_gb']} GB")
                output.append(f"    사용 중: {disk['used_gb']} GB ({disk['percentage']}%)")
                output.append(f"    여유 공간: {disk['free_gb']} GB")
            output.append("")
        
        # 네트워크 정보
        if "network" in self.info:
            output.append("🌐 네트워크 정보")
            output.append(f"  로컬 IP: {self.info['network'].get('local_ip', 'N/A')}")
            output.append(f"  MAC 주소: {self.info['network'].get('mac_address', 'N/A')}")
            output.append("")
        
        # 시스템 통계
        if "system_stats" in self.info:
            stats = self.info['system_stats']
            output.append("📊 시스템 통계")
            output.append(f"  부팅 시간: {stats.get('boot_time', 'N/A')}")
            output.append(f"  가동 시간: {stats.get('uptime', 'N/A')}")
            output.append("")
        
        # 배터리 정보
        if "battery" in self.info:
            battery = self.info['battery']
            output.append("🔋 배터리 정보")
            output.append(f"  충전량: {battery['percentage']}%")
            output.append(f"  전원 연결: {'예' if battery['plugged_in'] else '아니오'}")
            output.append(f"  남은 시간: {battery['time_left']}")
            output.append("")
        
        return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(description='시스템 정보 수집 도구')
    parser.add_argument('-o', '--output', help='출력 파일명')
    parser.add_argument('-f', '--format', choices=['json', 'txt'], default='txt', 
                       help='출력 형식 (기본값: txt)')
    parser.add_argument('-v', '--verbose', action='store_true', help='상세 정보 출력')
    
    args = parser.parse_args()
    
    # 시스템 정보 수집
    collector = SystemInfoCollector()
    info = collector.collect_all_info()
    
    # 화면에 출력
    if args.verbose:
        print(collector.format_output())
    else:
        print("시스템 정보 수집 완료!")
        print(f"OS: {info.get('os', {}).get('system', 'N/A')} {info.get('os', {}).get('release', '')}")
        print(f"CPU: {info.get('cpu', {}).get('usage_percent', 'N/A')}% 사용 중")
        print(f"메모리: {info.get('memory', {}).get('virtual', {}).get('percentage', 'N/A')}% 사용 중")
    
    # 파일 저장
    if args.output:
        collector.save_to_file(args.output, args.format)
    
    return info

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)