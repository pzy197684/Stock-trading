# core/managers/platform_manager.py
# 功能：重构后的平台管理器，支持插件化、账号隔离、多实例管理
from typing import Optional, Dict, List, Any
import os

from core.platform.base import ExchangeIf
from core.config_loader import load_api_keys
from core.logger import logger
from core.utils.plugin_loader import get_plugin_loader
from core.state_store import get_state_manager

class PlatformManager:
    """
    平台管理器
    
    功能：
    1. 插件化平台适配器加载
    2. 账号隔离的平台实例管理
    3. 配置和密钥管理
    4. 平台能力查询
    5. 健康检查和状态监控
    """

    def __init__(self):
        self.plugin_loader = get_plugin_loader()
        self.state_manager = get_state_manager()
        
        # 存放已创建的实例：{ account: { platform_name: instance } }
        self.platforms: Dict[str, Dict[str, ExchangeIf]] = {}
        
        # 平台实例的元信息：{ account: { platform_name: metadata } }
        self.platform_metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # 加载平台插件
        self._load_platform_plugins()

    def _load_platform_plugins(self):
        """加载平台插件"""
        try:
            plugins = self.plugin_loader.scan_platform_plugins()
            logger.log_info(f"🔌 Loaded {len(plugins)} platform plugins: {list(plugins.keys())}")
        except Exception as e:
            logger.log_error(f"❌ Failed to load platform plugins: {e}")

    def _ensure_account_slot(self, account: str):
        """确保账号槽位存在"""
        account = account.upper()
        if account not in self.platforms:
            self.platforms[account] = {}
            self.platform_metadata[account] = {}

    def get_available_platforms(self) -> List[str]:
        """获取所有可用平台列表"""
        return self.plugin_loader.list_available_platforms()

    def get_platform_config(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """获取平台配置"""
        return self.plugin_loader.get_platform_config(platform_name)

    def create_platform_for_account(self, account: str, platform_name: str, 
                                  api_key: Optional[str] = None, 
                                  api_secret: Optional[str] = None,
                                  extra_params: Optional[Dict[str, Any]] = None,
                                  **kwargs) -> ExchangeIf:
        """
        为指定账号创建并缓存平台实例
        
        Args:
            account: 账号名
            platform_name: 平台名称
            api_key: API密钥（可选，优先级最高）
            api_secret: API秘密（可选，优先级最高）
            extra_params: 额外参数（如passphrase等）
            **kwargs: 其他配置参数
            
        Returns:
            平台实例
            
        Raises:
            ValueError: 平台不存在或密钥无效
        """
        account = account.upper()
        
        # 获取平台类
        platform_class = self.plugin_loader.get_platform_class(platform_name)
        if not platform_class:
            raise ValueError(f"Platform not found or failed to load: {platform_name}")
        
        # 获取API密钥
        if not api_key or not api_secret:
            try:
                loaded_key, loaded_secret = load_api_keys(exchange=platform_name, account=account)
                api_key = api_key or loaded_key
                api_secret = api_secret or loaded_secret
            except Exception as e:
                logger.log_warning(f"Failed to load API keys for {account}/{platform_name}: {e}")

        if not api_key or not api_secret:
            raise ValueError(f"API keys for account='{account}', platform='{platform_name}' not found")

        # 获取平台配置
        platform_config = self.get_platform_config(platform_name)
        if not platform_config:
            raise ValueError(f"Platform config not found: {platform_name}")

        # 合并配置参数
        init_params = {
            "api_key": api_key,
            "api_secret": api_secret,
        }
        
        # 添加额外参数（如OKX的passphrase）
        if extra_params:
            init_params.update(extra_params)
        
        # 添加其他配置参数
        if kwargs:
            init_params.update(kwargs)

        # 创建实例
        try:
            instance = platform_class(**init_params)
            
            # 存储实例和元信息
            self._ensure_account_slot(account)
            self.platforms[account][platform_name] = instance
            self.platform_metadata[account][platform_name] = {
                "account": account,
                "platform": platform_name,
                "created_at": self.state_manager._get_iso_timestamp(),
                "status": "active",
                "config": platform_config,
                "capabilities": instance.capabilities() if hasattr(instance, 'capabilities') else {},
                "last_health_check": None
            }
            
            # 更新账号状态
            try:
                state = self.state_manager.load_state(account)
                state.metadata["platform"] = platform_name
                state.metadata["status"] = "connected"
                self.state_manager.save_state(account, state)
            except Exception as e:
                logger.log_warning(f"Failed to update state for account {account}: {e}")
            
            logger.log_info(f"✅ Created platform instance: {account}/{platform_name}")
            return instance
            
        except Exception as e:
            logger.log_error(f"❌ Failed to create platform instance {account}/{platform_name}: {e}")
            raise

    def add_platform_for_account(self, account: str, platform_name: str, 
                                platform_instance: ExchangeIf, 
                                metadata: Optional[Dict[str, Any]] = None):
        """
        手动添加平台实例到指定账号
        
        Args:
            account: 账号名
            platform_name: 平台名称
            platform_instance: 平台实例
            metadata: 元信息
        """
        account = account.upper()
        self._ensure_account_slot(account)
        
        self.platforms[account][platform_name] = platform_instance
        self.platform_metadata[account][platform_name] = metadata or {
            "account": account,
            "platform": platform_name,
            "created_at": self.state_manager._get_iso_timestamp(),
            "status": "active",
            "manual_added": True
        }
        
        logger.log_info(f"✅ Added platform instance: {account}/{platform_name}")

    def get_platform(self, platform_name: str, account: Optional[str] = None) -> ExchangeIf:
        """
        获取平台实例
        
        Args:
            platform_name: 平台名称
            account: 账号名（可选）
            
        Returns:
            平台实例
            
        Raises:
            ValueError: 实例不存在或参数错误
        """
        if account:
            # 指定账号模式
            account = account.upper()
            acct_map = self.platforms.get(account, {})
            instance = acct_map.get(platform_name)
            if instance:
                return instance
            
            # 实例不存在，提供创建建议
            available_platforms = self.get_available_platforms()
            if platform_name in available_platforms:
                raise ValueError(
                    f"Platform '{platform_name}' available but no instance for account '{account}'. "
                    f"Use create_platform_for_account('{account}', '{platform_name}')"
                )
            else:
                raise ValueError(f"Unknown platform: {platform_name}. Available: {available_platforms}")
        
        # 自动模式：尝试找到唯一匹配实例
        found = []
        for acct, platform_map in self.platforms.items():
            if platform_name in platform_map:
                found.append((acct, platform_map[platform_name]))
        
        if len(found) == 1:
            logger.log_info(f"🔍 Auto-selected platform instance: {found[0][0]}/{platform_name}")
            return found[0][1]
        elif len(found) > 1:
            accounts = [acct for acct, _ in found]
            raise ValueError(
                f"Multiple accounts have platform '{platform_name}': {accounts}. "
                f"Please specify account parameter"
            )
        else:
            # 未找到任何实例
            available_platforms = self.get_available_platforms()
            if platform_name in available_platforms:
                raise ValueError(
                    f"Platform '{platform_name}' available but no instance created. "
                    f"Use create_platform_for_account(account, '{platform_name}')"
                )
            else:
                raise ValueError(f"Unknown platform: {platform_name}. Available: {available_platforms}")

    def list_platforms(self, account: Optional[str] = None) -> Dict[str, Any]:
        """
        列出平台实例
        
        Args:
            account: 账号名（可选）
            
        Returns:
            平台列表信息
        """
        if account:
            account = account.upper()
            instances = self.platforms.get(account, {})
            metadata = self.platform_metadata.get(account, {})
            return {
                "account": account,
                "platforms": list(instances.keys()),
                "metadata": metadata
            }
        
        # 返回所有账号的平台信息
        result = {}
        for acct in self.platforms.keys():
            result[acct] = {
                "platforms": list(self.platforms[acct].keys()),
                "metadata": self.platform_metadata.get(acct, {})
            }
        return result

    def remove_platform(self, account: str, platform_name: str) -> bool:
        """
        移除平台实例
        
        Args:
            account: 账号名
            platform_name: 平台名称
            
        Returns:
            移除是否成功
        """
        try:
            account = account.upper()
            if account in self.platforms and platform_name in self.platforms[account]:
                del self.platforms[account][platform_name]
                
                if account in self.platform_metadata and platform_name in self.platform_metadata[account]:
                    del self.platform_metadata[account][platform_name]
                
                logger.log_info(f"🗑️  Removed platform instance: {account}/{platform_name}")
                return True
            else:
                logger.log_warning(f"⚠️  Platform instance not found: {account}/{platform_name}")
                return False
                
        except Exception as e:
            logger.log_error(f"❌ Failed to remove platform instance {account}/{platform_name}: {e}")
            return False

    def health_check_platform(self, account: str, platform_name: str) -> Dict[str, Any]:
        """
        平台健康检查
        
        Args:
            account: 账号名
            platform_name: 平台名称
            
        Returns:
            健康检查结果
        """
        try:
            instance = self.get_platform(platform_name, account)
            
            # 基础连接测试（尝试获取账户信息）
            if hasattr(instance, 'get_account_info'):
                result = instance.get_account_info()
                if result.get("error"):
                    return {
                        "status": "unhealthy",
                        "error": result.get("reason", "Unknown error"),
                        "timestamp": self.state_manager._get_iso_timestamp()
                    }
            
            # 更新元信息
            if account.upper() in self.platform_metadata and platform_name in self.platform_metadata[account.upper()]:
                self.platform_metadata[account.upper()][platform_name]["last_health_check"] = self.state_manager._get_iso_timestamp()
                self.platform_metadata[account.upper()][platform_name]["status"] = "healthy"
            
            return {
                "status": "healthy",
                "timestamp": self.state_manager._get_iso_timestamp()
            }
            
        except Exception as e:
            logger.log_error(f"❌ Health check failed for {account}/{platform_name}: {e}")
            
            # 更新错误状态
            if account.upper() in self.platform_metadata and platform_name in self.platform_metadata[account.upper()]:
                self.platform_metadata[account.upper()][platform_name]["status"] = "unhealthy"
                self.platform_metadata[account.upper()][platform_name]["last_error"] = str(e)
            
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": self.state_manager._get_iso_timestamp()
            }

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        检查所有平台实例的健康状态
        
        Returns:
            所有平台的健康检查结果
        """
        results = {}
        for account, platform_map in self.platforms.items():
            results[account] = {}
            for platform_name in platform_map.keys():
                results[account][platform_name] = self.health_check_platform(account, platform_name)
        return results

    def get_platform_capabilities(self, platform_name: str) -> Dict[str, Any]:
        """
        获取平台能力信息
        
        Args:
            platform_name: 平台名称
            
        Returns:
            平台能力信息
        """
        # 先从配置获取
        config = self.get_platform_config(platform_name)
        if config and "capabilities" in config:
            return config["capabilities"]
        
        # 再从实例获取（如果存在）
        for account, platform_map in self.platforms.items():
            if platform_name in platform_map:
                instance = platform_map[platform_name]
                if hasattr(instance, 'capabilities'):
                    return instance.capabilities()
        
        return {}

    def reload_plugins(self):
        """重新加载插件"""
        logger.log_info("🔄 Reloading platform plugins...")
        self.plugin_loader.reload_plugins()
        logger.log_info("✅ Platform plugins reloaded")

    def get_account_summary(self, account: str) -> Dict[str, Any]:
        """
        获取账号的平台摘要信息
        
        Args:
            account: 账号名
            
        Returns:
            账号平台摘要
        """
        account = account.upper()
        platforms_info = {}
        
        if account in self.platforms:
            for platform_name, instance in self.platforms[account].items():
                metadata = self.platform_metadata.get(account, {}).get(platform_name, {})
                platforms_info[platform_name] = {
                    "status": metadata.get("status", "unknown"),
                    "created_at": metadata.get("created_at", ""),
                    "last_health_check": metadata.get("last_health_check", ""),
                    "capabilities": metadata.get("capabilities", {}),
                    "instance_type": type(instance).__name__
                }
        
        return {
            "account": account,
            "platform_count": len(platforms_info),
            "platforms": platforms_info,
            "available_platforms": self.get_available_platforms()
        }

# 全局平台管理器实例
_platform_manager = None

def get_platform_manager() -> PlatformManager:
    """获取全局平台管理器实例"""
    global _platform_manager
    if _platform_manager is None:
        _platform_manager = PlatformManager()
    return _platform_manager

