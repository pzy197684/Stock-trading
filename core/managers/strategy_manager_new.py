# core/managers/strategy_manager.py
# 功能：重构后的策略管理器，支持插件化、多账号隔离
from typing import Dict, List, Any, Optional
import time
from core.strategy.base import StrategyBase, StrategyStatus, StrategyContext, TradingSignal
from core.utils.plugin_loader import get_plugin_loader
from core.state_store import get_state_manager
from core.logger import logger

class StrategyInstance:
    """策略实例包装器"""
    
    def __init__(self, strategy: StrategyBase, account: str, instance_id: str):
        self.strategy = strategy
        self.account = account
        self.instance_id = instance_id
        self.created_at = time.time()
        self.last_executed_at = None
        self.execution_interval = 1.0  # 执行间隔（秒）
        
    def should_execute(self) -> bool:
        """判断是否应该执行策略"""
        if self.strategy.status != StrategyStatus.RUNNING:
            return False
        
        if self.last_executed_at is None:
            return True
        
        return time.time() - self.last_executed_at >= self.execution_interval
    
    def execute(self, context: StrategyContext) -> Optional[TradingSignal]:
        """执行策略"""
        try:
            if not self.should_execute():
                return None
            
            signal = self.strategy.generate_signal(context)
            self.last_executed_at = time.time()
            self.strategy.execution_count += 1
            self.strategy.last_execution_time = self.last_executed_at
            self.strategy.last_signal = signal
            
            return signal
            
        except Exception as e:
            logger.log_error(f"❌ Strategy execution failed {self.account}/{self.instance_id}: {e}")
            self.strategy.on_error(e, context)
            return None
    
    def get_info(self) -> Dict[str, Any]:
        """获取策略实例信息"""
        return {
            "instance_id": self.instance_id,
            "account": self.account,
            "strategy_name": self.strategy.name,
            "status": self.strategy.status.value,
            "created_at": self.created_at,
            "last_executed_at": self.last_executed_at,
            "execution_interval": self.execution_interval,
            "execution_count": self.strategy.execution_count,
            "error_count": self.strategy.error_count,
            "last_error": self.strategy.last_error,
            "params": self.strategy.params.copy()
        }

