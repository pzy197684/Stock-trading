
# core/config_loader.py
# 功能：唯一配置源加载、缓存、校验、API密钥加载
import os
import json
from typing import Dict, Optional
from core.logger import logger

class ConfigLoader:
    def __init__(self):
        self._config_path = None
        self._config_cache = None
        self._config_mtime = None

    def get_config_path(self):
        return self._config_path

    def load_config(self, config_path: Optional[str] = None):
        if config_path:
            if not os.path.isfile(config_path):
                msg = f"配置文件不存在: {config_path}"
                logger.log_error(f"❌ {msg}")
                raise FileNotFoundError(msg)
            mtime = os.path.getmtime(config_path)
            if self._config_path != config_path or self._config_mtime != mtime or self._config_cache is None:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._config_cache = json.load(f)
                self._config_path = config_path
                self._config_mtime = mtime
                logger.log_info(f"✅ 成功加载配置文件: {config_path}")
            return self._config_cache
        if not self._config_path:
            msg = "配置未初始化：请在程序入口先调用 load_config(<config.json>)"
            logger.log_error(f"❌ {msg}")
            raise RuntimeError(msg)
        try:
            mtime = os.path.getmtime(self._config_path)
            if self._config_mtime != mtime:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._config_cache = json.load(f)
                self._config_mtime = mtime
                logger.log_info(f"♻️ 重新加载配置文件: {self._config_path}")
        except Exception as e:
            logger.log_error(f"❌ 读取配置失败: {e}")
            raise
        return self._config_cache

    def load_api_keys(self, exchange="binance", account=None):
        def _get_env(k, default=None):
            v = os.environ.get(k)
            return (v or default)
        account = account or _get_env("ACCOUNT", "BN8891")
        base_dir = _get_env("ACCOUNTS_DIR", "accounts")
        
        # 修复路径格式：accounts/PLATFORM/ACCOUNT/platform_api.json
        platform_upper = exchange.upper()
        base_path = os.path.join(base_dir, platform_upper, account)
        key_path = os.path.join(base_path, f"{exchange}_api.json")
        
        # 如果新路径不存在，尝试旧格式
        if not os.path.exists(key_path):
            old_base_path = os.path.join(base_dir, account)
            old_key_path = os.path.join(old_base_path, f"{exchange}_api.json")
            if os.path.exists(old_key_path):
                key_path = old_key_path
                logger.log_info(f"使用旧格式API密钥文件: {key_path}")
            else:
                logger.log_error(f"⚠️ API 密钥文件不存在：{key_path}")
                return None, None
                
        try:
            with open(key_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            api_key = data.get("API_KEY") or data.get("apiKey")
            api_secret = data.get("API_SECRET") or data.get("apiSecret")
            if not api_key or not api_secret:
                logger.log_error(f"⚠️ API 密钥文件字段缺失：{key_path}")
                return None, None
            logger.log_info(f"✅ 成功加载 API 密钥文件: {key_path}")
            return api_key, api_secret
        except Exception as e:
            logger.log_error(f"❌ 加载 API 密钥失败: {e}")
            return None, None

    def load_api_config(self, exchange="binance", account=None):
        """加载完整的API配置，包括testnet设置等"""
        def _get_env(k, default=None):
            v = os.environ.get(k)
            return (v or default)
        account = account or _get_env("ACCOUNT", "BN8891")
        base_dir = _get_env("ACCOUNTS_DIR", "accounts")
        
        # 修正路径结构：accounts/{EXCHANGE}/{account}/{exchange}_api.json
        exchange_upper = exchange.upper()
        base_path = os.path.join(base_dir, exchange_upper, account)
        key_path = os.path.join(base_path, f"{exchange}_api.json")
        
        if not os.path.exists(key_path):
            logger.log_error(f"⚠️ API 配置文件不存在：{key_path}")
            return None
        try:
            with open(key_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            api_key = data.get("API_KEY") or data.get("apiKey")
            api_secret = data.get("API_SECRET") or data.get("apiSecret")
            if not api_key or not api_secret:
                logger.log_error(f"⚠️ API 配置文件密钥字段缺失：{key_path}")
                return None
            logger.log_info(f"✅ 成功加载 API 配置文件: {key_path}")
            return data
        except Exception as e:
            logger.log_error(f"❌ 加载 API 配置失败: {e}")
            return None

# 单例
_loader = ConfigLoader()
get_config_path = _loader.get_config_path
load_config = _loader.load_config
load_api_keys = _loader.load_api_keys
load_api_config = _loader.load_api_config
