function updateMachineStatus() {
    fetch('/api/student-machines/')
        .then(response => response.json())
        .then(data => {
            const machineList = document.querySelector('.machine-list');
            if (data.length === 0) {
                machineList.innerHTML = '<p>当前没有学生在线</p>';
                return;
            }
            
            machineList.innerHTML = data.map(machine => `
                <div class="machine-item">
                    <div class="ip-address">${machine.ip}</div>
                    <div class="student-info">
                        <span class="student-name">${machine.name}</span>
                        <span class="login-time">登录时间: ${machine.login_time}</span>
                    </div>
                </div>
            `).join('');
        });
}

// 每5秒更新一次
setInterval(updateMachineStatus, 5000);

// 页面加载时立即更新一次
document.addEventListener('DOMContentLoaded', updateMachineStatus); 