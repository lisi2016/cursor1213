import React, { Component } from 'react';

class StudentStatusMonitor extends Component {
  state = {
    students: {},
    connectionStatus: 'disconnected',
    lastError: null
  };

  componentDidMount() {
    console.log('组件挂载，准备建立 WebSocket 连接...');
    this.connectWebSocket();
  }

  componentWillUnmount() {
    if (this.ws) {
      this.ws.close();
    }
  }

  connectWebSocket = () => {
    console.log('开始 WebSocket 连接过程...');
    this.setState({ connectionStatus: 'connecting', lastError: null });

    try {
      const wsUrl = 'ws://192.168.3.20:9000';
      console.log('尝试连接到:', wsUrl);
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('WebSocket 连接已成功建立');
        this.setState({ connectionStatus: 'connected', lastError: null });
        
        // 发送初始化消息
        this.sendMessage({
          type: 'INIT',
          clientType: 'teacher',
          timestamp: new Date().toISOString()
        });
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket 错误:', error);
        this.setState({ 
          connectionStatus: 'error',
          lastError: '连接错误: ' + (error.message || '未知错误')
        });
      };
      
      this.ws.onclose = (event) => {
        console.log('WebSocket 连接关闭。代码:', event.code, '原因:', event.reason);
        this.setState({ 
          connectionStatus: 'disconnected',
          lastError: `连接关闭 (代码: ${event.code}, 原因: ${event.reason || '未知'})`
        });
        
        // 重连逻辑
        setTimeout(() => {
          if (this.state.connectionStatus !== 'connected') {
            console.log('尝试重新连接...');
            this.connectWebSocket();
          }
        }, 3000);
      };
    } catch (error) {
      console.error('创建 WebSocket 连接时出错:', error);
      this.setState({ 
        connectionStatus: 'error',
        lastError: '创建连接失败: ' + error.message
      });
    }
  };

  // 添加发送消息的辅助方法
  sendMessage = (data) => {
    try {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        const message = JSON.stringify(data);
        console.log('发送消息:', message);
        this.ws.send(message);
      } else {
        console.error('WebSocket 未连接');
      }
    } catch (error) {
      console.error('发送消息失败:', error);
    }
  };

  render() {
    const { connectionStatus, lastError, lastMessage } = this.state;
    
    return (
      <div>
        <h2>WebSocket 连接测试</h2>
        <div>
          <strong>连接状态:</strong> {connectionStatus}
        </div>
        {lastError && (
          <div style={{ color: 'red' }}>
            <strong>后错误:</strong> {lastError}
          </div>
        )}
        {lastMessage && (
          <div>
            <strong>最后收到的消息:</strong>
            <pre>{JSON.stringify(lastMessage, null, 2)}</pre>
          </div>
        )}
      </div>
    );
  }
}

export default StudentStatusMonitor; 