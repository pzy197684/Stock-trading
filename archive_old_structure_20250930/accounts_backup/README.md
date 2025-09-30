# 📁 账户配置目录

存放交易账户的配置文件和参数设置。

## 目录结构
```
accounts/
├── README.md                    # 本文档
├── account_manager.py           # 账户管理器核心类
├── cli.py                      # 命令行工具
├── .gitignore                  # Git忽略文件（保护密钥安全）
├── BN_MARTINGALE_001/          # 示例账户（币安马丁策略001）
│   ├── binance_api.json        # 币安API密钥配置
│   └── account_settings.json   # 账户设置
└── template_account/           # 账户模板
    ├── template_binance_api.json
    └── account_settings.json
```

## 快速开始

### 1. 创建新账户
```bash
# 进入accounts目录
cd accounts

# 创建测试环境账户
python cli.py create MY_ACCOUNT_NAME --exchange binance --environment testnet

# 创建实盘环境账户  
python cli.py create MY_LIVE_ACCOUNT --exchange binance --environment live
```

### 2. 配置API密钥
编辑生成的`template_binance_api.json`文件，替换为实际的API密钥：
```json
{
  "API_KEY": "your_actual_binance_api_key",
  "API_SECRET": "your_actual_binance_api_secret",
  "API_PASSPHRASE": "",
  // ... 其他配置保持不变
}
```

**重要**: 配置完成后，将文件重命名为`binance_api.json`（去掉template_前缀）

### 3. 验证账户配置
```bash
# 验证单个账户
python cli.py validate MY_ACCOUNT_NAME

# 查看账户详细信息
python cli.py info MY_ACCOUNT_NAME

# 查看所有账户状态
python cli.py list
```

## 命令行工具详解

### 基本命令
- `list` - 列出所有账户及状态
- `info <account>` - 显示账户详细信息
- `validate <account>` - 验证账户配置完整性
- `summary` - 显示账户统计摘要
- `create <account>` - 创建新账户模板
- `check-api <account>` - 检查API密钥配置

### 使用示例
```bash
# 列出所有账户
python cli.py list
# 输出:
#   ✓ BN_MARTINGALE_001     [binance ] [testnet ]
#   ✗ BN_LIVE_002          [binance ] [live    ]

# 查看账户详情
python cli.py info BN_MARTINGALE_001

# 创建新的实盘账户
python cli.py create BN_LIVE_003 --exchange binance --environment live

# 检查API配置
python cli.py check-api BN_MARTINGALE_001
```

## 账户配置说明

### API密钥文件 (`binance_api.json`)
```json
{
  "API_KEY": "your_binance_api_key",
  "API_SECRET": "your_binance_api_secret",  
  "API_PASSPHRASE": "",
  "notes": {
    "exchange": "binance",
    "environment": "testnet",
    "permissions": ["futures_trading"],
    "created_date": "2025-09-29",
    "description": "币安期货交易API密钥"
  },
  "settings": {
    "testnet": true,
    "base_url": "https://testnet.binance.vision",
    "timeout": 30,
    "retry_count": 3
  }
}
```

### 账户设置文件 (`account_settings.json`)
```json
{
  "account_name": "BN_MARTINGALE_001",
  "description": "币安马丁策略测试账户",
  "platform": "binance",
  "environment": "testnet",
  
  "trading_settings": {
    "default_symbol": "ETHUSDT",
    "position_mode": "hedge",
    "margin_type": "isolated",
    "leverage": 1,
    "max_position_size": 0.1
  },
  
  "risk_limits": {
    "max_daily_loss": 100.0,
    "max_total_position": 1.0,
    "max_open_orders": 10
  },
  
  "notification": {
    "enable_alerts": true,
    "webhook_url": "",
    "email_alerts": false
  }
}
```

## 集成到交易策略

