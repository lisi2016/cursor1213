import socket
import subprocess
from typing import Dict
from .models import User

class MachineMonitor:
    @staticmethod
    def check_machine_status(ip: str, port: int = 80) -> bool:
        try:
            # 尝试 TCP 连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                return True
                
            # 如果 TCP 连接失败，尝试 ping
            ping_result = subprocess.run(
                ['ping', '-n', '1', '-w', '1000', ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return ping_result.returncode == 0
            
        except Exception:
            return False
    
    @classmethod
    def get_all_machines_status(cls) -> Dict[str, bool]:
        students = User.objects.filter(is_teacher=False)
        status_dict = {}
        
        for student in students:
            if student.ip_address:
                status_dict[student.ip_address] = cls.check_machine_status(student.ip_address)
                
        return status_dict 