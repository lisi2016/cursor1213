// 添加 WebSocket 连接
let ws = null;

async function handleLogin() {
  try {
    const loginResult = await loginAPI(credentials);
    
    // 登录成功后建立 WebSocket 连接
    ws = new WebSocket('ws://192.168.3.20:9000/ws?type=student', [], {
      headers: {
        Origin: 'http://192.168.3.20:8889'
      }
    });
    
    ws.onopen = () => {
      console.log('WebSocket连接成功');
      ws.send(JSON.stringify({
        type: 'STATUS_CHANGE',
        studentId: currentUser.id,
        status: 'online',
        name: currentUser.name
      }));
    };

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket连接关闭');
    };

  } catch (error) {
    console.error('登录失败:', error);
  }
}

// 添加登出处理
function handleLogout() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'STATUS_CHANGE',
      studentId: currentUser.id,
      status: 'offline',
      name: currentUser.name
    }));
    ws.close();
  }
} 