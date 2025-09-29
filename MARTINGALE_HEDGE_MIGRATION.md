# 马丁对冲策略移植文档

## 概述

本项目成功将928文件夹中已实盘验证的马丁对冲策略完整移植到Stock-trading框架中，适配Binance期货交易所。该策略包含从开首单、加仓、止盈、对冲、锁仓、解锁止盈、解锁止损到重开的完整交易链路。

## 策略逻辑

### 核心流程（按执行顺序）

1. **双开起步**
   - 多空各按 `first_qty` 开一笔仓位
   - 支持单向起步模式

2. **动态加仓**
   - 当价格相对首仓/均价的偏离 ≥ `add_interval` 时触发加仓
   - 加仓次数 < `max_add_times`
   - 下一笔数量 = 上一笔数量 × `add_ratio`

3. **普通止盈**（未锁仓状态）
   - **首仓止盈**：单侧仅有首仓时，浮盈比例 ≥ `tp_first_order` → 平该侧
   - **均价止盈**：已加仓，浮盈比例分别 ≥ `tp_before_full`/`tp_after_full` → 平该侧

4. **触发对冲+锁仓**（进入"锁仓态"）
   
   触发条件（任一方向）：
   - 该方向浮亏比例 ≥ `hedge.trigger_loss`
   - 该方向未锁仓（`hedge_locked=False`）
   - 该方向加仓已达上限（`add_times >= max_add_times`）
   - 相反方向持仓量 < 本方向持仓量

   执行：
   - 在相反方向下对冲单，数量 = `qty - opposite_qty`
   - 设置 `hedge_locked=True & hedge_stop=True`（本侧与对侧均停止普通策略）

5. **解锁止盈**（盈利侧先释放）
   
   条件：
   - 在锁仓态下，某一侧浮盈比例 ≥ `hedge.release_tp_after_full.[long/short]`

   执行：
   - 平掉盈利侧全部仓位
   - 将已实现利润记入对侧 `locked_profit`
   - 对侧维持锁仓状态

6. **解锁止损**（亏损侧保护释放）
   
   条件：
   - 当前亏损侧的绝对亏损金额 ≤ `locked_profit × hedge.release_sl_loss_ratio.[long/short]`

   执行：
   - 平掉亏损侧
   - 清除双边锁仓标识

7. **重开机制**（轮次重启）
   
   条件：多空均无仓位且 `hedge_stop=False`
   
   执行：回到步骤1，重新进入循环

## 项目结构

```
core/strategy/martingale_hedge/
├── __init__.py                     # 模块初始化
├── strategy.py                     # 策略核心逻辑类
├── executor.py                     # 策略执行器
├── utils.py                        # 辅助工具函数
└── adapters/                       # 交易所适配器
    ├── __init__.py
    └── binance.py                  # Binance适配器

core/strategy/plugins/
└── martingale_hedge.json          # 策略插件配置

profiles/BINANCE_MARTINGALE_HEDGE/
└── strategy_config.json           # 策略配置示例
```

## 关键特性

### 移植的核心功能

1. **完整的交易逻辑链路**
   - 从928项目移植的所有交易判断逻辑
   - 包含首仓、加仓、止盈、锁仓、解锁的完整流程

2. **风控保护机制**
   - 快速加仓冷却期
   - 仓位限制检查
   - 滑点保护
   - 异常冷静期

3. **状态管理**
   - 持仓状态跟踪
   - 锁仓状态管理
   - 历史记录维护
   - 异常恢复机制

4. **精确计算**
   - Decimal精度计算
   - 成交确认机制
   - 持仓同步校准

### 框架适配特性

1. **分层架构兼容**
   - 策略逻辑与执行分离
   - 交易所接口抽象
   - 可扩展的适配器模式

2. **标准化接口**
   - 统一的信号格式
   - 标准化的响应结构
   - 一致的错误处理

3. **配置驱动**
   - 完整的参数验证
   - 灵活的配置管理
   - 支持热更新

## 配置说明

