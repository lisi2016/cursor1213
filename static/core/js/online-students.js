class OnlineStudentsManager {
    constructor() {
        this.studentGrid = document.getElementById('studentGrid');
        this.studentCount = document.getElementById('studentCount');
        this.websocketStatus = document.getElementById('websocket-status');
        this.students = new Map();
        this.initWebSocket();
        
        // Debug log
        console.log('OnlineStudentsManager initialized');
    }

    initWebSocket() {
        const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        this.ws = new WebSocket(`${wsScheme}://${window.location.host}/ws/teacher/`);
        
        this.ws.onopen = () => {
            console.log('WebSocket连接已建立');
            this.updateWebSocketStatus(true);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket连接已断开');
            this.updateWebSocketStatus(false);
            setTimeout(() => this.initWebSocket(), 3000);
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('收到消息:', data);
                
                // 检查消息格式
                if (!data.type) {
                    console.error('消息缺少type字段:', data);
                    return;
                }
                
                if (data.type === 'student_login' && data.student) {
                    console.log('处理学生登录消息:', data.student);
                    this.addStudent(data.student);
                } else {
                    console.log('未处理的消息类型:', data.type);
                }
            } catch (error) {
                console.error('处理消息时出错:', error);
            }
        };
    }

    addStudent(student) {
        console.log('添加学生:', student);
        if (!student.student_id) {
            console.error('学生数据缺少student_id:', student);
            return;
        }
        
        this.students.set(student.student_id, student);
        this.updateDisplay();
    }

    updateDisplay() {
        console.log('更新显示, 当前学生数:', this.students.size);
        if (!this.studentGrid) {
            console.error('找不到studentGrid元素');
            return;
        }
        
        this.studentGrid.innerHTML = '';
        
        if (this.students.size === 0) {
            this.studentGrid.innerHTML = `
                <div class="no-students">
                    <i class="fas fa-user-slash"></i>
                    <p>当前没有在线学生</p>
                </div>
            `;
        } else {
            this.students.forEach(student => {
                const card = this.createStudentCard(student);
                this.studentGrid.appendChild(card);
            });
        }
        
        this.updateStudentCount();
    }

    createStudentCard(student) {
        const card = document.createElement('div');
        card.className = 'student-card';
        card.id = `student-${student.student_id}`;
        
        // 使用模板字符串创建卡片内容
        card.innerHTML = `
            <div class="student-info">
                <div class="student-name">${student.name || '未知姓名'}</div>
                <div class="student-id">学号：${student.student_id}</div>
                <div class="student-ip">IP：${student.ip || '未知IP'}</div>
                <div class="login-time">登录时间：${student.login_time || '未知时间'}</div>
            </div>
        `;
        
        console.log('创建学生卡片:', student.student_id);
        return card;
    }

    updateStudentCount() {
        if (this.studentCount) {
            this.studentCount.textContent = this.students.size;
            console.log('更新学生计数:', this.students.size);
        }
    }

    updateWebSocketStatus(connected) {
        if (this.websocketStatus) {
            this.websocketStatus.className = `websocket-status ${connected ? 'websocket-connected' : 'websocket-disconnected'}`;
            this.websocketStatus.innerHTML = `
                <i class="fas fa-${connected ? 'signal' : 'exclamation-triangle'}"></i>
                ${connected ? '连接正常' : '连接断开'}
            `;
        }
    }
}

// 确保在页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('页面加载完成，初始化OnlineStudentsManager');
    window.onlineStudentsManager = new OnlineStudentsManager();
}); 