### 在Python代码中使用
```python
from accounts.account_manager import AccountManager

# 初始化账户管理器
account_mgr = AccountManager()

# 加载账户配置
success, api_keys = account_mgr.load_api_keys("BN_MARTINGALE_001", "binance")
if success:
    api_key = api_keys["API_KEY"]
    api_secret = api_keys["API_SECRET"]
    
    # 使用API密钥初始化交易客户端
    # client = BinanceClient(api_key, api_secret)

# 加载账户设置
success, settings = account_mgr.load_account_settings("BN_MARTINGALE_001")
if success:
    leverage = settings["trading_settings"]["leverage"]
    max_position = settings["trading_settings"]["max_position_size"]
```

### 在主程序中集成
```python
# 在策略启动时验证账户
def main():
    account_name = "BN_MARTINGALE_001"
    
    # 验证账户配置
    account_mgr = AccountManager()
    success, message = account_mgr.validate_account(account_name)
    
    if not success:
        print(f"账户验证失败: {message}")
        return
    
    # 加载配置并启动策略
    success, api_keys = account_mgr.load_api_keys(account_name)
    success, settings = account_mgr.load_account_settings(account_name)
    
    # 启动交易策略...
```

## 安全注意事项

### 1. API密钥安全
- ✅ 实际API密钥文件已加入`.gitignore`，不会提交到Git仓库
- ✅ 模板文件（`template_*.json`）可以安全提交，不包含真实密钥
- ⚠️ 确保API密钥具有最小必要权限（仅期货交易，无提现权限）
- ⚠️ 定期轮换API密钥

### 2. 环境隔离
- 🧪 **测试环境** (`testnet`): 使用测试网API，无真实资金风险
- 💰 **实盘环境** (`live`): 使用正式API，涉及真实资金

### 3. 配置验证
使用内置验证功能确保配置正确：
```bash
python cli.py validate YOUR_ACCOUNT_NAME
```

## 故障排查

### 常见问题
1. **"API密钥似乎是模板文件"**
   - 原因：未替换模板中的placeholder值
   - 解决：编辑API文件，填入实际密钥

2. **"账户目录不存在"**
   - 原因：账户名输入错误或未创建
   - 解决：使用`list`命令查看可用账户

3. **"JSON格式错误"**
   - 原因：配置文件格式有误
   - 解决：检查JSON语法，确保引号、逗号正确

4. **API连接失败**
   - 检查网络连接
   - 验证API密钥权限
   - 确认测试网/正式网URL配置

### 调试命令
```bash
# 查看详细的账户信息
python cli.py info YOUR_ACCOUNT --verbose

# 检查所有账户状态
python cli.py summary --verbose

# 验证特定账户配置
python cli.py validate YOUR_ACCOUNT
```

## 扩展功能

### 支持新交易所
1. 在`account_manager.py`中扩展交易所支持
2. 创建对应的API模板文件
3. 更新验证逻辑

### 添加新配置项
1. 修改`account_settings.json`模板
2. 更新`AccountManager.load_account_settings()`方法
3. 在策略中读取新配置

---

**最后更新**: 2025-09-29  
**版本**: v1.0  
**维护者**: Stock-trading项目组

### 权限设置
✅ **必须开启的权限:**
- 期货交易权限 (Futures Trading)
- 期货读取权限 (Futures Reading)

❌ **禁止开启的权限:**
- 现货交易权限 (Spot Trading)
- 杠杆交易权限 (Margin Trading)  
- 提现权限 (Withdrawals)
- 充值权限 (Deposits)

### 安全建议
1. **IP白名单**: 强烈建议在Binance后台设置IP白名单
2. **权限最小化**: 只开启策略必需的权限
3. **定期轮换**: 建议定期更换API密钥
4. **备份安全**: API密钥文件不要提交到版本控制系统

## 使用方法

1. 复制对应的JSON模板文件
2. 填入真实的API密钥信息
3. 检查权限设置是否正确
4. 在策略配置中指定账户名称

## 示例配置引用

在策略配置中这样引用账户：
```json
{
  "account_name": "BN_MARTINGALE_001",
  "strategy": "martingale_hedge"
}
```

系统会自动加载 `accounts/BN_MARTINGALE_001/binance_api.json` 文件。