### 基础参数

```json
{
  "symbol": "ETHUSDT",           // 交易对
  "order_type": "MARKET",        // 订单类型
  "interval": 5,                 // 策略执行间隔（秒）
}
```

### 方向配置（long/short）

```json
{
  "first_qty": 0.01,             // 首仓数量
  "add_ratio": 2.0,              // 加仓倍数
  "add_interval": 0.02,          // 加仓间距（2%）
  "max_add_times": 3,            // 最大加仓次数
  "tp_first_order": 0.01,        // 首仓止盈比例（1%）
  "tp_before_full": 0.015,       // 满仓前止盈比例（1.5%）
  "tp_after_full": 0.02          // 满仓后止盈比例（2%）
}
```

### 对冲配置

```json
{
  "trigger_loss": 0.05,          // 锁仓触发浮亏比例（5%）
  "equal_eps": 0.01,             // 仓位平衡容差
  "min_wait_seconds": 60,        // 锁仓冷却时间
  "release_tp_after_full": {     // 解锁止盈阈值
    "long": 0.02,
    "short": 0.02
  },
  "release_sl_loss_ratio": {     // 解锁止损比例
    "long": 1.0,
    "short": 1.0
  }
}
```

### 风控配置

```json
{
  "tp_slippage": 0.002,          // 止盈滑点保护
  "max_total_qty": 1.0,          // 最大总仓位
  "cooldown_minutes": 1,         // 风控冷却时间
  "fast_add_window": 300         // 快速加仓检测窗口
}
```

## 使用方法

### 1. 环境准备

确保Stock-trading框架已正确安装并配置好Binance API密钥。

### 2. 配置策略

复制 `profiles/BINANCE_MARTINGALE_HEDGE/strategy_config.json` 到你的配置目录，根据需要调整参数。

### 3. 启动策略

```python
from core.strategy.martingale_hedge import MartingaleHedgeStrategy

# 加载配置
with open('strategy_config.json', 'r') as f:
    config = json.load(f)

# 创建策略实例
strategy = MartingaleHedgeStrategy(config['strategy'])

# 初始化策略
context = build_strategy_context(config)
success = strategy.initialize(context)

if success:
    print("策略初始化成功")
else:
    print("策略初始化失败")
```

### 4. 运行监控

策略运行时会输出详细的日志信息，包括：

- 🔍 方向处理状态
- 📥 首仓开仓信号
- 🔄 加仓操作
- 💰 止盈执行
- 🔒 对冲锁仓
- 🔓 解锁操作
- 📊 持仓状态同步

## 风险警告

1. **马丁策略风险**
   - 存在连续亏损的可能
   - 需要充足的账户资金
   - 在单边趋势市场中风险较高

2. **对冲锁仓风险**  
   - 会占用较多保证金
   - 解锁时机需要谨慎把握
   - 可能出现双边止损的情况

3. **技术风险**
   - 网络延迟可能影响执行
   - 需要稳定的服务器环境
   - 建议设置适当的滑点保护

## 建议

1. **参数设置**
   - 首次使用建议降低仓位大小
   - 根据账户资金合理设置 `max_total_qty`
   - 在波动适中的品种上测试

2. **监控管理**
   - 定期检查策略运行状态
   - 关注风险指标变化
   - 及时处理异常情况

3. **资金管理**
   - 预留足够的风险资金
   - 不要使用全部账户资金
   - 考虑设置最大亏损限制

## 技术支持

本策略移植保持了928项目中实盘验证的所有核心逻辑，在Stock-trading框架中提供了更好的可维护性和可扩展性。

如有问题，请参考：
1. 日志文件中的详细执行记录
2. 策略状态文件中的持仓信息
3. 配置文件中的参数说明

## 版本历史

- **v1.0.0** (2025-09-29)
  - 完整移植928项目马丁对冲策略
  - 适配Stock-trading框架架构
  - 支持Binance期货交易
  - 实现完整的锁仓解锁机制
  - 添加风控保护和异常处理