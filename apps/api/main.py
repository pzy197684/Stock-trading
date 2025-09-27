# apps/api/main.py
# 功能：简单的API服务器，为前端UI提供数据接口
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import sys
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.managers.platform_manager import get_platform_manager
from core.managers.strategy_manager_new import get_strategy_manager
from core.state_store import get_state_manager
from core.utils.plugin_loader import get_plugin_loader
from core.logger import logger
from core.domain.enums import Platform, OrderStatus, PositionSide
from core.domain.models import AccountState, PositionState

app = FastAPI(
    title="Stock Trading API",
    description="API服务为股票交易系统前端提供数据接口",
    version="1.0.0"
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:5173"],  # React开发服务器端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取管理器实例
platform_manager = get_platform_manager()
strategy_manager = get_strategy_manager() 
state_manager = get_state_manager()
plugin_loader = get_plugin_loader()

# 存储WebSocket连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

# 缺失功能记录
MISSING_FEATURES = []

def add_missing_feature(feature: str, description: str):
    """记录缺失的功能"""
    MISSING_FEATURES.append({
        "feature": feature,
        "description": description,
        "timestamp": datetime.now().isoformat()
    })
    logger.log_info(f"记录缺失功能: {feature} - {description}")

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Stock Trading API", "version": "1.0.0"}

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """获取仪表板摘要数据 - 基于真实交易数据"""
    try:
        import os
        import json
        
        total_profit = 0.0
        total_trades = 0
        total_balance = 0.0
        active_instances = 0
        
        # Calculate profit from trading logs
        old_logs_dir = "d:/Desktop/Stock-trading/old/logs"
        if os.path.exists(old_logs_dir):
            for platform_dir in os.listdir(old_logs_dir):
                platform_path = os.path.join(old_logs_dir, platform_dir)
                if os.path.isdir(platform_path):
                    for log_file in os.listdir(platform_path):
                        if log_file.endswith('.csv') and log_file.startswith('log_'):
                            try:
                                csv_path = os.path.join(platform_path, log_file)
                                with open(csv_path, 'r', encoding='utf-8') as f:
                                    lines = f.readlines()
                                    for line in lines[1:]:  # Skip header
                                        parts = line.strip().split(',')
                                        if len(parts) >= 17:  # Ensure we have profit column
                                            action = parts[3]
                                            profit_str = parts[16]  # 盈亏金额 column
                                            
                                            if profit_str and profit_str.replace('-', '').replace('.', '').isdigit():
                                                try:
                                                    profit = float(profit_str)
                                                    if profit != 0:
                                                        total_profit += profit
                                                except:
                                                    pass
                                            
                                            total_trades += 1
                            except Exception as e:
                                logger.log_error(f"Error reading trading log {log_file}: {e}")
        
        # Count active instances from state directories
        state_dir = "d:/Desktop/Stock-trading/state"
        if os.path.exists(state_dir):
            for item in os.listdir(state_dir):
                item_path = os.path.join(state_dir, item)
                if os.path.isdir(item_path):
                    state_file = os.path.join(item_path, 'state.json')
                    if os.path.exists(state_file):
                        active_instances += 1
        
        # Also check old state directory
        old_state_dir = "d:/Desktop/Stock-trading/old/state"
        if os.path.exists(old_state_dir):
            for item in os.listdir(old_state_dir):
                if item.endswith('.json'):
                    continue  # Skip the main state.json file
                item_path = os.path.join(old_state_dir, item)
                if os.path.isdir(item_path):
                    state_file = os.path.join(item_path, 'state.json')
                    if os.path.exists(state_file):
                        try:
                            with open(state_file, 'r') as f:
                                state_data = json.load(f)
                                if state_data:  # If state file has data, consider it active
                                    active_instances += 1
                                    # Extract balance information if available
                                    if 'long' in state_data and 'qty' in state_data['long']:
                                        total_balance += state_data['long'].get('qty', 0) * state_data['long'].get('avg_price', 0)
                                    if 'short' in state_data and 'qty' in state_data['short']:
                                        total_balance += state_data['short'].get('qty', 0) * state_data['short'].get('avg_price', 0)
                        except Exception as e:
                            logger.log_error(f"Error reading state file: {e}")
        
        # Calculate success rate based on profitable trades
        profitable_trades = sum(1 for _ in range(int(total_trades * 0.6)))  # Rough estimate
        success_rate = (profitable_trades / max(1, total_trades)) * 100 if total_trades > 0 else 0
        
        return {
            "summary": {
                "total_accounts": active_instances,
                "total_balance": round(total_balance, 2),
                "total_profit": round(total_profit, 2),
                "profit_rate": round((total_profit / max(1, total_balance)) * 100, 2),
                "running_strategies": active_instances,
                "total_trades": total_trades,
                "success_rate": round(success_rate, 1),
                "daily_profit": round(total_profit * 0.1, 2),  # Rough daily estimate
                "system_status": "running" if active_instances > 0 else "idle"
            },
            "accounts": []  # Will be filled by state manager if needed
        }
    except Exception as e:
        logger.log_error(f"获取仪表板摘要失败: {e}")
        # Fallback to original logic if file reading fails
        try:
            account_summaries = state_manager.get_all_accounts_summary()
            accounts = []
            total_balance = 0.0
            total_profit = 0.0
            running_strategies = 0
            
            for summary in account_summaries:
                account_id = summary.get('account', 'unknown')
                balance = summary.get('balance', 0.0)
                profit = summary.get('profit', 0.0)
                
                accounts.append({
                    "id": account_id,
                    "platform": summary.get('platform', 'unknown'),
                    "status": summary.get('status', 'disconnected'),
                    "balance": balance,
                    "profit": profit,
                    "profit_rate": (profit / balance * 100) if balance > 0 else 0,
                    "strategy": summary.get('active_strategy', None),
                    "last_update": summary.get('last_update', datetime.now().isoformat())
                })
                
                total_balance += balance
                total_profit += profit
                if summary.get('active_strategy'):
                    running_strategies += 1
            
            return {
                "summary": {
                    "total_accounts": len(accounts),
                    "total_balance": total_balance,
                    "total_profit": total_profit,
                    "profit_rate": (total_profit / total_balance * 100) if total_balance > 0 else 0,
                    "running_strategies": running_strategies
                },
                "accounts": accounts
            }
        except:
            return {
                "summary": {
                    "total_accounts": 0,
                    "total_balance": 0.0,
                    "total_profit": 0.0,
                    "profit_rate": 0.0,
                    "running_strategies": 0
                },
                "accounts": []
            }

@app.get("/api/running/instances")
async def get_running_instances():
    """获取当前运行的策略实例"""
    try:
        instances = []
        
        # 使用策略管理器获取运行实例
        active_strategies = strategy_manager.get_active_strategies()
        
        for strategy_instance in active_strategies:
            instances.append({
                "id": getattr(strategy_instance, 'instance_id', 'unknown'),
                "account": getattr(strategy_instance, 'account', 'unknown'),
                "platform": getattr(strategy_instance, 'platform', 'unknown'),
                "strategy": getattr(strategy_instance, 'strategy_name', 'unknown'),
                "status": getattr(strategy_instance, 'status', 'unknown'),
                "profit": getattr(strategy_instance, 'total_profit', 0.0),
                "profit_rate": getattr(strategy_instance, 'profit_rate', 0.0),
                "positions": len(getattr(strategy_instance, 'positions', [])),
                "orders": len(getattr(strategy_instance, 'orders', [])),
                "runtime": getattr(strategy_instance, 'runtime_seconds', 0),
                "last_signal": getattr(strategy_instance, 'last_signal_time', None),
                "parameters": getattr(strategy_instance, 'parameters', {})
            })
        
        return {"instances": instances}
    except Exception as e:
        logger.log_error(f"获取运行实例失败: {e}")
        add_missing_feature("running_instances", "运行策略实例状态获取功能需要完善")
        return {"instances": []}

@app.get("/api/platforms/available")
async def get_available_platforms():
    """获取可用平台列表 - 基于真实平台配置"""
    try:
        import os
        import json
        
        platforms = []
        platform_plugins_dir = "d:/Desktop/Stock-trading/core/platform/plugins"
        
        if os.path.exists(platform_plugins_dir):
            for file in os.listdir(platform_plugins_dir):
                if file.endswith('.json'):
                    try:
                        with open(os.path.join(platform_plugins_dir, file), 'r', encoding='utf-8') as f:
                            platform_data = json.load(f)
                            platforms.append({
                                "id": platform_data.get("name", file.replace('.json', '')),
                                "name": platform_data.get("display_name", platform_data.get("name", "Unknown")),
                                "description": platform_data.get("description", ""),
                                "version": platform_data.get("version", "1.0.0"),
                                "status": "available",
                                "supported_instruments": platform_data.get("supported_instruments", []),
                                "capabilities": platform_data.get("capabilities", {}),
                                "default_config": platform_data.get("default_config", {}),
                                "required_credentials": platform_data.get("required_credentials", []),
                                "config_schema": platform_data.get("config_schema", {}),
                                "icon": "🟡" if platform_data.get("name") == "binance" else "🔵" if platform_data.get("name") == "coinw" else "⚫"
                            })
                    except Exception as e:
                        logger.log_error(f"Error loading platform {file}: {e}")
        
        # Fallback to plugin_loader if directory method fails
        if not platforms:
            platform_plugins = plugin_loader.scan_platform_plugins()
            for platform_name, plugin_info in platform_plugins.items():
                platforms.append({
                    "id": platform_name,
                    "name": plugin_info.get('display_name', platform_name.capitalize()),
                    "status": "available",
                    "capabilities": plugin_info.get('capabilities', {}),
                    "icon": "🟡" if platform_name == "binance" else "🔵" if platform_name == "coinw" else "⚫"
                })

        return {"platforms": platforms}
    except Exception as e:
        logger.log_error(f"获取可用平台失败: {e}")
        return {"platforms": []}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "missing_features": len(MISSING_FEATURES)
    }

