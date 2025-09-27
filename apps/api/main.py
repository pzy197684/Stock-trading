# apps/api/main.py
# 功能：简单的API服务器，为前端UI提供数据接口
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.managers.platform_manager import get_platform_manager
from core.managers.strategy_manager_new import get_strategy_manager
from core.state_store import get_state_manager
from core.utils.plugin_loader import get_plugin_loader
from core.logger import logger

app = FastAPI(
    title="Stock Trading API",
    description="API服务为股票交易系统前端提供数据接口",
    version="1.0.0"
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React开发服务器端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取管理器实例
platform_manager = get_platform_manager()
strategy_manager = get_strategy_manager() 
state_manager = get_state_manager()
plugin_loader = get_plugin_loader()

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Stock Trading API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": state_manager._get_iso_timestamp(),
        "components": {
            "platform_manager": "ok",
            "strategy_manager": "ok",
            "state_manager": "ok",
            "plugin_loader": "ok"
        }
    }

# === 账号管理接口 ===
@app.get("/api/accounts")
async def list_accounts():
    """获取所有账号列表"""
    try:
        accounts = state_manager.list_accounts()
        return {"accounts": accounts}
    except Exception as e:
        logger.log_error(f"Failed to list accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/accounts/{account}/summary")
async def get_account_summary(account: str):
    """获取账号摘要信息"""
    try:
        # 状态摘要
        state_summary = state_manager.get_state_summary(account)
        
        # 平台摘要
        platform_summary = platform_manager.get_account_summary(account)
        
        # 策略摘要
        strategy_instances = strategy_manager.list_strategy_instances(account)
        
        return {
            "account": account.upper(),
            "state": state_summary,
            "platforms": platform_summary,
            "strategies": strategy_instances.get(account.upper(), [])
        }
    except Exception as e:
        logger.log_error(f"Failed to get account summary for {account}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/accounts/{account}/state")
