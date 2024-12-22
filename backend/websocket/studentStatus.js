const WebSocket = require('ws');
const http = require('http');

// 创建 HTTP 服务器
const server = http.createServer((req, res) => {
  console.log('\n收到 HTTP 请求:');
  console.log('Method:', req.method);
  console.log('URL:', req.url);
  console.log('Headers:', req.headers);
  
  // 允许所有来源
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', '*');
  res.setHeader('Access-Control-Allow-Headers', '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('WebSocket server is running\n');
});

// 创建 WebSocket 服务器
const wss = new WebSocket.Server({ 
  server,
  path: '/',  // 明确指定路径
  verifyClient: (info, done) => {
    console.log('\n收到 WebSocket 连接请求:');
    console.log('URL:', info.req.url);
    console.log('Headers:', info.req.headers);
    console.log('Origin:', info.origin);
    
    // 允许所有连接
    done(true);
  }
});

// 存储连接
const connections = new Set();

// 连接处理
wss.on('connection', (ws, req) => {
  console.log('\n新的 WebSocket 连接已建立');
  console.log('客户端 IP:', req.socket.remoteAddress);
  console.log('URL:', req.url);
  console.log('Headers:', req.headers);

  // 发送连接成功消息
  ws.send(JSON.stringify({
    type: 'CONNECTION_STATUS',
    status: 'connected',
    timestamp: new Date().toISOString()
  }));

  // 错误处理
  ws.on('error', (error) => {
    console.error('WebSocket 连接错误:', error);
  });

  // 关闭处理
  ws.on('close', (code, reason) => {
    console.log('\nWebSocket 连接关闭');
    console.log('关闭代码:', code);
    console.log('关闭原因:', reason);
  });
});

// 定期检查连接状态
setInterval(() => {
  const now = new Date();
  console.log(`[${now.toISOString()}] 当前活动连接数: ${connections.size}`);
  
  connections.forEach(ws => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.ping();
    }
  });
}, 30000);

// 启动服务器
const PORT = 9000;
server.listen(PORT, '0.0.0.0', () => {
  console.log(`\nWebSocket 服务器启动于端口 ${PORT}`);
  console.log(`HTTP 地址: http://0.0.0.0:${PORT}`);
  console.log(`WebSocket 地址: ws://0.0.0.0:${PORT}`);
});

// 错误处理
server.on('error', (error) => {
  console.error('服务器错误:', error);
});

process.on('uncaughtException', (error) => {
  console.error('未捕获的异常:', error);
}); 