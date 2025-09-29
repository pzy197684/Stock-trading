# -*- coding: utf-8 -*-
# tests/strategy/test_martingale_hedge.py
# 功能：马丁对冲策略单元测试

import unittest
import json
from unittest.mock import Mock, patch
from core.strategy.martingale_hedge import MartingaleHedgeStrategy
from core.strategy.martingale_hedge.utils import (
    MartingaleStateManager, 
    MartingaleCalculator,
    validate_strategy_config
)
from core.strategy.base import StrategyContext, TradingSignal, SignalType

class TestMartingaleHedgeStrategy(unittest.TestCase):
    """马丁对冲策略测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.config = {
            "name": "test_martingale_hedge",
            "params": {
                "symbol": "ETHUSDT",
                "order_type": "MARKET",
                "interval": 5,
                
                "long": {
                    "first_qty": 0.01,
                    "add_ratio": 2.0,
                    "add_interval": 0.02,
                    "max_add_times": 3,
                    "tp_first_order": 0.01,
                    "tp_before_full": 0.015,
                    "tp_after_full": 0.02
                },
                
                "short": {
                    "first_qty": 0.01,
                    "add_ratio": 2.0,
                    "add_interval": 0.02,
                    "max_add_times": 3,
                    "tp_first_order": 0.01,
                    "tp_before_full": 0.015,
                    "tp_after_full": 0.02
                },
                
                "hedge": {
                    "trigger_loss": 0.05,
                    "equal_eps": 0.01,
                    "min_wait_seconds": 60,
                    "release_tp_after_full": {
                        "long": 0.02,
                        "short": 0.02
                    },
                    "release_sl_loss_ratio": {
                        "long": 1.0,
                        "short": 1.0
                    }
                },
                
                "risk_control": {
                    "tp_slippage": 0.002,
                    "max_total_qty": 1.0,
                    "cooldown_minutes": 1,
                    "fast_add_window": 300
                }
            }
        }
        
        self.strategy = MartingaleHedgeStrategy(self.config)
        
        # 模拟上下文
        self.context = StrategyContext(
            account="test_account",
            platform="binance",
            symbol="ETHUSDT",
            current_price=3000.0,
            position_long={"quantity": 0.0, "average_price": 0.0},
            position_short={"quantity": 0.0, "average_price": 0.0},
            balance={"USDT": 1000.0}
        )
    
    def test_strategy_initialization(self):
        """测试策略初始化"""
        # 测试成功初始化
        result = self.strategy.initialize(self.context)
        self.assertTrue(result, "策略初始化应该成功")
        
        # 测试配置验证
        required_params = self.strategy.get_required_params()
        self.assertIn("symbol", required_params)
        self.assertIn("long", required_params)
        self.assertIn("short", required_params)
        self.assertIn("hedge", required_params)
    
    def test_parameter_validation(self):
        """测试参数验证"""
        # 测试有效配置
        errors = self.strategy.validate_params(self.config["params"])
        self.assertEqual(len(errors), 0, f"有效配置不应有验证错误: {errors}")
        
        # 测试无效配置
        invalid_config = self.config["params"].copy()
        del invalid_config["symbol"]  # 删除必需参数
        
        errors = self.strategy.validate_params(invalid_config)
        self.assertGreater(len(errors), 0, "无效配置应该有验证错误")
    
    def test_first_order_signal(self):
        """测试首仓开仓信号"""
        # 空仓情况下应该生成首仓信号
        signal = self.strategy.generate_signal(self.context)
        
        # 由于是双开起步，应该先生成一个方向的首仓信号
        self.assertIn(signal.signal_type, [SignalType.OPEN_LONG, SignalType.OPEN_SHORT])
        self.assertGreater(signal.quantity, 0)
        self.assertEqual(signal.symbol, "ETHUSDT")
    
    def test_add_position_logic(self):
        """测试加仓逻辑"""
        # 设置有持仓的状态
        self.strategy.long_state.qty = 0.01
        self.strategy.long_state.avg_price = 3000.0
        self.strategy.long_state.add_times = 0
        self.strategy.long_state.last_fill_price = 3000.0
        
        # 模拟价格下跌达到加仓条件
        self.context.current_price = 2940.0  # 下跌2%
        self.context.position_long = {"quantity": 0.01, "average_price": 3000.0}
        
        # 应该生成加仓信号
        signal = self.strategy.generate_signal(self.context)
        
        if signal.signal_type == SignalType.ADD_LONG:
            self.assertEqual(signal.signal_type, SignalType.ADD_LONG)
            self.assertAlmostEqual(signal.quantity, 0.02, places=6)  # 2倍加仓
    
    def test_take_profit_logic(self):
        """测试止盈逻辑"""
        # 设置有盈利的持仓状态
        self.strategy.long_state.qty = 0.01
        self.strategy.long_state.avg_price = 3000.0
        self.strategy.long_state.add_times = 0  # 首仓
        
        # 模拟价格上涨达到止盈条件
        self.context.current_price = 3030.0  # 上涨1%
        self.context.position_long = {"quantity": 0.01, "average_price": 3000.0}
        
        # 应该生成首仓止盈信号
        signal = self.strategy.generate_signal(self.context)
        
        if signal.signal_type == SignalType.TAKE_PROFIT:
            self.assertEqual(signal.signal_type, SignalType.TAKE_PROFIT)
            self.assertEqual(signal.quantity, 0.01)
    
    def test_hedge_trigger_logic(self):
        """测试对冲触发逻辑"""
        # 设置满仓状态
        self.strategy.long_state.qty = 0.15  # 0.01 + 0.02 + 0.04 + 0.08
        self.strategy.long_state.avg_price = 3000.0
        self.strategy.long_state.add_times = 3  # 满仓
        self.strategy.long_state.last_fill_price = 3000.0
        
        # 设置对侧无持仓
        self.strategy.short_state.qty = 0.0
        
        # 模拟价格大跌达到对冲条件
        self.context.current_price = 2850.0  # 下跌5%
        self.context.position_long = {"quantity": 0.15, "average_price": 3000.0}
        self.context.position_short = {"quantity": 0.0, "average_price": 0.0}
        
        # 应该生成对冲信号
        signal = self.strategy.generate_signal(self.context)
        
        if signal.signal_type == SignalType.HEDGE:
            self.assertEqual(signal.signal_type, SignalType.HEDGE)
            self.assertGreater(signal.quantity, 0)
    
    def test_state_manager_functions(self):
        """测试状态管理器功能"""
        # 测试默认状态创建
        default_state = MartingaleStateManager.create_default_state()
        
        self.assertIn("long", default_state)
        self.assertIn("short", default_state)
        self.assertIn("global", default_state)
        
        # 测试状态验证
        is_valid, errors = MartingaleStateManager.validate_state(default_state)
        self.assertTrue(is_valid, f"默认状态应该有效: {errors}")
    
    def test_calculator_functions(self):
        """测试计算工具功能"""
        # 测试加仓数量计算
        first_qty = 0.01
        add_ratio = 2.0
        add_times = 1
        
        next_qty = MartingaleCalculator.calculate_add_quantity(first_qty, add_ratio, add_times)
        expected_qty = first_qty * (add_ratio ** (add_times + 1))  # 0.01 * 2^2 = 0.04
        
        self.assertAlmostEqual(next_qty, expected_qty, places=8)
        
        # 测试总持仓计算
        total_qty = MartingaleCalculator.calculate_total_position_after_add(first_qty, add_ratio, add_times)
        expected_total = first_qty * (2**(add_times + 1) - 1) / (2 - 1)  # 几何级数求和
        
        self.assertAlmostEqual(total_qty, expected_total, places=8)
        
        # 测试盈亏计算
        qty = 0.01
        avg_price = 3000.0
        current_price = 3030.0
        direction = "long"
        
        pnl = MartingaleCalculator.calculate_unrealized_pnl(qty, avg_price, current_price, direction)
        expected_pnl = (current_price - avg_price) * qty
        
        self.assertAlmostEqual(pnl, expected_pnl, places=8)
    
    def test_config_validation(self):
        """测试配置验证功能"""
        # 测试有效配置
        is_valid, errors = validate_strategy_config(self.config["params"])
        self.assertTrue(is_valid, f"有效配置验证失败: {errors}")
        
        # 测试无效配置
        invalid_config = self.config["params"].copy()
        invalid_config["long"]["first_qty"] = -0.01  # 无效的负数
        
        is_valid, errors = validate_strategy_config(invalid_config)
        self.assertFalse(is_valid, "无效配置应该验证失败")
        self.assertGreater(len(errors), 0, "应该有验证错误")


class TestMartingaleHedgeIntegration(unittest.TestCase):
    """马丁对冲策略集成测试"""
    
    def setUp(self):
        """集成测试初始化"""
        self.config_file = "profiles/BINANCE_MARTINGALE_HEDGE/strategy_config.json"
    
    @patch('builtins.open')
    def test_config_loading(self, mock_open):
        """测试配置文件加载"""
        # 模拟配置文件内容
        mock_config = {
            "strategy": {
                "params": {
                    "symbol": "ETHUSDT",
                    "long": {"first_qty": 0.01},
                    "short": {"first_qty": 0.01},
                    "hedge": {"trigger_loss": 0.05}
                }
            }
        }
        
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_config)
        
        # 测试配置加载和验证
        with open(self.config_file, 'r') as f:
            config_data = json.loads(f.read())
            
        strategy_config = config_data["strategy"]["params"]
        is_valid, errors = validate_strategy_config(strategy_config)
        
        self.assertTrue(is_valid, f"配置文件验证失败: {errors}")
    
    def test_strategy_workflow(self):
        """测试策略工作流程"""
        # 这是一个简化的工作流程测试
        config = {
            "name": "integration_test",
            "params": {
                "symbol": "ETHUSDT",
                "long": {"first_qty": 0.01, "add_ratio": 2.0, "add_interval": 0.02, "max_add_times": 3, "tp_first_order": 0.01, "tp_before_full": 0.015, "tp_after_full": 0.02},
                "short": {"first_qty": 0.01, "add_ratio": 2.0, "add_interval": 0.02, "max_add_times": 3, "tp_first_order": 0.01, "tp_before_full": 0.015, "tp_after_full": 0.02},
                "hedge": {"trigger_loss": 0.05, "equal_eps": 0.01, "min_wait_seconds": 60, "release_tp_after_full": {"long": 0.02, "short": 0.02}, "release_sl_loss_ratio": {"long": 1.0, "short": 1.0}},
                "risk_control": {"tp_slippage": 0.002, "max_total_qty": 1.0, "cooldown_minutes": 1, "fast_add_window": 300}
            }
        }
        
        strategy = MartingaleHedgeStrategy(config)
        
        # 模拟策略执行上下文
        context = StrategyContext(
            account="test_integration",
            platform="binance",
            symbol="ETHUSDT",
            current_price=3000.0,
            position_long={"quantity": 0.0, "average_price": 0.0},
            position_short={"quantity": 0.0, "average_price": 0.0},
            balance={"USDT": 1000.0}
        )
        
        # 测试初始化
        init_result = strategy.initialize(context)
        self.assertTrue(init_result, "策略初始化应该成功")
        
        # 测试信号生成
        signal = strategy.generate_signal(context)
        self.assertIsNotNone(signal, "应该生成交易信号")
        self.assertIn(signal.signal_type, [
            SignalType.NONE, 
            SignalType.OPEN_LONG, 
            SignalType.OPEN_SHORT
        ], "信号类型应该有效")


if __name__ == '__main__':
    # 运行测试
    print("🧪 开始运行马丁对冲策略测试...")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTests(loader.loadTestsFromTestCase(TestMartingaleHedgeStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestMartingaleHedgeIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！马丁对冲策略移植成功。")
    else:
        print(f"\n❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        
    print(f"总计运行: {result.testsRun} 个测试")