async def get_account_state(account: str):
    """获取账号详细状态"""
    try:
        state = state_manager.load_state(account)
        return {
            "account": account.upper(),
            "state": state_manager._account_state_to_dict(state)
        }
    except Exception as e:
        logger.log_error(f"Failed to get state for account {account}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 平台管理接口 ===
@app.get("/api/platforms")
async def list_available_platforms():
    """获取所有可用平台列表"""
    try:
        platforms = platform_manager.get_available_platforms()
        platform_configs = {}
        
        for platform_name in platforms:
            config = platform_manager.get_platform_config(platform_name)
            if config:
                platform_configs[platform_name] = {
                    "name": config.get("name"),
                    "display_name": config.get("display_name"),
                    "description": config.get("description"),
                    "capabilities": config.get("capabilities", {}),
                    "supported_instruments": config.get("supported_instruments", [])
                }
        
        return {
            "platforms": platforms,
            "configs": platform_configs
        }
    except Exception as e:
        logger.log_error(f"Failed to list platforms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms/instances")
async def list_platform_instances(account: Optional[str] = Query(None)):
    """列出平台实例"""
    try:
        instances = platform_manager.list_platforms(account)
        return {"instances": instances}
    except Exception as e:
        logger.log_error(f"Failed to list platform instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/platforms/{account}/{platform_name}/create")
async def create_platform_instance(account: str, platform_name: str, config: Optional[Dict[str, Any]] = None):
    """创建平台实例"""
    try:
        if config is None:
            config = {}
        
        instance = platform_manager.create_platform_for_account(
            account=account,
            platform_name=platform_name,
            **config
        )
        
        return {
            "success": True,
            "message": f"Platform instance created: {account}/{platform_name}",
            "platform_name": instance.name() if hasattr(instance, 'name') else platform_name
        }
    except Exception as e:
        logger.log_error(f"Failed to create platform instance {account}/{platform_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/platforms/{account}/{platform_name}/health-check")
async def health_check_platform(account: str, platform_name: str):
    """平台健康检查"""
    try:
        result = platform_manager.health_check_platform(account, platform_name)
        return result
    except Exception as e:
        logger.log_error(f"Failed to health check platform {account}/{platform_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 策略管理接口 ===
@app.get("/api/strategies")
async def list_available_strategies():
    """获取所有可用策略列表"""
    try:
        strategies = strategy_manager.get_available_strategies()
        strategy_configs = {}
        
        for strategy_name in strategies:
            config = strategy_manager.get_strategy_config(strategy_name)
            if config:
                strategy_configs[strategy_name] = {
                    "name": config.get("name"),
                    "display_name": config.get("display_name"),
                    "description": config.get("description"),
                    "category": config.get("category"),
                    "risk_level": config.get("risk_level"),
                    "supported_platforms": config.get("supported_platforms", []),
                    "default_params": config.get("default_params", {}),
                    "param_schema": config.get("param_schema", {})
                }
        
        return {
            "strategies": strategies,
            "configs": strategy_configs
        }
    except Exception as e:
        logger.log_error(f"Failed to list strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies/instances")
async def list_strategy_instances(account: Optional[str] = Query(None)):
    """列出策略实例"""
    try:
        instances = strategy_manager.list_strategy_instances(account)
        return {"instances": instances}
    except Exception as e:
        logger.log_error(f"Failed to list strategy instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies/status")
async def get_strategy_status_summary():
    """获取策略状态摘要"""
    try:
        summary = strategy_manager.get_strategy_status_summary()
        return summary
    except Exception as e:
        logger.log_error(f"Failed to get strategy status summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies/{account}/{strategy_name}/create")
async def create_strategy_instance(account: str, strategy_name: str, config: Optional[Dict[str, Any]] = None):
    """创建策略实例"""
    try:
        if config is None:
            config = {}
        
        params = config.get("params", {})
        instance_config = config.get("instance_config", {})
        
        instance_id = strategy_manager.create_strategy_instance(
            account=account,
            strategy_name=strategy_name,
            params=params,
            instance_config=instance_config
        )
        
        return {
            "success": True,
            "message": f"Strategy instance created: {account}/{instance_id}",
            "instance_id": instance_id
        }
    except Exception as e:
        logger.log_error(f"Failed to create strategy instance {account}/{strategy_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/strategies/{account}/{instance_id}/start")
async def start_strategy_instance(account: str, instance_id: str):
    """启动策略实例"""
    try:
        success = strategy_manager.start_strategy(account, instance_id)
        if success:
            return {"success": True, "message": f"Strategy started: {account}/{instance_id}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to start strategy")
    except Exception as e:
        logger.log_error(f"Failed to start strategy {account}/{instance_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies/{account}/{instance_id}/pause")
async def pause_strategy_instance(account: str, instance_id: str):
    """暂停策略实例"""
    try:
        success = strategy_manager.pause_strategy(account, instance_id)
        if success:
            return {"success": True, "message": f"Strategy paused: {account}/{instance_id}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to pause strategy")
    except Exception as e:
        logger.log_error(f"Failed to pause strategy {account}/{instance_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies/{account}/{instance_id}/stop")
async def stop_strategy_instance(account: str, instance_id: str):
    """停止策略实例"""
    try:
        success = strategy_manager.stop_strategy(account, instance_id)
        if success:
            return {"success": True, "message": f"Strategy stopped: {account}/{instance_id}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop strategy")
    except Exception as e:
        logger.log_error(f"Failed to stop strategy {account}/{instance_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/strategies/{account}/{instance_id}")
async def remove_strategy_instance(account: str, instance_id: str):
    """删除策略实例"""
    try:
        success = strategy_manager.remove_strategy_instance(account, instance_id)
        if success:
            return {"success": True, "message": f"Strategy removed: {account}/{instance_id}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to remove strategy")
    except Exception as e:
        logger.log_error(f"Failed to remove strategy {account}/{instance_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 系统管理接口 ===
@app.post("/api/system/reload-plugins")
async def reload_plugins():
    """重新加载插件"""
    try:
        plugin_loader.reload_plugins()
        platform_manager.reload_plugins() 
        strategy_manager.reload_plugins()
        
        return {
            "success": True,
            "message": "Plugins reloaded successfully",
            "timestamp": state_manager._get_iso_timestamp()
        }
    except Exception as e:
        logger.log_error(f"Failed to reload plugins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/status")
async def get_system_status():
    """获取系统状态"""
    try:
        # 平台状态
        platform_health = platform_manager.health_check_all()
        
        # 策略状态
        strategy_summary = strategy_manager.get_strategy_status_summary()
        
        # 账号状态
        accounts = state_manager.get_all_accounts_summary()
        
        return {
            "platforms": platform_health,
            "strategies": strategy_summary,
            "accounts": accounts,
            "timestamp": state_manager._get_iso_timestamp()
        }
    except Exception as e:
        logger.log_error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === 异常处理器 ===
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": f"Path {request.url.path} not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.log_error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.log_info("🚀 Starting Stock Trading API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root / "core"), str(project_root / "apps" / "api")]
    )