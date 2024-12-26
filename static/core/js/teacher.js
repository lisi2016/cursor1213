console.log('teacher.js 已加载');

class TeacherDashboard {
    constructor() {
        this.studentGrid = document.getElementById('studentGrid');
        this.studentCount = document.getElementById('studentCount');
        this.wsStatus = document.getElementById('websocket-status');
        this.students = new Map();
        
        this.initWebSocket();
        console.log('TeacherDashboard initialized');
    }

    initWebSocket() {
        const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${wsScheme}://${window.location.host}/ws/teacher/`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateStatus('已连接', 'connected');
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateStatus('已断开', 'disconnected');
            setTimeout(() => this.initWebSocket(), 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateStatus('连接错误', 'error');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Received message:', data);
                
                if (data.type === 'student_login' && data.student) {
                    this.handleStudentLogin(data.student);
                }
            } catch (error) {
                console.error('Error processing message:', error);
            }
        };
    }

    handleStudentLogin(student) {
        console.log('Processing student login:', student);
        
        // 更新学生列表
        this.students.set(student.student_id, student);
        this.updateDisplay();
    }

    updateDisplay() {
        if (!this.studentGrid) {
            console.error('Student grid not found');
            return;
        }

        // 清空现有内容
        this.studentGrid.innerHTML = '';

        if (this.students.size === 0) {
            this.studentGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users fa-3x"></i>
                    <p>当前没有在线学生</p>
                </div>
            `;
        } else {
            this.students.forEach(student => {
                const card = this.createStudentCard(student);
                this.studentGrid.appendChild(card);
            });
        }

        // 更新学生数量
        if (this.studentCount) {
            this.studentCount.textContent = this.students.size;
        }
    }

    createStudentCard(student) {
        const card = document.createElement('div');
        card.className = 'student-card';
        card.id = `student-${student.student_id}`;
        
        card.innerHTML = `
            <div class="student-info">
                <div class="student-name">
                    <i class="fas fa-user"></i>
                    ${student.name || '未知姓名'}
                </div>
                <div class="student-id">
                    <i class="fas fa-id-card"></i>
                    学号：${student.student_id}
                </div>
                <div class="student-ip">
                    <i class="fas fa-network-wired"></i>
                    IP：${student.ip || '未知IP'}
                </div>
                <div class="login-time">
                    <i class="fas fa-clock"></i>
                    登录时间：${student.login_time || '未知时间'}
                </div>
            </div>
        `;
        
        return card;
    }

    updateStatus(message, status) {
        if (this.wsStatus) {
            this.wsStatus.className = `status-badge ${status}`;
            this.wsStatus.innerHTML = `
                <i class="fas fa-${status === 'connected' ? 'check-circle' : 'exclamation-circle'}"></i>
                ${message}
            `;
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, initializing TeacherDashboard');
    window.teacherDashboard = new TeacherDashboard();
}); 