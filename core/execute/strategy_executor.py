"""
Minimal strategy executor
- 加载策略管理器和平台管理器
- 根据配置/环境创建平台实例（若提供 API keys）
- 循环执行策略.decide() -> build_order() -> place_order()

这是一个最小可用版本，便于本地快速 smoke-run 与后续逐步移植旧版 executor 的复杂逻辑。
"""
import time
import os
from core.logger import logger
from core.managers.strategy_manager import StrategyManager
from core.managers.platform_manager import PlatformManager
from core.platform.base import ExchangeIf
from core.domain.enums import Platform, ConfigKey, DefaultValue
from typing import cast
from core.config_loader import load_config, load_api_keys
from core.services.order_service import build_order, place_order
from core.managers.state_manager import StateManager


def create_platforms(pm: PlatformManager, cfg: dict):
    # 优先使用 ConfigLoader 的 load_api_keys (accounts dir / env)
    accounts = cfg.get(ConfigKey.ACCOUNTS) if isinstance(cfg, dict) else None
    # 简单逻辑：若配置里明确给出 accounts mapping，则根据 mapping 创建实例
    for name in (Platform.BINANCE, Platform.COINW, Platform.OKX):
        api_key, api_secret = None, None
        # 1) 从 cfg.accounts.<name> 获取
        try:
            if accounts and isinstance(accounts, dict):
                a = accounts.get(name) or {}
                api_key = a.get(ConfigKey.API_KEY) or a.get("API_KEY")
                api_secret = a.get(ConfigKey.API_SECRET) or a.get("API_SECRET")
        except Exception:
            pass
        # 2) 否则尝试通过 ConfigLoader.load_api_keys(account=..)
        if not api_key or not api_secret:
            try:
                # load_api_keys 带 exchange 参数
                ak, sk = load_api_keys(exchange=name)
                if ak and sk:
                    api_key, api_secret = ak, sk
            except Exception:
                pass
        if api_key and api_secret:
            try:
                # 使用默认账号创建平台实例
                default_account = "DEFAULT"
                pm.create_platform_for_account(default_account, name, api_key, api_secret)
                logger.log_info(f"created platform instance: {name} for account {default_account}")
            except Exception as e:
                logger.log_warning(f"create_platform_for_account {name} failed: {e}")


def run_loop(poll_interval: float = 1.0):
    # load config if given
    cfg = {}
    try:
        cfg = load_config() or {}
    except Exception:
        cfg = {}

    # init managers
    strategies_cfg = cfg.get(ConfigKey.STRATEGIES) or [{
        ConfigKey.STRATEGY_NAME: DefaultValue.STRATEGY_NAME, 
        ConfigKey.NAME: DefaultValue.STRATEGY_DISPLAY_NAME, 
        ConfigKey.PARAMS: {}
    }]
    sm = StrategyManager(strategies_cfg)
    pm = PlatformManager()
    create_platforms(pm, cfg)

    state_mgr = StateManager()

    logger.log_info("executor: 启动完成，进行单次 smoke-run 迭代")
    # For smoke-run we do a single iteration to validate strategy->order path without real infinite loop
    for strat in sm.get_active_strategies():
        try:
            plan = strat.decide()
            if not plan:
                logger.log_info(f"strategy {strat.name} returned no plan")
                continue
            order_req = build_order(strat, plan)
            platform_name = plan.get(ConfigKey.PLATFORM) or cfg.get(ConfigKey.DEFAULT_PLATFORM) or DefaultValue.PLATFORM
            try:
                # 使用默认账号获取平台实例
                default_account = "DEFAULT"
                platform = pm.get_platform(platform_name, default_account)
            except Exception as e:
                logger.log_error(f"无法获取平台实例 {platform_name}: {e}")
                raise e  # 实盘环境必须有正确的平台配置

            resp = place_order(cast(ExchangeIf, platform), order_req)
            logger.log_info(f"order response: {resp}")
        except Exception as e:
            logger.log_error(f"strategy loop exception: {e}")


if __name__ == '__main__':
    run_loop(poll_interval=float(os.environ.get("EXECUTOR_POLL_SEC", "1")))
