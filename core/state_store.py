# core/state_store.py
# 功能：重构后的状态管理器，支持多账号隔离、JSON序列化、UI友好格式
import os
import json
import time
from datetime import datetime, timezone
from tempfile import NamedTemporaryFile
from typing import Optional, Dict, Any, List
from pathlib import Path
from core.logger import logger
from core.domain.models import AccountState, PositionState, Metrics

class StateManager:
    """
    状态管理器
    
    功能：
    1. 多账号状态隔离
    2. JSON格式存储，UI友好
    3. 原子化更新操作
    4. 状态快照功能
    5. 状态历史记录
    6. 数据验证和迁移
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else self._get_default_base_path()
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 状态缓存
        self._state_cache: Dict[str, AccountState] = {}
        
        # 文件修改时间缓存（用于检测外部修改）
        self._file_mtimes: Dict[str, float] = {}
        
    def _get_default_base_path(self) -> Path:
        """获取默认状态存储路径"""
        # 优先使用环境变量
        env_path = os.environ.get("STATE_DIR")
        if env_path:
            return Path(env_path)
        
        # 自动检测项目根目录
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent  # 从 core/state_store.py 向上两级
        return project_root / "state"
    
    def get_account_path(self, account: str) -> Path:
        """获取账号状态目录路径"""
        account = account.upper()
        account_path = self.base_path / account
        account_path.mkdir(parents=True, exist_ok=True)
        return account_path
    
    def get_state_file_path(self, account: str) -> Path:
        """获取账号状态文件路径"""
        return self.get_account_path(account) / "state.json"
    
    def get_history_path(self, account: str) -> Path:
        """获取账号历史记录目录"""
        history_path = self.get_account_path(account) / "history"
        history_path.mkdir(parents=True, exist_ok=True)
        return history_path
    
    def create_default_state(self) -> AccountState:
        """创建默认状态"""
        return AccountState(
            long=PositionState(),
            short=PositionState(),
            metrics=Metrics(),
            pause_until=None,
            schema_hydrated={},
            backfill_done={},
            # 新增UI友好字段
            metadata={
                "created_at": self._get_iso_timestamp(),
                "updated_at": self._get_iso_timestamp(),
                "version": "2.0.0",
                "account": "",
                "platform": "",
                "strategy": "",
                "status": "initialized"
            }
        )
    
    def load_state(self, account: str, use_cache: bool = True) -> AccountState:
        """
        加载账号状态
        
        Args:
            account: 账号名
            use_cache: 是否使用缓存
            
        Returns:
            账号状态对象
        """
        account = account.upper()
        
        # 检查缓存
        if use_cache and account in self._state_cache:
            # 检查文件是否被外部修改
            if not self._is_file_modified(account):
                return self._state_cache[account]
        
        state_file = self.get_state_file_path(account)
        
        if not state_file.exists():
            logger.log_info(f"📁 Creating new state file for account: {account}")
            state = self.create_default_state()
            state.metadata["account"] = account
            self.save_state(account, state)
            return state
        
        try:
            with open(state_file, 'r', encoding='utf-8-sig') as f:
                state_dict = json.load(f)
            
            # 记录文件修改时间
            self._file_mtimes[account] = state_file.stat().st_mtime
            
            # 数据迁移和验证
            state_dict = self._migrate_and_validate(state_dict, account)
            
            # 反序列化为AccountState对象
            state = self._dict_to_account_state(state_dict)
            
            # 缓存状态
            if use_cache:
                self._state_cache[account] = state
            
            logger.log_info(f"✅ Loaded state for account: {account}")
            return state
            
        except Exception as e:
            logger.log_error(f"❌ Failed to load state for account {account}: {e}")
            # 备份损坏的文件
            self._backup_corrupted_file(account)
            # 返回默认状态
            state = self.create_default_state()
            state.metadata["account"] = account
            return state
    
    def save_state(self, account: str, state: AccountState, create_snapshot: bool = False) -> bool:
        """
        保存账号状态
        
        Args:
            account: 账号名
            state: 状态对象
            create_snapshot: 是否创建快照
            
        Returns:
            保存是否成功
        """
        account = account.upper()
        state_file = self.get_state_file_path(account)
        
        try:
            # 更新metadata
            state.metadata["updated_at"] = self._get_iso_timestamp()
            state.metadata["account"] = account
            
            # 转换为字典格式
            state_dict = self._account_state_to_dict(state)
            
            # 原子写入
            temp_file = state_file.parent / f".{state_file.name}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, ensure_ascii=False, indent=2, default=self._json_serializer)
            
            # 原子替换
            temp_file.replace(state_file)
            
            # 更新缓存
            self._state_cache[account] = state
            self._file_mtimes[account] = state_file.stat().st_mtime
            
            # 创建快照（可选）
            if create_snapshot:
                self._create_snapshot(account, state_dict)
            
            logger.log_info(f"💾 Saved state for account: {account}")
            return True
            
        except Exception as e:
            logger.log_error(f"❌ Failed to save state for account {account}: {e}")
            return False
    
    def update_state_bulk(self, account: str, updates: Dict[str, Any], 
                         create_snapshot: bool = False) -> bool:
        """
        批量更新状态字段
        
        Args:
            account: 账号名
            updates: 更新字段字典，支持嵌套路径如 "long.qty"
            create_snapshot: 是否创建快照
            
        Returns:
            更新是否成功
        """
        try:
            state = self.load_state(account)
            
            # 应用更新
            for key_path, value in updates.items():
                self._update_nested_field(state, key_path, value)
            
            # 更新时间戳
            state.metadata["updated_at"] = self._get_iso_timestamp()
            
            # 保存状态
            return self.save_state(account, state, create_snapshot)
            
        except Exception as e:
            logger.log_error(f"❌ Failed to bulk update state for account {account}: {e}")
            return False
    
    def get_state_summary(self, account: str) -> Dict[str, Any]:
        """
        获取状态摘要（UI友好格式）
        
        Args:
            account: 账号名
            
        Returns:
            状态摘要字典
        """
        try:
            state = self.load_state(account)
            
            return {
                "account": account,
                "status": state.metadata.get("status", "unknown"),
                "platform": state.metadata.get("platform", ""),
                "strategy": state.metadata.get("strategy", ""),
                "updated_at": state.metadata.get("updated_at", ""),
                "positions": {
                    "long": {
                        "qty": state.long.qty,
                        "avg_price": state.long.avg_price,
                        "unrealized_pnl": 0.0,  # 可由外部计算填入
                        "add_times": state.long.add_times,
                        "hedge_locked": state.long.hedge_locked,
                        "hedge_stop": state.long.hedge_stop
                    },
                    "short": {
                        "qty": state.short.qty,
                        "avg_price": state.short.avg_price,
                        "unrealized_pnl": 0.0,  # 可由外部计算填入
                        "add_times": state.short.add_times,
                        "hedge_locked": state.short.hedge_locked,
                        "hedge_stop": state.short.hedge_stop
                    }
                },
                "metrics": {
                    "nv_prev": state.metrics.nv_prev,
                    "last_snapshot_date": state.metrics.last_snapshot_date
                },
                "pause_until": state.pause_until,
                "file_path": str(self.get_state_file_path(account))
            }
            
        except Exception as e:
            logger.log_error(f"❌ Failed to get state summary for account {account}: {e}")
            return {
                "account": account,
                "status": "error",
                "error": str(e)
            }
    
    def list_accounts(self) -> List[str]:
        """列出所有账号"""
        accounts = []
        try:
            for account_dir in self.base_path.iterdir():
                if account_dir.is_dir() and (account_dir / "state.json").exists():
                    accounts.append(account_dir.name)
            return sorted(accounts)
        except Exception as e:
            logger.log_error(f"❌ Failed to list accounts: {e}")
            return []
    
    def get_all_accounts_summary(self) -> List[Dict[str, Any]]:
        """获取所有账号的状态摘要"""
        summaries = []
        for account in self.list_accounts():
            summaries.append(self.get_state_summary(account))
        return summaries
    
    def delete_account_state(self, account: str, create_backup: bool = True) -> bool:
        """
        删除账号状态
        
        Args:
            account: 账号名
            create_backup: 是否创建备份
            
        Returns:
            删除是否成功
        """
        try:
            account = account.upper()
            account_path = self.get_account_path(account)
            
            if not account_path.exists():
                logger.log_warning(f"⚠️  Account state not found: {account}")
                return True
            
            # 创建备份
            if create_backup:
                backup_name = f"deleted_{account}_{int(time.time())}"
                backup_path = self.base_path / "backups" / backup_name
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                # 移动整个账号目录到备份位置
                account_path.rename(backup_path)
                logger.log_info(f"📦 Backed up account {account} to {backup_path}")
            else:
                # 直接删除
                import shutil
                shutil.rmtree(account_path)
            
            # 清理缓存
            self._state_cache.pop(account, None)
            self._file_mtimes.pop(account, None)
            
            logger.log_info(f"🗑️  Deleted state for account: {account}")
            return True
            
        except Exception as e:
            logger.log_error(f"❌ Failed to delete state for account {account}: {e}")
            return False
    
    # 私有辅助方法
    def _get_iso_timestamp(self) -> str:
        """获取ISO格式的时间戳"""
        return datetime.now(timezone.utc).isoformat()
    
    def _is_file_modified(self, account: str) -> bool:
        """检查文件是否被外部修改"""
        try:
            state_file = self.get_state_file_path(account)
            if not state_file.exists():
                return True
            
            current_mtime = state_file.stat().st_mtime
            cached_mtime = self._file_mtimes.get(account, 0)
            return current_mtime > cached_mtime
        except Exception:
            return True
    
    def _migrate_and_validate(self, state_dict: Dict[str, Any], account: str) -> Dict[str, Any]:
        """数据迁移和验证"""
        # 1. 迁移旧版字段
        migrated = False
        for side in ("long", "short"):
            if side not in state_dict or not isinstance(state_dict[side], dict):
                state_dict[side] = {}
            
            # 确保新字段存在
            state_dict[side].setdefault("hedge_locked", False)
            state_dict[side].setdefault("hedge_stop", False)
            state_dict[side].setdefault("locked_profit", 0)
        
        # 处理顶层旧字段
        if "hedge_locked" in state_dict:
            for side in ("long", "short"):
                if not state_dict[side].get("hedge_locked"):
                    state_dict[side]["hedge_locked"] = state_dict["hedge_locked"]
            state_dict.pop("hedge_locked")
            migrated = True
        
        if "locked_profit" in state_dict:
            for side in ("long", "short"):
                if not state_dict[side].get("locked_profit"):
                    state_dict[side]["locked_profit"] = state_dict["locked_profit"]
            state_dict.pop("locked_profit")
            migrated = True
        
        # 2. 字段补全
        for side in ("long", "short"):
            d = state_dict[side]
            d.setdefault("qty", 0)
            d.setdefault("avg_price", 0)
            d.setdefault("add_times", 0)
            d.setdefault("round", 0)
            d.setdefault("last_qty", 0)
            d.setdefault("opposite_qty", 0)
            d.setdefault("last_entry_price", d.get("avg_price", 0) or 0)
            d.setdefault("last_fill_price", d.get("avg_price", 0) or 0)
            d.setdefault("last_fill_ts", 0)
            d.setdefault("last_open_ts", 0)
            d.setdefault("fast_add_paused_until", 0)
            d.setdefault("cooldown_until", 0)
            d.setdefault("last_add_time", None)
        
        # 3. 顶级字段补全
        state_dict.setdefault("schema_hydrated", {})
        state_dict.setdefault("backfill_done", {})
        state_dict.setdefault("pause_until", None)
        
        # 4. metrics补全
        m = state_dict.setdefault("metrics", {})
        m.setdefault("nv_prev", 0.0)
        m.setdefault("last_snapshot_date", "")
        
        # 5. metadata补全
        meta = state_dict.setdefault("metadata", {})
        current_time = self._get_iso_timestamp()
        meta.setdefault("created_at", current_time)
        meta.setdefault("updated_at", current_time)
        meta.setdefault("version", "2.0.0")
        meta.setdefault("account", account)
        meta.setdefault("platform", "")
        meta.setdefault("strategy", "")
        meta.setdefault("status", "initialized")
        
        if migrated:
            logger.log_info(f"✅ Migrated legacy fields for account: {account}")
        
        return state_dict
    
    def _dict_to_account_state(self, state_dict: Dict[str, Any]) -> AccountState:
        """将字典转换为AccountState对象"""
        return AccountState(
            long=PositionState(**state_dict["long"]),
            short=PositionState(**state_dict["short"]),
            metrics=Metrics(**state_dict["metrics"]),
            pause_until=state_dict.get("pause_until"),
            schema_hydrated=state_dict.get("schema_hydrated", {}),
            backfill_done=state_dict.get("backfill_done", {}),
            metadata=state_dict.get("metadata", {})
        )
    
    def _account_state_to_dict(self, state: AccountState) -> Dict[str, Any]:
        """将AccountState对象转换为字典"""
        return {
            "long": self._position_state_to_dict(state.long),
            "short": self._position_state_to_dict(state.short),
            "metrics": {
                "nv_prev": state.metrics.nv_prev,
                "last_snapshot_date": state.metrics.last_snapshot_date
            },
            "pause_until": state.pause_until,
            "schema_hydrated": state.schema_hydrated,
            "backfill_done": state.backfill_done,
            "metadata": state.metadata
        }
    
    def _position_state_to_dict(self, pos: PositionState) -> Dict[str, Any]:
        """将PositionState对象转换为字典"""
        return {
            "qty": pos.qty,
            "avg_price": pos.avg_price,
            "add_times": pos.add_times,
            "last_add_time": pos.last_add_time,
            "hedge_locked": pos.hedge_locked,
            "hedge_stop": pos.hedge_stop,
            "locked_profit": pos.locked_profit,
            "round": pos.round,
            "last_qty": pos.last_qty,
            "opposite_qty": pos.opposite_qty,
            "last_entry_price": pos.last_entry_price,
            "last_fill_price": pos.last_fill_price,
            "last_fill_ts": pos.last_fill_ts,
            "last_open_ts": pos.last_open_ts,
            "fast_add_paused_until": pos.fast_add_paused_until,
            "cooldown_until": pos.cooldown_until
        }
    
    def _json_serializer(self, obj) -> Any:
        """自定义JSON序列化器"""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)
    
    def _update_nested_field(self, state: AccountState, key_path: str, value: Any):
        """更新嵌套字段"""
        keys = key_path.split('.')
        current = state
        
        # 导航到目标对象
        for key in keys[:-1]:
            if hasattr(current, key):
                current = getattr(current, key)
            elif isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise ValueError(f"Invalid key path: {key_path}")
        
        # 设置最终值
        final_key = keys[-1]
        if hasattr(current, final_key):
            setattr(current, final_key, value)
        elif isinstance(current, dict):
            current[final_key] = value
        else:
            raise ValueError(f"Cannot set field: {key_path}")
    
    def _create_snapshot(self, account: str, state_dict: Dict[str, Any]):
        """创建状态快照"""
        try:
            history_path = self.get_history_path(account)
            timestamp = int(time.time())
            snapshot_file = history_path / f"snapshot_{timestamp}.json"
            
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, ensure_ascii=False, indent=2, default=self._json_serializer)
            
            logger.log_info(f"📸 Created snapshot for account {account}: {snapshot_file.name}")
            
            # 清理旧快照（保留最近10个）
            self._cleanup_old_snapshots(account, keep_count=10)
            
        except Exception as e:
            logger.log_error(f"❌ Failed to create snapshot for account {account}: {e}")
    
    def _cleanup_old_snapshots(self, account: str, keep_count: int = 10):
        """清理旧快照"""
        try:
            history_path = self.get_history_path(account)
            snapshots = list(history_path.glob("snapshot_*.json"))
            
            if len(snapshots) > keep_count:
                # 按时间戳排序，删除最旧的
                snapshots.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                for old_snapshot in snapshots[keep_count:]:
                    old_snapshot.unlink()
                    logger.log_info(f"🗑️  Cleaned up old snapshot: {old_snapshot.name}")
                    
        except Exception as e:
            logger.log_error(f"❌ Failed to cleanup old snapshots for account {account}: {e}")
    
    def _backup_corrupted_file(self, account: str):
        """备份损坏的状态文件"""
        try:
            state_file = self.get_state_file_path(account)
            if state_file.exists():
                backup_dir = self.base_path / "corrupted_backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = int(time.time())
                backup_file = backup_dir / f"{account}_corrupted_{timestamp}.json"
                
                state_file.rename(backup_file)
                logger.log_warning(f"⚠️  Backed up corrupted file: {backup_file}")
                
        except Exception as e:
            logger.log_error(f"❌ Failed to backup corrupted file for account {account}: {e}")


# 向后兼容的函数接口
def load_state(account: Optional[str] = None) -> AccountState:
    """向后兼容：加载状态"""
    account = account or os.environ.get("ACCOUNT", "BN1602")
    manager = StateManager()
    return manager.load_state(account)

def save_state(account: Optional[str], state: AccountState):
    """向后兼容：保存状态"""
    if account is None:
        account = os.environ.get("ACCOUNT", "BN1602")
    manager = StateManager()
    manager.save_state(account, state)

def get_state_path(account: Optional[str] = None) -> str:
    """向后兼容：获取状态文件路径"""
    account = account or os.environ.get("ACCOUNT", "BN1602")
    manager = StateManager()
    return str(manager.get_state_file_path(account))

# 全局状态管理器实例
_state_manager = None

def get_state_manager() -> StateManager:
    """获取全局状态管理器实例"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
