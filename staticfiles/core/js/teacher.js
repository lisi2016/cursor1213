// WebSocket 连接
let socket = null;

function connectWebSocket() {
    // 确定WebSocket URL (使用相对路径)
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/teacher/`;
    
    console.log('正在连接WebSocket:', wsUrl);
    
    try {
        // 创建WebSocket连接
        socket = new WebSocket(wsUrl);
        
        socket.onopen = function(e) {
            console.log("WebSocket 连接已建立");
            updateWebSocketStatus("已连接", "success");
        };
        
        socket.onmessage = function(e) {
            console.log("收到消息:", e.data);
            try {
                const data = JSON.parse(e.data);
                if (data.type === "connection_status") {
                    updateWebSocketStatus(data.message, data.status === "connected" ? "success" : "error");
                } else if (data.type === "student_status") {
                    handleStudentStatus(data.data);
                }
            } catch (error) {
                console.error("解析消息错误:", error);
            }
        };
        
        socket.onclose = function(e) {
            console.log("WebSocket 连接已断开:", e.code, e.reason);
            updateWebSocketStatus(`连接已断开 (${e.code})`, "error");
            
            // 如果不是主动关闭的连接，5秒后尝试重新连接
            if (e.code !== 1000) {
                setTimeout(connectWebSocket, 5000);
            }
        };
        
        socket.onerror = function(e) {
            console.error("WebSocket 错误:", e);
            updateWebSocketStatus("连接错误", "error");
        };
    } catch (error) {
        console.error("创建WebSocket连接时出错:", error);
        updateWebSocketStatus("连接失败", "error");
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

function handleStudentStatus(data) {
    console.log("处理学生状态:", data); // 调试日志
    if (data.action === "login") {
        updateStudentStatus(data);
    } else if (data.action === "logout") {
        removeStudentStatus(data.student_id);
    }
}

function updateStudentStatus(data) {
    const machineGrid = document.querySelector('.machine-grid');
    if (!machineGrid) return;
    
    // 清除"当前没有学生在线"的提示
    if (machineGrid.querySelector('.text-center')) {
        machineGrid.innerHTML = '';
    }
    
    let studentElement = document.getElementById(`student-${data.student_id}`);
    if (!studentElement) {
        studentElement = document.createElement('div');
        studentElement.id = `student-${data.student_id}`;
        studentElement.className = 'machine-item';
        machineGrid.appendChild(studentElement);
    }
    
    studentElement.innerHTML = `
        <div class="student-info">
            <div class="student-name">${data.name}</div>
            <div class="student-id">${data.student_id}</div>
            <div class="student-ip">IP: ${data.ip}</div>
            <div class="login-time">登录: ${data.last_login}</div>
        </div>
    `;
}

function removeStudentStatus(studentId) {
    const studentElement = document.getElementById(`student-${studentId}`);
    if (studentElement) {
        studentElement.remove();
        
        // 检查是否还有其他学生在线
        const machineGrid = document.querySelector('.machine-grid');
        if (machineGrid && !machineGrid.children.length) {
            machineGrid.innerHTML = '<div class="text-center">当前没有学生在线</div>';
        }
    }
}

// 页面加载完成后连接WebSocket
document.addEventListener('DOMContentLoaded', function() {
    console.log("页面加载完成，开始连接WebSocket");
    connectWebSocket();
}); 