class StrategyManager:
    """
    策略管理器
    
    功能：
    1. 插件化策略加载
    2. 多账号策略实例管理
    3. 策略生命周期管理
    4. 策略执行调度
    5. 策略配置管理
    """
    
    def __init__(self):
        self.plugin_loader = get_plugin_loader()
        self.state_manager = get_state_manager()
        
        # 策略实例存储：{ account: { instance_id: StrategyInstance } }
        self.strategy_instances: Dict[str, Dict[str, StrategyInstance]] = {}
        
        # 实例计数器
        self._instance_counter = 0
        
        # 加载策略插件
        self._load_strategy_plugins()
    
    def _load_strategy_plugins(self):
        """加载策略插件"""
        try:
            plugins = self.plugin_loader.scan_strategy_plugins()
            logger.log_info(f"📋 Loaded {len(plugins)} strategy plugins: {list(plugins.keys())}")
        except Exception as e:
            logger.log_error(f"❌ Failed to load strategy plugins: {e}")
    
    def _ensure_account_slot(self, account: str):
        """确保账号槽位存在"""
        account = account.upper()
        if account not in self.strategy_instances:
            self.strategy_instances[account] = {}
    
    def _generate_instance_id(self, strategy_name: str) -> str:
        """生成策略实例ID"""
        self._instance_counter += 1
        return f"{strategy_name}_{self._instance_counter}_{int(time.time())}"
    
    def get_available_strategies(self) -> List[str]:
        """获取所有可用策略列表"""
        return self.plugin_loader.list_available_strategies()
    
    def get_strategy_config(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取策略配置"""
        return self.plugin_loader.get_strategy_config(strategy_name)
    
    def create_strategy_instance(self, account: str, strategy_name: str, 
                               params: Optional[Dict[str, Any]] = None,
                               instance_config: Optional[Dict[str, Any]] = None) -> str:
        """
        创建策略实例
        
        Args:
            account: 账号名
            strategy_name: 策略名称
            params: 策略参数
            instance_config: 实例配置（执行间隔等）
            
        Returns:
            策略实例ID
            
        Raises:
            ValueError: 策略不存在或参数错误
        """
        account = account.upper()
        
        # 获取策略类
        strategy_class = self.plugin_loader.get_strategy_class(strategy_name)
        if not strategy_class:
            raise ValueError(f"Strategy not found or failed to load: {strategy_name}")
        
        # 获取策略配置
        strategy_config = self.get_strategy_config(strategy_name)
        if not strategy_config:
            raise ValueError(f"Strategy config not found: {strategy_name}")
        
        # 合并参数
        final_params = strategy_config.get("default_params", {}).copy()
        if params:
            final_params.update(params)
        
        # 构建完整配置
        config = {
            "name": strategy_config.get("display_name", strategy_name),
            "params": final_params,
            "metadata": {
                "account": account,
                "strategy_name": strategy_name,
                "created_at": self.state_manager._get_iso_timestamp(),
                "plugin_config": strategy_config
            }
        }
        
        try:
            # 创建策略实例
            strategy = strategy_class(config)
            
            # 生成实例ID
            instance_id = self._generate_instance_id(strategy_name)
            
            # 创建包装器
            wrapper = StrategyInstance(strategy, account, instance_id)
            
            # 应用实例配置
            if instance_config:
                if "execution_interval" in instance_config:
                    wrapper.execution_interval = instance_config["execution_interval"]
            
            # 存储实例
            self._ensure_account_slot(account)
            self.strategy_instances[account][instance_id] = wrapper
            
            # 更新账号状态
            try:
                state = self.state_manager.load_state(account)
                state.metadata["strategy"] = strategy_name
                state.metadata["strategy_instance"] = instance_id
                self.state_manager.save_state(account, state)
            except Exception as e:
                logger.log_warning(f"Failed to update state for account {account}: {e}")
            
            logger.log_info(f"✅ Created strategy instance: {account}/{instance_id} ({strategy_name})")
            return instance_id
            
        except Exception as e:
            logger.log_error(f"❌ Failed to create strategy instance {account}/{strategy_name}: {e}")
            raise
    
    def get_strategy_instance(self, account: str, instance_id: str) -> Optional[StrategyInstance]:
        """获取策略实例"""
        account = account.upper()
        return self.strategy_instances.get(account, {}).get(instance_id)
    
    def list_strategy_instances(self, account: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        列出策略实例
        
        Args:
            account: 账号名（可选）
            
        Returns:
            策略实例信息字典
        """
        if account:
            account = account.upper()
            instances = self.strategy_instances.get(account, {})
            return {
                account: [instance.get_info() for instance in instances.values()]
            }
        
        # 返回所有账号的策略实例
        result = {}
        for acct, instances in self.strategy_instances.items():
            result[acct] = [instance.get_info() for instance in instances.values()]
        return result
    
    def start_strategy(self, account: str, instance_id: str) -> bool:
        """启动策略"""
        instance = self.get_strategy_instance(account, instance_id)
        if not instance:
            logger.log_error(f"❌ Strategy instance not found: {account}/{instance_id}")
            return False
        
        try:
            instance.strategy.start()
            logger.log_info(f"▶️  Started strategy: {account}/{instance_id}")
            return True
        except Exception as e:
            logger.log_error(f"❌ Failed to start strategy {account}/{instance_id}: {e}")
            return False
    
    def pause_strategy(self, account: str, instance_id: str) -> bool:
        """暂停策略"""
        instance = self.get_strategy_instance(account, instance_id)
        if not instance:
            logger.log_error(f"❌ Strategy instance not found: {account}/{instance_id}")
            return False
        
        try:
            instance.strategy.pause()
            logger.log_info(f"⏸️  Paused strategy: {account}/{instance_id}")
            return True
        except Exception as e:
            logger.log_error(f"❌ Failed to pause strategy {account}/{instance_id}: {e}")
            return False
    
    def stop_strategy(self, account: str, instance_id: str) -> bool:
        """停止策略"""
        instance = self.get_strategy_instance(account, instance_id)
        if not instance:
            logger.log_error(f"❌ Strategy instance not found: {account}/{instance_id}")
            return False
        
        try:
            instance.strategy.stop()
            logger.log_info(f"⏹️  Stopped strategy: {account}/{instance_id}")
            return True
        except Exception as e:
            logger.log_error(f"❌ Failed to stop strategy {account}/{instance_id}: {e}")
            return False
    
    def remove_strategy_instance(self, account: str, instance_id: str) -> bool:
        """移除策略实例"""
        try:
            account = account.upper()
            if account in self.strategy_instances and instance_id in self.strategy_instances[account]:
                # 先停止策略
                instance = self.strategy_instances[account][instance_id]
                instance.strategy.stop()
                
                # 清理资源
                context = self._create_dummy_context(account)
                instance.strategy.cleanup(context)
                
                # 移除实例
                del self.strategy_instances[account][instance_id]
                
                logger.log_info(f"🗑️  Removed strategy instance: {account}/{instance_id}")
                return True
            else:
                logger.log_warning(f"⚠️  Strategy instance not found: {account}/{instance_id}")
                return False
                
        except Exception as e:
            logger.log_error(f"❌ Failed to remove strategy instance {account}/{instance_id}: {e}")
            return False
    
    def execute_strategies(self, account: str, context: StrategyContext) -> List[TradingSignal]:
        """
        执行指定账号下的所有运行中策略
        
        Args:
            account: 账号名
            context: 策略上下文
            
        Returns:
            交易信号列表
        """
        account = account.upper()
        signals = []
        
        instances = self.strategy_instances.get(account, {})
        for instance_id, instance in instances.items():
            if instance.strategy.status == StrategyStatus.RUNNING:
                signal = instance.execute(context)
                if signal and signal.signal_type.value != "none":
                    signals.append(signal)
        
        return signals
    
    def get_active_strategies(self, account: Optional[str] = None) -> List[StrategyInstance]:
        """
        获取活跃策略实例
        
        Args:
            account: 账号名（可选）
            
        Returns:
            活跃策略实例列表
        """
        active_strategies = []
        
        if account:
            account = account.upper()
            instances = self.strategy_instances.get(account, {})
            for instance in instances.values():
                if instance.strategy.status == StrategyStatus.RUNNING:
                    active_strategies.append(instance)
        else:
            for instances in self.strategy_instances.values():
                for instance in instances.values():
                    if instance.strategy.status == StrategyStatus.RUNNING:
                        active_strategies.append(instance)
        
        return active_strategies
    
    def update_strategy_params(self, account: str, instance_id: str, 
                             params: Dict[str, Any]) -> bool:
        """更新策略参数"""
        instance = self.get_strategy_instance(account, instance_id)
        if not instance:
            logger.log_error(f"❌ Strategy instance not found: {account}/{instance_id}")
            return False
        
        try:
            # 验证参数
            errors = instance.strategy.validate_params(params)
            if errors:
                logger.log_error(f"❌ Parameter validation failed: {errors}")
                return False
            
            # 更新参数
            instance.strategy.params.update(params)
            logger.log_info(f"✅ Updated strategy params: {account}/{instance_id}")
            return True
            
        except Exception as e:
            logger.log_error(f"❌ Failed to update strategy params {account}/{instance_id}: {e}")
            return False
    
    def get_strategy_status_summary(self) -> Dict[str, Any]:
        """获取策略状态摘要"""
        summary = {
            "total_instances": 0,
            "running": 0,
            "paused": 0,
            "stopped": 0,
            "error": 0,
            "by_account": {}
        }
        
        for account, instances in self.strategy_instances.items():
            account_summary = {
                "total": len(instances),
                "running": 0,
                "paused": 0,
                "stopped": 0,
                "error": 0,
                "strategies": []
            }
            
            for instance_id, instance in instances.items():
                status = instance.strategy.status
                account_summary["strategies"].append({
                    "instance_id": instance_id,
                    "name": instance.strategy.name,
                    "status": status.value
                })
                
                if status == StrategyStatus.RUNNING:
                    account_summary["running"] += 1
                    summary["running"] += 1
                elif status == StrategyStatus.PAUSED:
                    account_summary["paused"] += 1
                    summary["paused"] += 1
                elif status == StrategyStatus.STOPPED:
                    account_summary["stopped"] += 1
                    summary["stopped"] += 1
                elif status == StrategyStatus.ERROR:
                    account_summary["error"] += 1
                    summary["error"] += 1
                
                summary["total_instances"] += 1
            
            summary["by_account"][account] = account_summary
        
        return summary
    
    def reload_plugins(self):
        """重新加载策略插件"""
        logger.log_info("🔄 Reloading strategy plugins...")
        self.plugin_loader.reload_plugins()
        logger.log_info("✅ Strategy plugins reloaded")
    
    def _create_dummy_context(self, account: str) -> StrategyContext:
        """创建虚拟上下文（用于清理等操作）"""
        return StrategyContext(
            account=account,
            platform="",
            symbol="",
            current_price=0.0,
            position_long={},
            position_short={},
            balance={}
        )

# 全局策略管理器实例
_strategy_manager = None

def get_strategy_manager() -> StrategyManager:
    """获取全局策略管理器实例"""
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
    return _strategy_manager