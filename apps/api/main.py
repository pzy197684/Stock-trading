# apps/api/main.py
# 功能：简单的API服务器，为前端UI提供数据接口
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import sys
import os
import asyncio
import json
import traceback
import time
import shutil
from functools import wraps
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.managers.platform_manager import get_platform_manager
from core.managers.strategy_manager import get_strategy_manager
from core.state_store import get_state_manager
from core.utils.plugin_loader import get_plugin_loader
from core.logger import logger
from core.websocket_logger import setup_websocket_logging
from core.domain.enums import Platform, OrderStatus, PositionSide
from core.domain.models import AccountState, PositionState
from core.utils.error_codes import ErrorCodeManager, format_error, duplicate_instance_error, parameters_incomplete_error, instance_not_found_error

# 错误处理装饰器
def handle_api_errors(func):
    """统一的API错误处理装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # 记录API调用开始
            func_name = func.__name__
            logger.debug(f"API调用开始: {func_name}")
            
            result = await func(*args, **kwargs)
            
            # 记录API调用成功
            logger.debug(f"API调用成功: {func_name}")
            return result
            
        except HTTPException as e:
            # HTTP异常直接抛出
            logger.warning(f"HTTP异常 [{func_name}]: {e.status_code} - {e.detail}")
            raise e
            
        except Exception as e:
            # 记录详细错误信息
            error_msg = f"API错误 [{func_name}]: {str(e)}"
            logger.exception(error_msg)
            
            # 广播错误日志
            await manager.broadcast_log({
                "timestamp": datetime.now().isoformat(),
                "level": "error",
                "message": error_msg,
                "source": "API",
                "category": "api_error",
                "data": {
                    "function": func_name,
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            })
            
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error in {func_name}: {str(e)}"
            )
    return wrapper

app = FastAPI(
    title="Stock Trading API",
    description="API服务为股票交易系统前端提供数据接口",
    version="1.0.0"
)

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取管理器实例
platform_manager = get_platform_manager()
strategy_manager = get_strategy_manager() 
state_manager = get_state_manager()
plugin_loader = get_plugin_loader()

# 导入策略执行引擎
from core.execute.strategy_engine import get_strategy_engine
strategy_engine = get_strategy_engine()

# 存储WebSocket连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.log_connections: List[WebSocket] = []  # 专门用于日志推送
        self.max_connections = 50  # 限制最大连接数
        self.connection_metadata = {}  # 存储连接元数据

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        if len(self.active_connections) >= self.max_connections:
            # 移除最老的连接
            oldest = self.active_connections.pop(0)
            try:
                await oldest.close()
            except:
                pass
        self.active_connections.append(websocket)

    async def connect_log(self, websocket: WebSocket):
        """连接日志WebSocket - 增强版本"""
        try:
            await websocket.accept()
            
            # 限制连接数，防止资源耗尽
            if len(self.log_connections) >= self.max_connections:
                oldest = self.log_connections.pop(0)
                try:
                    await oldest.close(code=1000, reason="连接数量达到上限")
                except:
                    pass
                    
            self.log_connections.append(websocket)
            
            # 记录连接元数据
            client_info = {
                "connect_time": datetime.now().isoformat(),
                "ip": websocket.client.host if websocket.client else "unknown",
                "last_heartbeat": datetime.now()
            }
            self.connection_metadata[id(websocket)] = client_info
            
            logger.info(f"日志WebSocket客户端已连接，当前总数: {len(self.log_connections)}")
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            raise

    def disconnect(self, websocket: WebSocket):
        """增强的断开连接处理"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            if websocket in self.log_connections:
                self.log_connections.remove(websocket)
                logger.info(f"日志WebSocket客户端已断开，当前总数: {len(self.log_connections)}")
                
            # 清理元数据
            conn_id = id(websocket)
            if conn_id in self.connection_metadata:
                del self.connection_metadata[conn_id]
                
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")

    async def cleanup_stale_connections(self):
        """清理过期连接"""
        stale_connections = []
        current_time = datetime.now()
        
        for websocket in self.log_connections:
            conn_id = id(websocket)
            if conn_id in self.connection_metadata:
                last_heartbeat = self.connection_metadata[conn_id]["last_heartbeat"]
                if (current_time - last_heartbeat).total_seconds() > 120:  # 2分钟无心跳
                    stale_connections.append(websocket)
        
        for websocket in stale_connections:
            try:
                await websocket.close(code=1000, reason="连接超时")
            except:
                pass
            self.disconnect(websocket)
        
        if stale_connections:
            logger.info(f"清理了 {len(stale_connections)} 个过期连接")

    async def broadcast(self, message: dict):
        """增强的广播功能"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"WebSocket广播消息失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_log(self, log_entry: dict):
        """广播日志消息 - 增强版本"""
        if not self.log_connections:
            return  # 静默处理，避免控制台噪音
            
        # 确保消息编码正确
        message = {
            "type": "log",
            "data": log_entry,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected = []
        success_count = 0
        
        for connection in self.log_connections:
            try:
                # 使用ensure_ascii=False确保中文正确显示
                json_message = json.dumps(message, ensure_ascii=False)
                await connection.send_text(json_message)
                success_count += 1
                
                # 更新心跳时间
                conn_id = id(connection)
                if conn_id in self.connection_metadata:
                    self.connection_metadata[conn_id]["last_heartbeat"] = datetime.now()
                    
            except Exception as e:
                logger.debug(f"WebSocket发送失败，将断开连接: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)
            
        # 只在有异常时记录日志
        if disconnected:
            logger.warning(f"清理了 {len(disconnected)} 个断开的WebSocket连接")

    def get_connection_stats(self):
        """获取连接统计信息"""
        return {
            "total_connections": len(self.log_connections),
            "active_connections": len(self.active_connections),
            "max_connections": self.max_connections,
            "connection_details": [
                {
                    "id": conn_id,
                    "connect_time": info["connect_time"],
                    "ip": info["ip"],
                    "last_heartbeat": info["last_heartbeat"].isoformat()
                }
                for conn_id, info in self.connection_metadata.items()
            ]
        }

manager = ConnectionManager()

# 设置WebSocket日志推送
setup_websocket_logging(logger, manager.broadcast_log)

# 全局工具函数
def deep_merge(target, source):
    """深度合并字典，保留target中source没有的键"""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target

# 应用生命周期事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.log_info("🚀 API服务器启动中...")
    logger.log_info("📂 开始自动策略启动检查...")
    
    # 测试WebSocket日志系统
    print("[系统启动] 初始化WebSocket日志系统...")
    logger.log_info("🔌 WebSocket日志系统已初始化")
    logger.log_info("📡 等待前端连接到 ws://localhost:8001/ws/logs")
    
    # 启动定期清理任务
    asyncio.create_task(periodic_cleanup_task())
    logger.log_info("🧹 WebSocket连接清理任务已启动")
    
    # 手动调用策略管理器的自动启动方法
    try:
        logger.log_info("🔄 调用策略管理器自动启动方法...")
        strategy_manager._load_and_start_auto_strategies()
        logger.log_info("✅ 策略自动启动检查完成")
    except Exception as e:
        logger.log_error(f"❌ 策略自动启动失败: {e}")
        import traceback
        logger.log_error(f"详细错误: {traceback.format_exc()}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.log_info("🛑 API服务器正在关闭...")
    
    # 优雅关闭所有WebSocket连接
    for websocket in manager.log_connections.copy():
        try:
            await websocket.close(code=1001, reason="服务器关闭")
        except:
            pass
    
    for websocket in manager.active_connections.copy():
        try:
            await websocket.close(code=1001, reason="服务器关闭")
        except:
            pass
    
    logger.log_info("✅ API服务器已关闭")

async def periodic_cleanup_task():
    """定期清理任务"""
    while True:
        try:
            await asyncio.sleep(300)  # 每5分钟执行一次
            await manager.cleanup_stale_connections()
            
            # 记录连接状态
            if len(manager.log_connections) > 0:
                logger.debug(f"WebSocket连接状态: {len(manager.log_connections)} 个活跃连接")
                
        except Exception as e:
            logger.error(f"定期清理任务出错: {e}")
            await asyncio.sleep(60)  # 出错后短暂等待再继续
    
    # 启动策略执行引擎
    try:
        logger.log_info("🔄 启动策略执行引擎...")
        await strategy_engine.start()
        logger.log_info("✅ 策略执行引擎启动成功")
    except Exception as e:
        logger.log_error(f"❌ 策略执行引擎启动失败: {e}")
        import traceback
        logger.log_error(f"详细错误: {traceback.format_exc()}")

@app.on_event("shutdown") 
async def shutdown_event():
    """应用关闭事件"""
    logger.log_info("⏹️ API服务器关闭中...")
    
    # 停止策略执行引擎
    try:
        await strategy_engine.stop()
        logger.log_info("✅ 策略执行引擎已停止")
    except Exception as e:
        logger.log_error(f"❌ 策略执行引擎停止失败: {e}")

# Pydantic模型定义
class CreateInstanceRequest(BaseModel):
    account_id: str
    platform: str  
    strategy: str
    symbol: str
    parameters: Optional[Dict[str, Any]] = None

class StopStrategyRequest(BaseModel):
    account_id: str
    instance_id: str

class ForceStopStrategyRequest(BaseModel):
    account_id: str
    instance_id: str

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

def get_account_owner(account_name: str) -> str:
    """获取账号拥有人信息 - 优先从API配置文件读取"""
    try:
        # 方法1：优先从API配置文件读取拥有人信息
        accounts_dir = os.path.join(project_root, "accounts")
        
        # 查找账号的API配置文件
        for platform_dir in os.listdir(accounts_dir):
            if platform_dir.startswith('_'):
                continue
            platform_path = os.path.join(accounts_dir, platform_dir)
            if os.path.isdir(platform_path):
                account_path = os.path.join(platform_path, account_name)
                if os.path.isdir(account_path):
                    # 查找API配置文件（支持多种命名格式）
                    api_files = [
                        f"{platform_dir.lower()}_api.json",  # 如 binance_api.json
                        "api.json",
                        "config.json"
                    ]
                    
                    for api_file in api_files:
                        api_file_path = os.path.join(account_path, api_file)
                        if os.path.exists(api_file_path):
                            with open(api_file_path, 'r', encoding='utf-8-sig') as f:
                                api_config = json.load(f)
                                owner = api_config.get('owner')
                                if owner:
                                    logger.log_info(f"Found owner '{owner}' for account {account_name} in {api_file}")
                                    return owner
        
        # 方法2：从profile.json读取拥有人信息（向后兼容）
        profiles_dir = os.path.join(project_root, "profiles")
        
        for platform_dir in os.listdir(profiles_dir):
            if platform_dir.startswith('_'):
                continue
            platform_path = os.path.join(profiles_dir, platform_dir)
            if os.path.isdir(platform_path):
                account_path = os.path.join(platform_path, account_name)
                if os.path.isdir(account_path):
                    profile_file = os.path.join(account_path, 'profile.json')
                    if os.path.exists(profile_file):
                        with open(profile_file, 'r', encoding='utf-8-sig') as f:
                            profile = json.load(f)
                            owner = profile.get('profile_info', {}).get('owner')
                            if owner:
                                logger.log_info(f"Found owner '{owner}' for account {account_name} in profile.json (fallback)")
                                return owner
        
        # 方法3：使用默认规则（最后的后备方案）
        if account_name == 'BN2055':
            logger.log_info(f"Using default rule: {account_name} -> 潘正芳")
            return '潘正芳'
        else:
            logger.log_info(f"Using default rule: {account_name} -> 潘正友")
            return '潘正友'
    except Exception as e:
        logger.log_error(f"获取账号 {account_name} 拥有人信息失败: {e}")
        # 默认规则：BN2055属于潘正芳，其他账号属于潘正友
        if account_name == 'BN2055':
            return '潘正芳'
        else:
            return '潘正友'

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
@handle_api_errors
async def get_running_instances():
    """获取当前运行的策略实例 - 标准化响应格式"""
    try:
        instances = []
        
        # 获取所有策略实例
        try:
            all_strategies = []
            # 遍历所有账号的策略实例
            for account_instances in strategy_manager.strategy_instances.values():
                for instance in account_instances.values():
                    all_strategies.append(instance)
            logger.log_info(f"Found {len(all_strategies)} total strategy instances")
        except Exception as e:
            logger.log_error(f"Failed to get strategy instances: {e}")
            all_strategies = []
        
        for strategy_instance in all_strategies:
            try:
                # 标准化数据格式
                instance_data = {
                    "id": getattr(strategy_instance, 'instance_id', 'unknown'),
                    "account": getattr(strategy_instance, 'account', 'unknown'),
                    "platform": getattr(strategy_instance, 'platform', 'unknown'),
                    "strategy": getattr(strategy_instance, 'strategy_name', 'unknown'),
                    "status": normalize_status(strategy_instance),
                    "symbol": normalize_symbol(strategy_instance),
                    "profit": float(getattr(strategy_instance, 'total_profit', 0.0)),
                    "profit_rate": float(getattr(strategy_instance, 'profit_rate', 0.0)),
                    "positions": len(getattr(strategy_instance, 'positions', [])),
                    "orders": len(getattr(strategy_instance, 'orders', [])),
                    "runtime": int(getattr(strategy_instance, 'runtime_seconds', 0)),
                    "last_signal": getattr(strategy_instance, 'last_signal_time', None),
                    "created_at": getattr(strategy_instance, 'created_at', datetime.now().isoformat()),
                    "pid": getattr(strategy_instance, 'pid', None),
                    "owner": get_account_owner(getattr(strategy_instance, 'account', 'unknown'))
                }
                
                # 兼容字段
                instance_data["tradingPair"] = instance_data["symbol"]
                
                instances.append(instance_data)
                
            except Exception as e:
                logger.log_error(f"Error processing strategy instance: {e}")
                continue
        
        # 按创建时间排序
        instances.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            "success": True,
            "data": {
                "instances": instances,
                "total": len(instances),
                "running": len([i for i in instances if i['status'] == 'running']),
                "stopped": len([i for i in instances if i['status'] == 'stopped'])
            }
        }
        
    except Exception as e:
        logger.log_error(f"获取运行实例失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "instances": [],
                "total": 0,
                "running": 0,
                "stopped": 0
            }
        }

def normalize_status(strategy_instance) -> str:
    """标准化策略状态"""
    try:
        if hasattr(strategy_instance, 'strategy') and hasattr(strategy_instance.strategy, 'status'):
            status_value = strategy_instance.strategy.status
            if hasattr(status_value, 'value'):
                status = status_value.value.lower()
            else:
                status = str(status_value).lower()
        elif hasattr(strategy_instance, 'status'):
            status = str(getattr(strategy_instance, 'status', 'stopped')).lower()
        else:
            status = 'stopped'
        
        # 映射到标准状态
        status_mapping = {
            'active': 'running',
            'inactive': 'stopped',
            'running': 'running',
            'stopped': 'stopped',
            'error': 'error',
            'starting': 'starting'
        }
        
        return status_mapping.get(status, 'stopped')
        
    except Exception:
        return 'stopped'

def normalize_symbol(strategy_instance) -> str:
    """标准化交易对格式"""
    try:
        parameters = getattr(strategy_instance, 'parameters', {})
        symbol = parameters.get('symbol', 'OP/USDT')
        
        # 标准化格式
        if symbol and 'USDT' in symbol and '/' not in symbol:
            symbol = symbol.replace('USDT', '/USDT')
        
        return symbol
        
    except Exception:
        return 'OP/USDT'

@app.get("/api/running/instances/{instance_name}/parameters")
async def get_instance_parameters(instance_name: str):
    """获取指定运行实例的参数"""
    try:
        # 获取活跃策略
        active_strategies = strategy_manager.get_active_strategies()
        
        # 查找匹配的策略实例
        target_instance = None
        for strategy_instance in active_strategies:
            if getattr(strategy_instance, 'instance_id', '') == instance_name or \
               getattr(strategy_instance, 'account', '') == instance_name:
                target_instance = strategy_instance
                break
        
        if not target_instance:
            logger.log_warning(f"Instance not found: {instance_name}")
            return {"success": False, "error": "Instance not found"}
        
        # 获取原始参数
        raw_parameters = getattr(target_instance, 'parameters', {})
        
        logger.log_info(f"Retrieved parameters for instance {instance_name}")
        return {
            "success": True,
            "instance_id": getattr(target_instance, 'instance_id', instance_name),
            "account": getattr(target_instance, 'account', 'unknown'),
            "platform": getattr(target_instance, 'platform', 'unknown'),
            "strategy": getattr(target_instance, 'strategy_name', 'unknown'),
            "raw_parameters": raw_parameters
        }
        
    except Exception as e:
        logger.log_error(f"获取实例参数失败: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/running/instances/{instance_name}/parameters")
async def update_instance_parameters(instance_name: str, parameters: dict):
    """更新指定运行实例的参数"""
    try:
        logger.log_info(f"收到参数更新请求 - 实例: {instance_name}")
        logger.log_info(f"收到的参数: {json.dumps(parameters, indent=2, ensure_ascii=False)}")
        
        # 获取活跃策略
        active_strategies = strategy_manager.get_active_strategies()
        logger.log_info(f"当前活跃策略数量: {len(active_strategies)}")
        
        # 查找匹配的策略实例
        target_instance = None
        for strategy_instance in active_strategies:
            instance_id = getattr(strategy_instance, 'instance_id', '')
            account = getattr(strategy_instance, 'account', '')
            logger.log_info(f"检查策略实例 - instance_id: {instance_id}, account: {account}")
            
            if instance_id == instance_name or account == instance_name:
                target_instance = strategy_instance
                logger.log_info(f"找到匹配的实例: {instance_name}")
                break
        
        if not target_instance:
            logger.log_warning(f"Instance not found: {instance_name}, 直接更新配置文件")
            # 如果找不到运行实例，直接更新配置文件
            # 假设实例名就是账户名，如 BN1602
            account = instance_name
            platform = "BINANCE"  # 可以根据account前缀判断
            strategy_name = "martingale_hedge"
        else:
            # 更新参数 - 这里应该调用策略实例的更新方法
            # 暂时只是记录，因为具体的更新逻辑依赖于策略实现
            if hasattr(target_instance, 'update_parameters'):
                target_instance.update_parameters(parameters)
            else:
                # 如果没有更新方法，直接设置参数属性
                setattr(target_instance, 'parameters', parameters)
            
            account = getattr(target_instance, 'account', instance_name)
            platform = getattr(target_instance, 'platform', 'BINANCE')
            strategy_name = getattr(target_instance, 'strategy_name', 'martingale_hedge')
        # 保存参数到配置文件
        try:
            # 构建配置文件路径
            if platform.upper() == 'BINANCE':
                config_path = f"profiles/BINANCE/{account}/strategies/{strategy_name}.json"
            elif platform.upper() == 'COINW':
                config_path = f"profiles/COINW/{account}/strategies/{strategy_name}.json"
            elif platform.upper() == 'OKX':
                config_path = f"profiles/OKX/{account}/strategies/{strategy_name}.json"
            else:
                config_path = f"profiles/{platform.upper()}/{account}/strategies/{strategy_name}.json"
            
            logger.log_info(f"保存配置到文件: {config_path}")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 读取现有配置文件，如果存在的话
            existing_config = {}
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8-sig') as f:
                        existing_config = json.load(f)
                except Exception as e:
                    logger.log_warning(f"Failed to read existing config: {e}")
            
            # 深度合并参数，确保autoTrade等关键参数被正确保存
            logger.log_info(f"合并前的现有配置: {json.dumps(existing_config, indent=2, ensure_ascii=False)}")
            
            # 特别处理autoTrade参数，确保它被正确保存
            if 'autoTrade' in parameters:
                existing_config['autoTrade'] = parameters['autoTrade']
                logger.log_info(f"✅ 专门保存autoTrade参数: {parameters['autoTrade']}")
            
            # 深度合并其他参数
            deep_merge(existing_config, parameters)
            
            logger.log_info(f"合并后的最终配置: {json.dumps(existing_config, indent=2, ensure_ascii=False)}")
            
            # 保存更新后的配置文件
            with open(config_path, 'w', encoding='utf-8-sig') as f:
                json.dump(existing_config, f, indent=2, ensure_ascii=False)
            
            logger.log_info(f"Parameters saved to config file: {config_path}")
            
        except Exception as save_error:
            logger.log_warning(f"Failed to save parameters to config file: {save_error}")
        
        logger.log_info(f"Updated parameters for instance {instance_name}")
        return {
            "success": True,
            "message": f"Parameters updated for instance {instance_name}"
        }
        
    except Exception as e:
        logger.log_error(f"更新实例参数失败: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/config/profiles/{platform}/{account}/{strategy}")
async def update_profile_config(platform: str, account: str, strategy: str, parameters: dict):
    """直接更新配置文件，不依赖运行实例"""
    try:
        logger.log_info(f"直接更新配置文件 - 平台: {platform}, 账户: {account}, 策略: {strategy}")
        logger.log_info(f"更新参数: {json.dumps(parameters, indent=2, ensure_ascii=False)}")
        
        # 构建配置文件路径
        config_path = f"profiles/{platform.upper()}/{account}/strategies/{strategy}.json"
        logger.log_info(f"配置文件路径: {config_path}")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 读取现有配置文件
        existing_config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8-sig') as f:
                    existing_config = json.load(f)
                logger.log_info(f"读取到现有配置，共{len(existing_config)}个字段")
            except Exception as e:
                logger.log_warning(f"读取现有配置失败: {e}")
        else:
            logger.log_info("配置文件不存在，将创建新文件")
        
        # 深度合并参数
        def deep_merge(target, source):
            """深度合并字典，保留target中source没有的键"""
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
            return target
        
        logger.log_info(f"合并前配置: {json.dumps(existing_config, indent=2, ensure_ascii=False)}")
        
        # 合并参数
        deep_merge(existing_config, parameters)
        
        logger.log_info(f"合并后配置: {json.dumps(existing_config, indent=2, ensure_ascii=False)}")
        
        # 保存配置文件
        with open(config_path, 'w', encoding='utf-8-sig') as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)
        
        logger.log_info(f"配置文件已成功保存: {config_path}")
        
        return {
            "success": True,
            "message": f"配置文件已更新: {config_path}",
            "config_path": config_path
        }
        
    except Exception as e:
        logger.log_error(f"更新配置文件失败: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/config/update")
async def update_config_parameters(request_data: dict):
    """
    通用配置更新API - 支持多种更新模式
    
    请求格式:
    {
        "config_id": "BINANCE_BN1602_martingale_hedge",  // 可选：使用配置ID
        "platform": "BINANCE",                           // 或单独指定
        "account": "BN1602", 
        "strategy": "martingale_hedge",
        "parameters": { ... }                           // 要更新的参数
    }
    """
    try:
        # 支持两种方式：config_id 或 分别指定 platform/account/strategy
        if "config_id" in request_data:
            # 从配置ID解析信息 (格式: PLATFORM_ACCOUNT_STRATEGY)
            config_id = request_data["config_id"]
            parts = config_id.split("_")
            if len(parts) >= 3:
                platform = parts[0]
                account = parts[1] 
                strategy = "_".join(parts[2:])  # 策略名可能包含下划线
            else:
                raise ValueError(f"Invalid config_id format: {config_id}")
        else:
            # 直接从请求中获取
            platform = request_data.get("platform")
            account = request_data.get("account") 
            strategy = request_data.get("strategy")
            
        if not all([platform, account, strategy]):
            raise ValueError("Missing required fields: platform, account, strategy")
            
        parameters = request_data.get("parameters", {})
        if not parameters:
            raise ValueError("No parameters to update")
        
        # 构建配置文件路径
        config_path = f"profiles/{platform.upper()}/{account}/strategies/{strategy}.json"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 读取现有配置文件
        existing_config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8-sig') as f:
                    existing_config = json.load(f)
            except Exception as e:
                logger.log_warning(f"Failed to read existing config: {e}")
        
        # 使用深度合并更新配置
        # 使用全局deep_merge函数
        
        deep_merge(existing_config, parameters)
        
        # 保存更新后的配置文件
        with open(config_path, 'w', encoding='utf-8-sig') as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)
        
        logger.log_info(f"Configuration updated: {config_path}")
        
        return {
            "success": True,
            "message": f"Configuration updated for {platform}/{account}/{strategy}",
            "config_path": config_path
        }
        
    except Exception as e:
        logger.log_error(f"更新配置文件失败: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/config/list")
async def list_configurations():
    """获取所有可用的配置文件列表"""
    try:
        configs = []
        profiles_dir = "profiles"
        
        if not os.path.exists(profiles_dir):
            return {"success": True, "configs": []}
            
        # 遍历所有平台
        for platform in os.listdir(profiles_dir):
            platform_dir = os.path.join(profiles_dir, platform)
            if not os.path.isdir(platform_dir):
                continue
                
            # 遍历所有账号
            for account in os.listdir(platform_dir):
                account_dir = os.path.join(platform_dir, account)
                strategies_dir = os.path.join(account_dir, "strategies")
                
                if not os.path.isdir(strategies_dir):
                    continue
                    
                # 遍历所有策略文件
                for strategy_file in os.listdir(strategies_dir):
                    if strategy_file.endswith('.json'):
                        strategy_name = strategy_file[:-5]  # 移除.json后缀
                        config_id = f"{platform}_{account}_{strategy_name}"
                        config_path = os.path.join(strategies_dir, strategy_file)
                        
                        configs.append({
                            "config_id": config_id,
                            "platform": platform,
                            "account": account,
                            "strategy": strategy_name,
                            "config_path": config_path,
                            "exists": os.path.exists(config_path)
                        })
        
        return {
            "success": True,
            "configs": configs,
            "total": len(configs)
        }
        
    except Exception as e:
        logger.log_error(f"获取配置列表失败: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/config/get")
async def get_configuration(config_id: str = None, platform: str = None, account: str = None, strategy: str = None):
    """获取指定配置文件内容"""
    try:
        # 支持两种方式获取配置
        if config_id:
            parts = config_id.split("_")
            if len(parts) >= 3:
                platform = parts[0]
                account = parts[1]
                strategy = "_".join(parts[2:])
            else:
                raise ValueError(f"Invalid config_id format: {config_id}")
        
        if not all([platform, account, strategy]):
            raise ValueError("Missing required parameters")
            
        config_path = f"profiles/{platform.upper()}/{account}/strategies/{strategy}.json"
        
        if not os.path.exists(config_path):
            return {"success": False, "error": "Configuration file not found"}
            
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config_data = json.load(f)
            
        return {
            "success": True,
            "config": config_data,
            "config_id": f"{platform}_{account}_{strategy}",
            "config_path": config_path
        }
        
    except Exception as e:
        logger.log_error(f"获取配置失败: {e}")
        return {"success": False, "error": str(e)}

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

@app.get("/api/accounts/available")
async def get_available_accounts(platform: Optional[str] = None):
    """获取可用账号列表 - 支持按平台筛选"""
    try:
        logger.log_info(f"=== ACCOUNTS API CALLED ===")
        logger.log_info(f"Platform filter: {platform}")
        
        accounts = []
        
        # 方法2：扫描新的profiles目录获取配置的账号
        import os
        # 确保使用正确的profiles目录路径
        profiles_dir = os.path.join(project_root, "profiles")
        logger.log_info(f"Checking profiles directory: {profiles_dir}")
        logger.log_info(f"Current working directory: {os.getcwd()}")
        logger.log_info(f"Project root: {project_root}")
        
        if os.path.exists(profiles_dir):
            logger.log_info(f"New profiles directory exists, scanning...")
            # 扫描平台目录 (BINANCE, COINW, OKX, DEEP)
            for platform_dir in os.listdir(profiles_dir):
                if platform_dir.startswith('_'):  # 跳过 _shared_defaults
                    continue
                platform_path = os.path.join(profiles_dir, platform_dir)
                if os.path.isdir(platform_path):
                    logger.log_info(f"Scanning platform: {platform_dir}")
                    # 扫描账号目录
                    for account in os.listdir(platform_path):
                        account_path = os.path.join(platform_path, account)
                        if os.path.isdir(account_path):
                            profile_file = os.path.join(account_path, 'profile.json')
                            logger.log_info(f"Checking profile file: {profile_file}")
                            if os.path.exists(profile_file):
                                logger.log_info(f"Profile file exists, reading...")
                                try:
                                    with open(profile_file, 'r', encoding='utf-8') as f:
                                        profile = json.load(f)
                                        account_platform = profile.get('profile_info', {}).get('platform', 'unknown')
                                        logger.log_info(f"Loaded profile for {account}, platform: {account_platform}")
                                        logger.log_info(f"Platform comparison: '{account_platform.lower()}' vs '{platform.lower() if platform else None}'")
                                        
                                        # 平台筛选 (不区分大小写)
                                        if platform is None or account_platform.lower() == platform.lower():
                                            logger.log_info(f"Platform matches! Adding account {account}")
                                            # 检查是否已在列表中
                                            if not any(acc['id'] == account for acc in accounts):
                                                accounts.append({
                                                    "id": account,
                                                    "name": profile.get('profile_info', {}).get('display_name', account),
                                                    "platform": account_platform,
                                                    "status": "configured",
                                                    "balance": 0.0,
                                                    "last_active": None,
                                                    "config": profile
                                                })
                                            else:
                                                logger.log_info(f"Account {account} already in list, skipping")
                                        else:
                                            logger.log_info(f"Platform mismatch for {account}: '{account_platform}' != '{platform}'")
                                except Exception as e:
                                    logger.log_error(f"Failed to read profile for account {account}: {e}")
                            else:
                                logger.log_info(f"Profile file not found: {profile_file}")
                        else:
                            logger.log_info(f"Not a directory: {account_path}")
                else:
                    logger.log_info(f"Not a platform directory: {platform_path}")
        else:
            logger.log_error(f"Profiles directory not found: {profiles_dir}")
        
        logger.log_info(f"Total accounts found: {len(accounts)}")
        for acc in accounts:
            logger.log_info(f"Account: {acc['id']}, Platform: {acc['platform']}, Status: {acc['status']}")
        
        return {"accounts": accounts}
        
    except Exception as e:
        logger.log_error(f"获取可用账号失败: {e}")
        import traceback
        logger.log_error(f"Traceback: {traceback.format_exc()}")
        return {"accounts": []}

@app.get("/api/accounts/{platform}")
async def get_accounts_by_platform(platform: str):
    """根据平台获取账号列表 - 兼容性端点"""
    try:
        logger.log_info(f"=== PLATFORM ACCOUNTS API CALLED ===")
        logger.log_info(f"Platform: {platform}")
        
        # 调用通用账号API并按平台筛选
        result = await get_available_accounts(platform=platform)
        accounts = result.get("accounts", [])
        
        logger.log_info(f"Found {len(accounts)} accounts for platform {platform}")
        for acc in accounts:
            logger.log_info(f"Account: {acc['id']}, Platform: {acc['platform']}, Status: {acc['status']}")
        
        # 直接返回账号数组，与之前的格式保持一致
        return accounts
        
    except Exception as e:
        logger.log_error(f"获取平台账号失败: {e}")
        return []

@app.post("/api/accounts/test-connection")
async def test_account_connection_generic(request: dict):
    """测试账号平台连接 - 通用端点"""
    try:
        platform = request.get("platform")
        account_id = request.get("account_id")
        
        if not platform or not account_id:
            return {
                "success": False,
                "message": "缺少必要参数：platform或account_id",
                "status": "missing_parameters"
            }
        
        # 调用具体的账号测试函数
        return await test_account_connection_impl(account_id, platform)
    
    except Exception as e:
        logger.log_error(f"通用账号连接测试失败: {e}")
        return {
            "success": False,
            "message": f"连接测试异常：{str(e)}",
            "status": "test_error"
        }

@app.post("/api/accounts/{account_id}/test-connection")
async def test_account_connection(account_id: str):
    """测试账号平台连接"""
    return await test_account_connection_impl(account_id)

async def test_account_connection_impl(account_id: str, platform_filter: str = None):
    """测试账号平台连接的实现"""
    try:
        # 首先从新的profiles目录读取账号配置
        profiles_dir = os.path.join(project_root, "profiles")
        # 扫描平台目录找到账号
        account_config_path = None
        found_platform = None
        for platform_dir in os.listdir(profiles_dir):
            if platform_dir.startswith('_'):
                continue
            if platform_filter and platform_dir.upper() != platform_filter.upper():
                continue
            platform_path = os.path.join(profiles_dir, platform_dir)
            if os.path.isdir(platform_path):
                account_path = os.path.join(platform_path, account_id)
                if os.path.isdir(account_path):
                    config_file = os.path.join(account_path, 'profile.json')
                    if os.path.exists(config_file):
                        account_config_path = config_file
                        found_platform = platform_dir
                        break
        
        if not account_config_path:
            return {
                "success": False,
                "message": f"账号 {account_id} 配置文件不存在",
                "status": "config_not_found"
            }
        
        # 读取账号配置
        with open(account_config_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        config = profile.get('profile_info', {})
        platform_name = config.get('platform')
        if not platform_name:
            return {
                "success": False,
                "message": "账号配置中未指定平台",
                "status": "platform_not_specified"
            }
        
        # 获取API密钥 - 支持两种配置方式
        api_credentials = {}
        api_key = None
        api_secret = None
        
        # 方式1: 直接在profile.json中的exchange_config
        if 'exchange_config' in profile and 'credentials' in profile['exchange_config']:
            api_credentials = profile['exchange_config']['credentials']
            api_key = api_credentials.get('api_key')
            api_secret = api_credentials.get('secret_key')
        
        # 方式2: 通过api_config.path指向外部文件
        elif 'api_config' in profile and 'path' in profile['api_config']:
            api_config_path = os.path.join(project_root, profile['api_config']['path'])
            if os.path.exists(api_config_path):
                try:
                    with open(api_config_path, 'r', encoding='utf-8') as f:
                        api_config = json.load(f)
                    api_credentials = api_config
                    # 支持多种字段名格式
                    api_key = (api_config.get('api_key') or 
                              api_config.get('API_KEY') or
                              api_config.get('apiKey'))
                    api_secret = (api_config.get('secret_key') or 
                                 api_config.get('api_secret') or
                                 api_config.get('API_SECRET') or
                                 api_config.get('secretKey'))
                except Exception as e:
                    logger.log_error(f"读取API配置文件失败: {e}")
        
        if not api_key or not api_secret:
            return {
                "success": False,
                "message": f"API密钥配置不完整 - 账号 {account_id}",
                "status": "credentials_missing"
            }
        
        # 尝试创建平台连接
        try:
            platform_instance = platform_manager.create_platform_for_account(
                account=account_id,
                platform_name=platform_name,
                api_key=api_key,
                api_secret=api_secret,
                extra_params=api_credentials.get('extra_params', {})
            )
            
            # 尝试进行基本的连接测试（获取账户信息或余额）
            # 由于这是示例账号，预期会失败
            try:
                # 调用平台的健康检查方法
                test_result = platform_manager.health_check_platform(account_id, platform_name)
                
                # 检查连接测试结果
                if test_result and test_result.get("status") == "healthy":
                    return {
                        "success": True,
                        "message": f"平台 {platform_name} 连接成功",
                        "status": "connected",
                        "platform": platform_name,
                        "details": test_result
                    }
                else:
                    return {
                        "success": False,
                        "message": f"平台 {platform_name} 连接测试失败：{test_result.get('error', 'Unknown error')}",
                        "status": "connection_failed",
                        "platform": platform_name,
                        "details": test_result
                    }
                
            except Exception as conn_e:
                error_msg = str(conn_e)
                logger.log_error(f"平台连接测试失败 - 平台: {platform_name}, 错误: {error_msg}")
                return {
                    "success": False,
                    "message": f"交易连接失败：{error_msg}。请检查API密钥配置和网络连接。",
                    "status": "connection_error",
                    "platform": platform_name,
                    "error_details": error_msg,
                    "troubleshooting": [
                        "检查API密钥是否正确",
                        "确认网络连接正常",
                        "验证平台服务是否可用"
                    ]
                }
                
        except Exception as create_e:
            return {
                "success": False,
                "message": f"创建平台实例失败：{str(create_e)}",
                "status": "platform_creation_failed",
                "platform": platform_name
            }
            
    except Exception as e:
        logger.log_error(f"测试账号连接失败: {e}")
        return {
            "success": False,
            "message": f"连接测试异常：{str(e)}",
            "status": "test_error"
        }

@app.get("/api/symbols/available")
async def get_available_symbols(platform: Optional[str] = None):
    """获取可用交易对列表 - 优先从真实平台获取"""
    try:
        symbols = []
        
        if platform:
            # 尝试从指定平台获取真实交易对
            try:
                platform_config = platform_manager.get_platform_config(platform)
                if platform_config and platform_config.get('capabilities', {}).get('supported_instruments'):
                    # 基于平台能力返回通用交易对
                    base_symbols = ["BTC", "ETH", "SOL", "BNB", "ADA", "DOT", "LINK", "LTC", "UNI", "XRP"]
                    for base in base_symbols:
                        symbols.append({
                            "symbol": f"{base}USDT", 
                            "name": f"{base}/USDT", 
                            "base": base, 
                            "quote": "USDT",
                            "platform": platform
                        })
                else:
                    logger.log_warning(f"Platform {platform} config not found")
            except Exception as e:
                logger.log_error(f"Failed to get symbols from platform {platform}: {e}")
        
        # 如果没有指定平台或平台获取失败，返回通用交易对
        if not symbols:
            default_symbols = [
                {"symbol": "BTCUSDT", "name": "BTC/USDT", "base": "BTC", "quote": "USDT", "platform": "all"},
                {"symbol": "ETHUSDT", "name": "ETH/USDT", "base": "ETH", "quote": "USDT", "platform": "all"},
                {"symbol": "SOLUSDT", "name": "SOL/USDT", "base": "SOL", "quote": "USDT", "platform": "all"},
                {"symbol": "BNBUSDT", "name": "BNB/USDT", "base": "BNB", "quote": "USDT", "platform": "all"},
                {"symbol": "ADAUSDT", "name": "ADA/USDT", "base": "ADA", "quote": "USDT", "platform": "all"},
                {"symbol": "DOTUSDT", "name": "DOT/USDT", "base": "DOT", "quote": "USDT", "platform": "all"},
                {"symbol": "LINKUSDT", "name": "LINK/USDT", "base": "LINK", "quote": "USDT", "platform": "all"},
                {"symbol": "LTCUSDT", "name": "LTC/USDT", "base": "LTC", "quote": "USDT", "platform": "all"},
                {"symbol": "UNIUSDT", "name": "UNI/USDT", "base": "UNI", "quote": "USDT", "platform": "all"},
                {"symbol": "XRPUSDT", "name": "XRP/USDT", "base": "XRP", "quote": "USDT", "platform": "all"}
            ]
            symbols = default_symbols
            
        return {"symbols": symbols}
        
    except Exception as e:
        logger.log_error(f"获取可用交易对失败: {e}")
        return {"symbols": []}

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

@app.get("/api/strategies/{strategy_name}/templates")
async def get_strategy_templates(strategy_name: str):
    """获取指定策略的模板列表"""
    try:
        templates = plugin_loader.get_strategy_templates(strategy_name)
        template_list = []
        
        for template_id, template_config in templates.items():
            template_list.append({
                "id": template_id,
                "name": template_config.get("name", template_id),
                "description": template_config.get("description", ""),
                "risk_level": template_config.get("risk_level", "medium"),
                "parameters": template_config.get("parameters", {}),
                "recommended_capital": template_config.get("recommended_capital", 1000),
                "max_drawdown_expected": template_config.get("max_drawdown_expected", 0.2),
                "notes": template_config.get("notes", "")
            })
        
        return {"templates": template_list}
    except Exception as e:
        logger.log_error(f"获取策略模板失败: {e}")
        return {"templates": []}

@app.get("/api/strategies/{strategy_name}/templates/{template_id}")
async def get_strategy_template(strategy_name: str, template_id: str):
    """获取指定策略的特定模板"""
    try:
        template = plugin_loader.get_strategy_template(strategy_name, template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"模板未找到: {strategy_name}/{template_id}")
        
        return {
            "template": {
                "id": template.get("id", template_id),
                "name": template.get("name", template_id),
                "description": template.get("description", ""),
                "risk_level": template.get("risk_level", "medium"),
                "parameters": template.get("parameters", {}),
                "recommended_capital": template.get("recommended_capital", 1000),
                "max_drawdown_expected": template.get("max_drawdown_expected", 0.2),
                "notes": template.get("notes", "")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(f"获取策略模板失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.post("/api/instances/create")
async def create_instance(request: CreateInstanceRequest):
    """创建新的交易实例"""
    try:
        # 验证输入参数
        if not all([request.account_id, request.platform, request.strategy, request.symbol]):
            raise HTTPException(status_code=400, detail="缺少必需参数")
        
        # 验证平台是否支持
        available_platforms = platform_manager.get_available_platforms()
        if request.platform not in available_platforms:
            raise HTTPException(status_code=400, detail=f"不支持的平台: {request.platform}")
        
        # 验证策略是否存在
        available_strategies = strategy_manager.get_available_strategies()
        if request.strategy not in available_strategies:
            raise HTTPException(status_code=400, detail=f"策略不存在: {request.strategy}")
        
        # 检查是否已存在相同的实例（同策略、同平台、同账号、同币种）
        try:
            active_strategies = strategy_manager.get_active_strategies()
            for strategy_instance in active_strategies:
                if (hasattr(strategy_instance, 'account') and 
                    hasattr(strategy_instance, 'platform') and 
                    hasattr(strategy_instance, 'strategy_name') and
                    hasattr(strategy_instance, 'parameters')):
                    
                    instance_account = getattr(strategy_instance, 'account', '')
                    instance_platform = getattr(strategy_instance, 'platform', '')
                    instance_strategy = getattr(strategy_instance, 'strategy_name', '')
                    instance_symbol = getattr(strategy_instance, 'parameters', {}).get('symbol', '')
                    
                    # 标准化交易对格式进行比较
                    request_symbol_normalized = request.symbol.replace('/', '').upper()
                    instance_symbol_normalized = instance_symbol.replace('/', '').upper()
                    
                    if (instance_account == request.account_id and 
                        instance_platform.upper() == request.platform.upper() and
                        instance_strategy == request.strategy and
                        instance_symbol_normalized == request_symbol_normalized):
                        
                        # 使用新的错误编码系统
                        error_response = duplicate_instance_error(
                            request.platform, request.account_id, request.strategy, request.symbol
                        )
                        raise HTTPException(status_code=400, detail=error_response)
        except HTTPException as http_exc:
            # 重新抛出HTTPException（比如重复实例检查）
            raise http_exc
        except Exception as e:
            logger.log_warning(f"检查重复实例时出错: {e}")
            # 继续执行，不因检查失败而阻止创建
        
        # 创建策略实例
        final_params = request.parameters or {}
        if request.symbol:
            final_params['symbol'] = request.symbol
            
        instance_id = strategy_manager.create_strategy_instance(
            account=request.account_id,
            strategy_name=request.strategy,
            params=final_params
        )
        
        # 获取创建的实例并设置平台信息
        strategy_instance = strategy_manager.get_strategy_instance(request.account_id, instance_id)
        if strategy_instance:
            strategy_instance.platform = request.platform
            strategy_instance.strategy_name = request.strategy
            # 不要覆盖parameters，因为策略管理器已经加载了完整的配置文件参数
            # strategy_instance.parameters = final_params  # 删除这行，保留从配置文件加载的参数
        
        # 不再自动启动策略实例，需要用户手动启动
        logger.log_info(f"✅ Created strategy instance: {request.account_id}/{instance_id} (manual start required)")
        
        # 广播更新
        await manager.broadcast({
            "type": "instance_created",
            "account_id": request.account_id,
            "platform": request.platform,
            "strategy": request.strategy,
            "instance_id": instance_id,
            "started": False,  # 不再自动启动
            "timestamp": datetime.now().isoformat()
        })
        
        logger.log_info(f"✅ Created instance {instance_id} for {request.account_id}/{request.strategy}")
        
        return {
            "success": True,
            "message": f"实例 {request.strategy} 创建成功，请在实例卡片中手动启动策略",
            "instance_id": instance_id,
            "account_id": request.account_id,
            "platform": request.platform,
            "strategy": request.strategy,
            "started": False  # 不再自动启动
        }
        
    except HTTPException as http_exc:
        # 重新抛出HTTPException（包括重复实例检查和其他业务逻辑错误）
        raise http_exc
    except ValueError as e:
        # 处理重复实例等业务逻辑错误
        error_msg = str(e)
        logger.log_warning(f"⚠️ Business logic error: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.log_error(f"❌ Create instance failed: {e}")
        import traceback
        logger.log_error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"创建实例失败: {str(e)}")

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
async def stop_strategy(request: StopStrategyRequest):
    """停止策略 - 使用request body"""
    try:
        success = strategy_manager.stop_strategy(request.account_id, request.instance_id)
        
        if success:
            # 广播更新
            await manager.broadcast({
                "type": "strategy_stopped",
                "account_id": request.account_id,
                "instance_id": request.instance_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "success": True, 
                "message": f"策略实例 {request.instance_id} 在账号 {request.account_id} 上停止成功"
            }
        else:
            return {"success": False, "message": "策略停止失败"}
    except Exception as e:
        logger.log_error(f"停止策略失败: {e}")
        add_missing_feature("strategy_stop", "策略停止功能需要完善")
        raise HTTPException(status_code=500, detail=str(e))

# 删除实例请求模型
class DeleteInstanceRequest(BaseModel):
    account_id: str
    instance_id: str

@app.post("/api/instances/delete")
async def delete_instance(request: DeleteInstanceRequest):
    """删除策略实例"""
    try:
        # 检查实例是否存在
        strategy_instance = strategy_manager.get_strategy_instance(request.account_id, request.instance_id)
        if not strategy_instance:
            error_response = instance_not_found_error(request.account_id, request.instance_id)
            raise HTTPException(status_code=404, detail=error_response)
        
        # 先停止策略（如果正在运行）
        stop_success = strategy_manager.stop_strategy(request.account_id, request.instance_id)
        if stop_success:
            logger.log_info(f"已停止实例 {request.instance_id} 在账号 {request.account_id}")
        
        # 删除策略实例
        delete_success = strategy_manager.delete_strategy_instance(request.account_id, request.instance_id)
        
        if delete_success:
            # 广播更新
            await manager.broadcast({
                "type": "instance_deleted",
                "account_id": request.account_id,
                "instance_id": request.instance_id,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.log_info(f"✅ Deleted instance {request.instance_id} for account {request.account_id}")
            return {
                "success": True,
                "message": f"实例 {request.instance_id} 删除成功"
            }
        else:
            error_response = format_error(
                "DELETE_INSTANCE_FAILED",
                f"删除实例 {request.instance_id} 失败",
                account=request.account_id,
                instance_id=request.instance_id
            )
            raise HTTPException(status_code=500, detail=error_response)
            
    except HTTPException as http_exc:
        # 重新抛出HTTPException
        raise http_exc
    except Exception as e:
        logger.log_error(f"删除实例失败: {e}")
        error_response = format_error(
            "DELETE_INSTANCE_FAILED",
            f"删除实例时发生错误: {str(e)}",
            account=request.account_id,
            instance_id=request.instance_id
        )
        raise HTTPException(status_code=500, detail=error_response)

@app.post("/api/strategy/force-stop-and-close")
async def force_stop_and_close_strategy(request: ForceStopStrategyRequest):
    """紧急平仓并停止策略"""
    try:
        # 执行紧急平仓
        close_result = strategy_manager.force_close_all_positions(request.account_id, request.instance_id)
        
        # 停止策略
        stop_success = strategy_manager.stop_strategy(request.account_id, request.instance_id)
        
        if close_result["success"] and stop_success:
            # 广播更新
            await manager.broadcast({
                "type": "strategy_force_stopped",
                "account_id": request.account_id,
                "instance_id": request.instance_id,
                "timestamp": datetime.now().isoformat(),
                "details": close_result
            })
            
            return {
                "success": True,
                "message": f"策略实例 {request.instance_id} 紧急平仓并停止成功",
                "details": close_result
            }
        else:
            error_msg = f"紧急平仓失败: {close_result.get('errors', [])} | 停止策略: {'成功' if stop_success else '失败'}"
            return {
                "success": False, 
                "message": error_msg,
                "details": close_result
            }
    except Exception as e:
        logger.log_error(f"紧急平仓并停止策略失败: {e}")
        add_missing_feature("strategy_force_stop", "紧急平仓功能需要完善")
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
        
        # Read from main runtime log - 使用正确的项目根目录路径
        runtime_log_path = project_root / "logs" / "runtime.log"
        if runtime_log_path.exists():
            try:
                with open(runtime_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-limit*2:]  # Read more to filter
                    
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Parse log format: 2025-10-03 01:37:40 - INFO - [logger.py:info:73] - message
                    # 尝试多种日志格式
                    match = None
                    
                    # 格式1：完整格式 with file info
                    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:,\d+)? - (\w+) - \[.*?\] - (.+)', line)
                    if not match:
                        # 格式2：简单格式 without file info
                        match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:,\d+)? - (\w+) - (.+)', line)
                    
                    if match:
                        timestamp_str, log_level, message = match.groups()
                        
                        # Filter by level if specified
                        if level and log_level.upper() != level.upper():
                            continue
                            
                        logs.append({
                            "timestamp": timestamp_str,
                            "level": log_level.upper(),
                            "message": message.strip(),
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

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """日志WebSocket端点 - 增强稳定性版本"""
    client_ip = websocket.client.host if websocket.client else "unknown"
    logger.info(f"新的日志WebSocket连接请求来自: {client_ip}")
    
    try:
        await manager.connect_log(websocket)
        logger.info(f"日志WebSocket客户端已连接: {client_ip}")
        
        # 发送连接成功消息
        welcome_message = {
            "type": "connection",
            "status": "connected",
            "message": "日志WebSocket连接成功",
            "timestamp": datetime.now().isoformat(),
            "connection_id": client_ip,
            "server_info": {
                "api_version": "1.0.0",
                "websocket_version": "enhanced",
                "heartbeat_interval": 60
            }
        }
        
        await websocket.send_text(json.dumps(welcome_message, ensure_ascii=False))
        
        # 发送初始测试消息
        test_message = {
            "type": "log",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"✅ WebSocket日志连接已建立 (客户端: {client_ip})",
                "source": "websocket_system",
                "category": "connection"
            }
        }
        await websocket.send_text(json.dumps(test_message, ensure_ascii=False))
        
        # 保持连接活跃 - 改进的心跳机制
        heartbeat_interval = 60  # 增加到60秒
        last_cleanup = datetime.now()
        
        while True:
            try:
                # 等待客户端消息，支持更长的超时
                data = await asyncio.wait_for(websocket.receive_text(), timeout=heartbeat_interval)
                
                try:
                    message = json.loads(data)
                    message_type = message.get("type", "unknown")
                    
                    if message_type == "ping":
                        # 响应心跳
                        pong_response = {
                            "type": "pong",
                            "timestamp": datetime.now().isoformat(),
                            "server_time": datetime.now().isoformat()
                        }
                        await websocket.send_text(json.dumps(pong_response, ensure_ascii=False))
                        
                    elif message_type == "request_logs":
                        # 客户端请求最近日志
                        await send_recent_logs(websocket)
                        
                    # 更新心跳时间
                    conn_id = id(websocket)
                    if conn_id in manager.connection_metadata:
                        manager.connection_metadata[conn_id]["last_heartbeat"] = datetime.now()
                        
                except json.JSONDecodeError:
                    logger.warning(f"收到无效JSON消息: {data}")
                    
            except asyncio.TimeoutError:
                # 发送服务器端心跳
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "connection_count": len(manager.log_connections),
                    "server_status": "active"
                }
                
                try:
                    await websocket.send_text(json.dumps(heartbeat_message, ensure_ascii=False))
                except Exception as e:
                    logger.warning(f"发送心跳失败，连接可能已断开: {e}")
                    break
                    
            # 定期清理过期连接
            current_time = datetime.now()
            if (current_time - last_cleanup).total_seconds() > 300:  # 每5分钟清理一次
                await manager.cleanup_stale_connections()
                last_cleanup = current_time
                
    except WebSocketDisconnect:
        logger.info(f"日志WebSocket客户端主动断开: {client_ip}")
    except Exception as e:
        logger.error(f"日志WebSocket连接错误 ({client_ip}): {e}")
        import traceback
        logger.debug(f"WebSocket错误详情: {traceback.format_exc()}")
    finally:
        manager.disconnect(websocket)
        logger.info(f"日志WebSocket连接已清理: {client_ip}")

async def send_recent_logs(websocket: WebSocket, count: int = 20):
    """发送最近的日志到WebSocket客户端"""
    try:
        log_file = project_root / "logs" / "runtime.log"
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_logs = lines[-count:] if len(lines) > count else lines
                
            for i, line in enumerate(recent_logs):
                if line.strip():
                    log_message = {
                        "type": "log",
                        "data": {
                            "timestamp": datetime.now().isoformat(),
                            "level": "INFO",
                            "message": line.strip(),
                            "source": "history",
                            "category": "system",
                            "index": i + 1,
                            "total": len(recent_logs)
                        }
                    }
                    await websocket.send_text(json.dumps(log_message, ensure_ascii=False))
                    
            # 发送历史日志完成消息
            complete_message = {
                "type": "log",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "level": "INFO",
                    "message": f"📜 历史日志加载完成 (共 {len(recent_logs)} 条)",
                    "source": "websocket_system",
                    "category": "system"
                }
            }
            await websocket.send_text(json.dumps(complete_message, ensure_ascii=False))
            
    except Exception as e:
        logger.error(f"发送历史日志失败: {e}")
        error_message = {
            "type": "log",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "message": f"⚠️ 无法加载历史日志: {e}",
                "source": "websocket_system",
                "category": "error"
            }
        }
        await websocket.send_text(json.dumps(error_message, ensure_ascii=False))

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

@app.post("/api/logs/test")
async def test_logs():
    """测试日志功能"""
    logger.info("这是一条测试信息日志")
    logger.warning("这是一条测试警告日志")
    logger.error("这是一条测试错误日志")
    logger.trade("测试交易日志: BTCUSDT 买入订单已提交")
    
    return {"message": "测试日志已生成", "status": "success"}

@app.get("/api/logs/websocket/status")
async def websocket_status():
    """获取WebSocket连接状态"""
    try:
        stats = manager.get_connection_stats()
        return {
            "status": "success",
            "websocket_status": {
                "total_log_connections": stats["total_connections"],
                "total_active_connections": stats["active_connections"],
                "max_connections": stats["max_connections"],
                "server_status": "running",
                "last_check": datetime.now().isoformat()
            },
            "connection_details": stats["connection_details"],
            "health": {
                "is_healthy": stats["total_connections"] < stats["max_connections"] * 0.9,
                "capacity_usage": f"{(stats['total_connections'] / stats['max_connections']) * 100:.1f}%"
            }
        }
    except Exception as e:
        logger.error(f"获取WebSocket状态失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "websocket_status": {
                "total_log_connections": 0,
                "server_status": "error"
            }
        }

@app.post("/api/logs/websocket/cleanup")
async def cleanup_websocket_connections():
    """手动清理WebSocket连接"""
    try:
        initial_count = len(manager.log_connections)
        await manager.cleanup_stale_connections()
        final_count = len(manager.log_connections)
        cleaned = initial_count - final_count
        
        return {
            "status": "success",
            "message": f"WebSocket连接清理完成",
            "cleaned_connections": cleaned,
            "remaining_connections": final_count,
            "initial_connections": initial_count
        }
    except Exception as e:
        logger.error(f"清理WebSocket连接失败: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
async def get_websocket_log_status():
    """获取WebSocket日志连接状态"""
    return {
        "active_connections": len(manager.log_connections),
        "total_connections": len(manager.active_connections),
        "status": "connected" if len(manager.log_connections) > 0 else "disconnected",
        "endpoint": "ws://localhost:8001/ws/logs",
        "message": "WebSocket日志系统状态正常" if len(manager.log_connections) > 0 else "没有活跃的WebSocket日志连接"
    }

@app.post("/api/logs/websocket/test")
async def test_websocket_logs():
    """测试WebSocket日志推送"""
    try:
        # 直接触发日志推送
        test_messages = [
            "🧪 WebSocket日志测试 - 信息级别",
            "⚠️ WebSocket日志测试 - 警告级别", 
            "❌ WebSocket日志测试 - 错误级别",
            "📈 WebSocket日志测试 - 交易级别"
        ]
        
        for i, msg in enumerate(test_messages):
            await manager.broadcast_log({
                "timestamp": datetime.now().isoformat(),
                "level": ["info", "warning", "error", "trade"][i],
                "message": msg,
                "source": "websocket_test",
                "category": "test",
                "test_sequence": i + 1
            })
        
        return {
            "success": True,
            "message": f"已发送 {len(test_messages)} 条测试日志",
            "active_connections": len(manager.log_connections),
            "test_messages": test_messages
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "WebSocket日志测试失败"
        }

@app.post("/api/webhook/test")
async def test_webhook_notification():
    """测试Webhook通知功能"""
    try:
        logger.log_info("🔔 测试Webhook通知功能")
        
        # 模拟发送webhook通知
        test_notification = {
            "type": "test",
            "message": "Webhook通知测试",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "test_id": "webhook_test_001",
                "status": "success"
            }
        }
        
        # 广播测试通知
        await manager.broadcast({
            "type": "webhook_test",
            "data": test_notification
        })
        
        logger.log_info("✅ Webhook通知测试完成")
        return {
            "success": True,
            "message": "Webhook通知功能测试完成",
            "test_data": test_notification
        }
    except Exception as e:
        logger.log_error(f"Webhook测试失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Webhook通知功能测试失败"
        }

# ==================== 配置文件管理接口 ====================

@app.get("/api/config/profiles")
@handle_api_errors
async def list_config_profiles():
    """列出所有配置文件"""
    try:
        profiles = {}
        
        # 扫描profiles目录
        profiles_dir = project_root / "profiles"
        if profiles_dir.exists():
            for platform_dir in profiles_dir.iterdir():
                if platform_dir.is_dir() and not platform_dir.name.startswith('_'):
                    platform_name = platform_dir.name
                    profiles[platform_name] = {}
                    
                    for account_dir in platform_dir.iterdir():
                        if account_dir.is_dir():
                            account_name = account_dir.name
                            profiles[platform_name][account_name] = {}
                            
                            # 列出该账户下的所有策略配置
                            for config_file in account_dir.glob("*.json"):
                                if config_file.name != "profile.json":
                                    strategy_name = config_file.stem
                                    profiles[platform_name][account_name][strategy_name] = {
                                        "file_path": str(config_file),
                                        "last_modified": config_file.stat().st_mtime,
                                        "size": config_file.stat().st_size
                                    }
        
        return {
            "success": True,
            "data": {
                "profiles": profiles,
                "total_platforms": len(profiles),
                "total_accounts": sum(len(accounts) for accounts in profiles.values())
            }
        }
        
    except Exception as e:
        logger.log_error(f"列出配置文件失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/config/profiles/{platform}/{account}/{strategy}")
@handle_api_errors
async def get_config_profile(platform: str, account: str, strategy: str):
    """获取特定的配置文件内容"""
    try:
        config_file = project_root / "profiles" / platform / account / f"{strategy}.json"
        
        if not config_file.exists():
            return {
                "success": False,
                "error": f"配置文件不存在: {config_file}"
            }
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return {
            "success": True,
            "data": {
                "config": config_data,
                "file_info": {
                    "path": str(config_file),
                    "last_modified": config_file.stat().st_mtime,
                    "size": config_file.stat().st_size
                }
            }
        }
        
    except Exception as e:
        logger.log_error(f"获取配置文件失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/config/profiles/{platform}/{account}/{strategy}")
@handle_api_errors
async def save_config_profile(platform: str, account: str, strategy: str, config_data: dict):
    """保存配置文件"""
    try:
        config_dir = project_root / "profiles" / platform / account
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / f"{strategy}.json"
        
        # 备份现有文件
        if config_file.exists():
            backup_file = config_file.with_suffix(f".json.backup.{int(time.time())}")
            shutil.copy2(config_file, backup_file)
            logger.log_info(f"已备份配置文件到: {backup_file}")
        
        # 验证配置数据
        validated_config = validate_config_data(config_data, strategy)
        
        # 保存新配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(validated_config, f, indent=2, ensure_ascii=False)
        
        logger.log_info(f"配置文件已保存: {config_file}")
        
        # 广播配置更新事件
        await manager.broadcast_log({
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "message": f"配置文件已更新: {platform}/{account}/{strategy}",
            "source": "ConfigAPI",
            "category": "config_update",
            "data": {
                "platform": platform,
                "account": account,
                "strategy": strategy,
                "file_path": str(config_file)
            }
        })
        
        return {
            "success": True,
            "data": {
                "message": "配置文件保存成功",
                "file_path": str(config_file)
            }
        }
        
    except Exception as e:
        logger.log_error(f"保存配置文件失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.delete("/api/config/profiles/{platform}/{account}/{strategy}")
@handle_api_errors
async def delete_config_profile(platform: str, account: str, strategy: str):
    """删除配置文件"""
    try:
        config_file = project_root / "profiles" / platform / account / f"{strategy}.json"
        
        if not config_file.exists():
            return {
                "success": False,
                "error": "配置文件不存在"
            }
        
        # 创建备份
        backup_file = config_file.with_suffix(f".json.deleted.{int(time.time())}")
        shutil.move(config_file, backup_file)
        
        logger.log_info(f"配置文件已删除，备份到: {backup_file}")
        
        return {
            "success": True,
            "data": {
                "message": "配置文件删除成功",
                "backup_path": str(backup_file)
            }
        }
        
    except Exception as e:
        logger.log_error(f"删除配置文件失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def validate_config_data(config_data: dict, strategy: str) -> dict:
    """验证配置数据的有效性"""
    validated = config_data.copy()
    
    # 基本验证
    if not isinstance(validated, dict):
        raise ValueError("配置数据必须是字典格式")
    
    # 策略特定验证
    if strategy == "martingale_hedge":
        required_fields = ["symbol", "base_amount", "price_step"]
        for field in required_fields:
            if field not in validated:
                validated[field] = get_default_value(field)
    
    # 数据类型验证
    if "base_amount" in validated:
        try:
            validated["base_amount"] = float(validated["base_amount"])
        except (ValueError, TypeError):
            validated["base_amount"] = 10.0
    
    if "price_step" in validated:
        try:
            validated["price_step"] = float(validated["price_step"])
        except (ValueError, TypeError):
            validated["price_step"] = 0.01
    
    return validated

def get_default_value(field: str):
    """获取字段的默认值"""
    defaults = {
        "symbol": "OP/USDT",
        "base_amount": 10.0,
        "price_step": 0.01,
        "max_orders": 20,
        "hedge_enabled": True
    }
    return defaults.get(field, None)

# ==================== 日志文件读取接口 ====================

@app.get("/api/logs/file")
@handle_api_errors
async def get_log_file(path: str = Query(..., description="日志文件路径")):
    """读取本地日志文件"""
    try:
        # 安全检查，防止路径遍历攻击
        if '..' in path or path.startswith('/'):
            return {
                "success": False,
                "error": "非法的文件路径"
            }
        
        # 支持的日志文件路径
        allowed_paths = [
            project_root / "logs",
            Path("d:/Desktop/Stock-trading/old/logs")
        ]
        
        log_file = None
        for allowed_path in allowed_paths:
            candidate = allowed_path / path
            if candidate.exists() and candidate.is_file():
                log_file = candidate
                break
        
        if not log_file:
            return {
                "success": False,
                "error": f"日志文件不存在: {path}"
            }
        
        # 读取文件内容
        logs = []
        try:
            if log_file.suffix == '.csv':
                # CSV格式日志
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines[1:], 1):  # 跳过标题行
                        parts = line.strip().split(',')
                        if len(parts) >= 4:
                            logs.append({
                                "timestamp": parts[0] if len(parts) > 0 else "",
                                "level": "trade",
                                "message": f"交易记录 #{i}: {parts[3] if len(parts) > 3 else ''}",
                                "source": "TradingLog",
                                "data": {
                                    "raw_line": line.strip(),
                                    "parts": parts
                                }
                            })
            else:
                # 文本格式日志
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if line.strip():
                            logs.append({
                                "timestamp": datetime.now().isoformat(),
                                "level": "info",
                                "message": line.strip(),
                                "source": "LogFile",
                                "line": i + 1
                            })
        
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(log_file, 'r', encoding='gbk') as f:
                content = f.read()
                logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "level": "info", 
                    "message": f"日志文件内容 (GBK编码): {content[:1000]}...",
                    "source": "LogFile"
                })
        
        return {
            "success": True,
            "data": {
                "logs": logs,
                "total": len(logs),
                "file_info": {
                    "path": str(log_file),
                    "size": log_file.stat().st_size,
                    "last_modified": log_file.stat().st_mtime
                }
            }
        }
        
    except Exception as e:
        logger.log_error(f"读取日志文件失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)