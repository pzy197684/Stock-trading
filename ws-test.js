const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:8001/ws/logs');
ws.on('open', () => { console.log('WebSocket连接成功'); process.exit(0); });
ws.on('error', (error) => { console.log('WebSocket连接失败:', error.message); process.exit(1); });
ws.on('close', () => { console.log('WebSocket连接关闭'); process.exit(1); });
setTimeout(() => { console.log('连接超时'); process.exit(1); }, 5000);