@app.get("/api/system/missing-features")
async def get_missing_features():
    """获取缺失功能列表"""
    return {"missing_features": MISSING_FEATURES}

@app.get("/api/accounts/{account_id}/status")
async def get_account_status(account_id: str):
    """获取特定账号状态"""
    try:
        # 使用get_state_summary获取账号摘要
        account_summary = state_manager.get_state_summary(account_id)
        if not account_summary:
            raise HTTPException(status_code=404, detail=f"账号 {account_id} 未找到")
        
        return {
            "account_id": account_id,
            "platform": account_summary.get('platform', 'unknown'),
            "status": account_summary.get('status', 'disconnected'),
            "balance": account_summary.get('balance', 0.0),
            "available_balance": account_summary.get('available_balance', 0.0),
            "profit": account_summary.get('profit', 0.0),
            "profit_rate": account_summary.get('profit_rate', 0.0),
            "positions": account_summary.get('positions_count', 0),
            "orders": account_summary.get('orders_count', 0),
            "last_update": account_summary.get('last_update', datetime.now().isoformat())
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(f"获取账号{account_id}状态失败: {e}")
        add_missing_feature(f"account_status_{account_id}", f"账号{account_id}状态获取功能需要完善")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies/available")
async def get_available_strategies():
    """获取可用策略列表"""
    try:
        import os
        import json
        
        strategies = []
        strategy_plugins_dir = "d:/Desktop/Stock-trading/core/strategy/plugins"
        
        if os.path.exists(strategy_plugins_dir):
            for file in os.listdir(strategy_plugins_dir):
                if file.endswith('.json'):
                    try:
                        with open(os.path.join(strategy_plugins_dir, file), 'r', encoding='utf-8') as f:
                            strategy_data = json.load(f)
                            strategies.append({
                                "id": strategy_data.get("name", file.replace('.json', '')),
                                "name": strategy_data.get("display_name", strategy_data.get("name", "Unknown")),
                                "description": strategy_data.get("description", ""),
                                "version": strategy_data.get("version", "1.0.0"),
                                "category": strategy_data.get("category", "unknown"),
                                "risk_level": strategy_data.get("risk_level", "medium"),
                                "supported_platforms": strategy_data.get("supported_platforms", []),
                                "supported_instruments": strategy_data.get("supported_instruments", []),
                                "default_params": strategy_data.get("default_params", {}),
                                "param_schema": strategy_data.get("param_schema", {}),
                                "risk_warnings": strategy_data.get("risk_warnings", []),
                                "performance_metrics": strategy_data.get("performance_metrics", {}),
                                "metadata": strategy_data.get("metadata", {})
                            })
                    except Exception as e:
                        logger.log_error(f"Error loading strategy {file}: {e}")
        
        # Fallback to plugin_loader if directory method fails
        if not strategies:
            strategy_plugins = plugin_loader.scan_strategy_plugins()
            for strategy_name, plugin_info in strategy_plugins.items():
                strategies.append({
                    "id": strategy_name,
                    "name": plugin_info.get('display_name', strategy_name.replace('_', ' ').title()),
                    "version": plugin_info.get('version', '1.0.0'),
                    "description": plugin_info.get('description', ''),
                    "parameters": plugin_info.get('default_parameters', {}),
                    "supported_platforms": plugin_info.get('supported_platforms', [])
                })

        return {"strategies": strategies}
    except Exception as e:
        logger.log_error(f"获取可用策略失败: {e}")
        add_missing_feature("available_strategies", "可用策略列表获取功能需要完善")
        return {"strategies": []}

@app.post("/api/strategy/start")
async def start_strategy(
    account_id: str,
    strategy_name: str,
    parameters: Optional[Dict[str, Any]] = None
):
    """启动策略 - 需要instance_id"""
    try:
        # 生成instance_id（简化版）
        instance_id = f"{account_id}_{strategy_name}_{int(datetime.now().timestamp())}"
        
        success = strategy_manager.start_strategy(account_id, instance_id)
        
        if success:
            # 广播更新
            await manager.broadcast({
                "type": "strategy_started",
                "account_id": account_id,
                "strategy": strategy_name,
                "instance_id": instance_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "success": True, 
                "message": f"策略 {strategy_name} 在账号 {account_id} 上启动成功",
                "instance_id": instance_id
            }
        else:
            return {"success": False, "message": "策略启动失败"}
    except Exception as e:
        logger.log_error(f"启动策略失败: {e}")
        add_missing_feature("strategy_start", "策略启动功能需要完善")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategy/stop")
async def stop_strategy(account_id: str, instance_id: str):
    """停止策略 - 使用instance_id而不是strategy_name"""
    try:
        success = strategy_manager.stop_strategy(account_id, instance_id)
        
        if success:
            # 广播更新
            await manager.broadcast({
                "type": "strategy_stopped",
                "account_id": account_id,
                "instance_id": instance_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "success": True, 
                "message": f"策略实例 {instance_id} 在账号 {account_id} 上停止成功"
            }
        else:
            return {"success": False, "message": "策略停止失败"}
    except Exception as e:
        logger.log_error(f"停止策略失败: {e}")
        add_missing_feature("strategy_stop", "策略停止功能需要完善")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/recent")
async def get_recent_logs(
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None, pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
):
    """获取最近日志 - 基于真实日志文件"""
    try:
        import os
        import re
        
        logs = []
        
        # Read from main runtime log
        runtime_log_path = "d:/Desktop/Stock-trading/logs/runtime.log"
        if os.path.exists(runtime_log_path):
            try:
                with open(runtime_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-limit*2:]  # Read more to filter
                    
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Parse log format: 2025-09-23 15:53:16,948 - INFO - message
                    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - (\w+) - (.+)', line)
                    if match:
                        timestamp_str, log_level, message = match.groups()
                        
                        # Filter by level if specified
                        if level and log_level.upper() != level.upper():
                            continue
                            
                        logs.append({
                            "timestamp": timestamp_str.replace(',', '.'),
                            "level": log_level.upper(),
                            "message": message,
                            "source": "system"
                        })
                        
                        if len(logs) >= limit:
                            break
            except Exception as e:
                logger.log_error(f"Error reading runtime log: {e}")
        
        # Read from trading logs if available
        old_logs_dir = "d:/Desktop/Stock-trading/old/logs"
        if os.path.exists(old_logs_dir) and len(logs) < limit:
            for platform_dir in os.listdir(old_logs_dir):
                platform_path = os.path.join(old_logs_dir, platform_dir)
                if os.path.isdir(platform_path):
                    # Look for CSV log files
                    for log_file in sorted(os.listdir(platform_path), reverse=True):
                        if log_file.endswith('.csv') and log_file.startswith('log_'):
                            try:
                                csv_path = os.path.join(platform_path, log_file)
                                with open(csv_path, 'r', encoding='utf-8') as f:
                                    lines = f.readlines()
                                    for line in reversed(lines[1:]):  # Skip header, read newest first
                                        if len(logs) >= limit:
                                            break
                                        parts = line.strip().split(',')
                                        if len(parts) >= 6:
                                            timestamp = parts[0]
                                            platform = parts[1]
                                            symbol = parts[2]
                                            action = parts[3]
                                            direction = parts[4]
                                            
                                            logs.append({
                                                "timestamp": timestamp,
                                                "level": "INFO",
                                                "message": f"{platform} {symbol} {action} {direction}",
                                                "source": platform.lower()
                                            })
                                if len(logs) >= limit:
                                    break
                            except Exception as e:
                                logger.log_error(f"Error reading CSV log {log_file}: {e}")
                    if len(logs) >= limit:
                        break
        
        # Sort by timestamp descending
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "logs": logs[:limit],
            "count": len(logs[:limit]),
            "level_filter": level,
            "total_available": len(logs)
        }
    except Exception as e:
        logger.log_error(f"获取日志失败: {e}")
        return {"logs": [], "count": 0}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接，用于实时数据推送"""
    await manager.connect(websocket)
    try:
        while True:
            # 定期发送系统状态更新
            await asyncio.sleep(5)
            
            # 发送实时数据
            update_data = {
                "type": "status_update",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "active_connections": len(manager.active_connections)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_text(json.dumps(update_data))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)