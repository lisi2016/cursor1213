console.log('teacher.js 已加载');

let ws = null;
const RECONNECT_TIMEOUT = 5000;

function connectWebSocket() {
    console.log('开始 WebSocket 连接过程...');
    updateWebSocketStatus('正在连接...', 'info');
    
    const host = window.location.host;
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${host}/ws/teacher/`;
    
    console.log('尝试连接 WebSocket URL:', wsUrl);
    
    try {
        if (ws) {
            console.log('关闭现有连接');
            ws.close();
        }
        
        ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            console.log('WebSocket 连接已建立');
            updateWebSocketStatus('已连接', 'success');
        };
        
        ws.onmessage = function(event) {
            console.log('收到 WebSocket 消息:', event.data);
            try {
                const data = JSON.parse(event.data);
                console.log('解析后的数据:', data);
                
                if (data.type === 'student_status' && data.data) {
                    console.log('收到学生状态更新:', data.data);
                    handleStudentStatus(data.data);
                } else {
                    console.log('未知消息类型:', data.type);
                }
            } catch (error) {
                console.error('处理消息时出错:', error);
                console.error('原始消息:', event.data);
            }
        };
        
        ws.onclose = function(event) {
            console.log('WebSocket 连接关闭。代码:', event.code, '原因:', event.reason);
            updateWebSocketStatus('连接已断开', 'error');
            setTimeout(connectWebSocket, 5000);
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket 连接错误:', error);
            updateWebSocketStatus('连接错误', 'error');
        };
        
    } catch (error) {
        console.error('创建 WebSocket 连接失败:', error);
        updateWebSocketStatus('连接失败', 'error');
        setTimeout(connectWebSocket, 5000);
    }
}

function handleInitialStatus(students) {
    console.log('处理初始状态:', students);
    const machineGrid = document.querySelector('.machine-grid');
    if (!machineGrid) return;
    
    machineGrid.innerHTML = '';
    
    if (students.length === 0) {
        machineGrid.innerHTML = '<div class="text-center">当前没有学生在线</div>';
        return;
    }
    
    students.forEach(student => {
        const studentElement = document.createElement('div');
        studentElement.id = `student-${student.student_id}`;
        studentElement.className = 'machine-item';
        studentElement.innerHTML = `
            <div class="student-info">
                <div class="student-name">${student.username}</div>
                <div class="student-id">${student.student_id}</div>
                <div class="student-ip">IP: ${student.ip_address}</div>
                <div class="login-time">登录时间: ${new Date(student.last_login).toLocaleString()}</div>
            </div>
        `;
        machineGrid.appendChild(studentElement);
    });
}

function handleStudentStatus(data) {
    console.log('开始处理学生状态:', data);
    if (!data || !data.action) {
        console.error('无效的学生状态数据:', data);
        return;
    }
    
    const machineGrid = document.querySelector('.machine-grid');
    if (!machineGrid) {
        console.error('找不到 machine-grid 元素');
        return;
    }
    
    try {
        if (data.action === 'login') {
            console.log('处理学生登录:', data);
            updateStudentStatus(data);
        } else if (data.action === 'logout') {
            console.log('处理学生登出:', data);
            removeStudentStatus(data.student_id);
        }
    } catch (error) {
        console.error('处理学生状态时出错:', error);
        console.error('状态数据:', data);
    }
}

function updateStudentStatus(data) {
    const machineGrid = document.querySelector('#machineGrid');
    if (!machineGrid) return;
    
    // 清除"当前没有学生在线"的提示
    if (machineGrid.querySelector('.text-center')) {
        machineGrid.innerHTML = '';
    }
    
    // 添加或更新学生状态
    let studentElement = document.getElementById(`student-${data.student_id}`);
    if (!studentElement) {
        studentElement = document.createElement('div');
        studentElement.id = `student-${data.student_id}`;
        studentElement.className = 'student-card';
        machineGrid.appendChild(studentElement);
    }
    
    studentElement.innerHTML = `
        <div class="student-header">
            <div>
                <div class="student-name">${data.name}</div>
                <div class="student-id">${data.student_id}</div>
            </div>
        </div>
        <div class="info-item">
            <span class="info-icon">🖥️</span>
            <span>${data.ip}</span>
        </div>
        <div class="info-item">
            <span class="info-icon">🕒</span>
            <span>${data.last_login}</span>
        </div>
    `;
}

function updateOnlineCount() {
    const count = document.querySelectorAll('.student-card').length;
    const countElement = document.getElementById('onlineCount');
    if (countElement) {
        countElement.textContent = count;
    }
}

// 搜索功能
document.getElementById('studentSearch').addEventListener('input', function(e) {
    const searchText = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('#machineGrid tr:not(.text-center)');
    
    rows.forEach(row => {
        const name = row.children[0]?.textContent.toLowerCase() || '';
        const id = row.children[1]?.textContent.toLowerCase() || '';
        
        if (name.includes(searchText) || id.includes(searchText)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
});

// 移除学生状态的函数
function removeStudentStatus(studentId) {
    const studentElement = document.getElementById(`student-${studentId}`);
    if (studentElement) {
        studentElement.remove();
        
        const machineGrid = document.querySelector('#machineGrid');
        if (machineGrid && machineGrid.children.length === 0) {
            machineGrid.innerHTML = '<div class="text-center">当前没有学生在线</div>';
        }
    }
}

function updateWebSocketStatus(status, type = 'info') {
    const statusElement = document.getElementById("websocket-status");
    if (statusElement) {
        statusElement.textContent = `WebSocket 状态: ${status}`;
        
        // 更新状态样式
        statusElement.className = 'alert mb-0 py-1';
        switch (type) {
            case 'success':
                statusElement.classList.add('alert-success');
                break;
            case 'error':
                statusElement.classList.add('alert-danger');
                break;
            default:
                statusElement.classList.add('alert-info');
        }
    }
}

// 页面加载时连接WebSocket
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，准备连接WebSocket...');
    connectWebSocket();
}); 