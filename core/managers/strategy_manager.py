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
        
        # 添加API需要的属性
        self.strategy_name = getattr(strategy, 'name', 'unknown')
        self.platform = 'unknown'  # 将在create_strategy_instance中设置
        self.status = getattr(strategy, 'status', 'unknown')
        self.total_profit = 0.0
        self.profit_rate = 0.0
        self.positions = []
        self.orders = []
        self.runtime_seconds = 0
        self.last_signal_time = None
        self.parameters = {}
        # 添加运行时数据存储
        self.runtime_data = {}
        
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
            
            # 更新运行时统计
            self.runtime_seconds = int(time.time() - self.created_at)
            if signal:
                self.last_signal_time = self.last_executed_at
            
            # 更新状态
            self.status = getattr(self.strategy, 'status', 'unknown')

            return signal
            
        except Exception as e:
            logger.log_error(f"❌ Strategy execution failed {self.account}/{self.instance_id}: {e}")
            self.strategy.on_error(e, context)
            return None
    
    def get_runtime_seconds(self) -> int:
        """计算实际运行时长（秒）"""
        if self.strategy.status == StrategyStatus.RUNNING and hasattr(self.strategy, '_start_time'):
            return int(time.time() - self.strategy._start_time)
        elif self.strategy.status == StrategyStatus.RUNNING:
            # 如果没有start_time，使用创建时间作为起始时间
            if not hasattr(self.strategy, '_start_time'):
                self.strategy._start_time = time.time()
            return int(time.time() - self.strategy._start_time)
        return 0
    

    
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
            "params": self.strategy.params.copy(),
            "runtime_seconds": self.get_runtime_seconds()
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
    
    def _validate_strategy_params(self, params: Dict[str, Any], strategy_name: str):
        """验证策略参数的完整性"""
        logger.log_info(f"🔍 Validating strategy params for {strategy_name}")
        logger.log_info(f"📋 Parameters received: {params}")
        
        # 针对马丁对冲策略的关键参数验证
        if strategy_name == "martingale_hedge":
            required_params = [
                "symbol",
                "long.first_qty", "long.add_ratio", "long.add_interval", "long.max_add_times",
                "long.tp_first_order", "long.tp_before_full", "long.tp_after_full",
                "short.first_qty", "short.add_ratio", "short.add_interval", "short.max_add_times", 
                "short.tp_first_order", "short.tp_before_full", "short.tp_after_full",
                "hedge.trigger_loss", "hedge.equal_eps", "hedge.min_wait_seconds",
                "risk_control.max_total_qty"
            ]
            
            missing_params = []
            for param_path in required_params:
                value = self._get_nested_value(params, param_path)
                logger.log_info(f"🔍 Checking {param_path}: {value}")
                if value is None:
                    missing_params.append(param_path)
            
            if missing_params:
                logger.log_error(f"❌ Missing required parameters: {missing_params}")
                raise ValueError(f"策略参数不完整，缺少以下必需参数: {', '.join(missing_params)}。请先在账户配置文件中设置完整参数，或通过前端界面配置所有参数。")
            else:
                logger.log_info(f"✅ All required parameters validated successfully")
    
    def _get_nested_value(self, data: Dict[str, Any], path: str):
        """获取嵌套字典中的值"""
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _load_account_specific_config(self, account: str, strategy_name: str) -> Optional[Dict[str, Any]]:
        """加载账户特定的策略配置文件"""
        import os
        import json
        from pathlib import Path
        
        # 确定平台和配置文件路径
        platform_map = {
            'BN': 'BINANCE',
            'CW': 'COINW', 
            'OK': 'OKX',
            'DC': 'DEEP'
        }
        
        platform = None
        for prefix, platform_name in platform_map.items():
            if account.startswith(prefix):
                platform = platform_name
                break
        
        if not platform:
            logger.log_warning(f"Cannot determine platform for account: {account}")
            return None
        
        config_path = f"profiles/{platform}/{account}/strategies/{strategy_name}.json"
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8-sig') as f:
                    config = json.load(f)
                logger.log_info(f"Loaded account-specific config: {config_path}")
                return config
            else:
                logger.log_info(f"No account-specific config found: {config_path}")
                return None
        except Exception as e:
            logger.log_error(f"Failed to load account config {config_path}: {e}")
            return None
    
    def _flatten_strategy_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """将嵌套的策略配置展平为策略参数格式"""
        flattened = {}
        
        if 'trading' in config:
            trading = config['trading']
            # 基本交易参数
            flattened.update({
                'symbol': trading.get('symbol'),
                'order_type': trading.get('order_type'),
                'interval': trading.get('interval'),
                'leverage': trading.get('leverage'),
                'mode': trading.get('mode')
            })
            
            # 多头参数
            if 'long' in trading:
                flattened['long'] = trading['long']
            
            # 空头参数  
            if 'short' in trading:
                flattened['short'] = trading['short']
                
            # 对冲参数
            if 'hedge' in trading:
                flattened['hedge'] = trading['hedge']
        
        # 风险控制参数
        if 'risk_control' in config:
            flattened['risk_control'] = config['risk_control']
        
        # 执行参数
        if 'execution' in config:
            flattened['execution'] = config['execution']
            
        # 监控参数
        if 'monitoring' in config:
            flattened['monitoring'] = config['monitoring']
            
        # 安全参数
        if 'safety' in config:
            flattened['safety'] = config['safety']
        
        return flattened
    
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
        
        # 合并参数 - 加载账户特定配置
        final_params = strategy_config.get("default_params", {}).copy()
        
        # 尝试加载账户特定的配置文件
        account_config = self._load_account_specific_config(account, strategy_name)
        if account_config:
            # 将嵌套的配置结构展平为策略参数格式
            flattened_config = self._flatten_strategy_config(account_config)
            final_params.update(flattened_config)
        
        # 最后应用传入的参数（具有最高优先级）
        if params:
            final_params.update(params)
        
        # 验证关键参数不能为null
        self._validate_strategy_params(final_params, strategy_name)
        
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
            
            # 设置基本属性
            wrapper.strategy_name = strategy_name
            wrapper.parameters = final_params
            
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
            # 记录启动时间
            instance.strategy._start_time = time.time()
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
    
    def force_close_all_positions(self, account: str, instance_id: str) -> Dict[str, Any]:
        """
        紧急平仓并撤单 - 一键清空所有持仓和订单
        
        Returns:
            Dict 包含操作结果详情
        """
        try:
            account = account.upper()
            result = {
                "positions_closed": 0,
                "orders_cancelled": 0,
                "errors": [],
                "success": False
            }
            
            # 获取策略实例
            instance = self.get_strategy_instance(account, instance_id)
            if not instance:
                result["errors"].append(f"策略实例未找到: {account}/{instance_id}")
                return result
            
            logger.log_warning(f"🚨 开始紧急平仓: {account}/{instance_id}")
            
            # 真实环境：调用交易所API进行平仓
            # TODO: 实现真实环境的平仓逻辑
            logger.log_warning(f"⚠️ 真实环境平仓功能需要实现交易所API调用: {account}")
            result["errors"].append("真实环境平仓功能待实现")
            
            # 设置成功状态
            if len(result["errors"]) == 0:
                result["success"] = True
                logger.log_info(f"🎯 紧急平仓成功: {account}/{instance_id}")
            else:
                logger.log_error(f"❌ 紧急平仓部分失败: {result['errors']}")
            
            return result
            
        except Exception as e:
            logger.log_error(f"❌ 紧急平仓异常: {account}/{instance_id} - {e}")
            return {
                "positions_closed": 0,
                "orders_cancelled": 0,
                "errors": [str(e)],
                "success": False
            }
                
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