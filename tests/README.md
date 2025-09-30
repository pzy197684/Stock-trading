# Tests测试目录说明

## 📁 目录结构

```
tests/                          # 测试文件目录
├── strategy/                   # 策略测试目录
│   └── test_martingale_hedge.py # 马丁对冲策略测试
├── test_accounts.py            # 账户功能测试（项目根目录）
└── test_recovery_strategy.py   # 解套策略测试（项目根目录）
```

## 📋 测试类型说明

### 🧪 单元测试
针对单个组件或功能的测试
- 策略逻辑测试
- 工具函数测试
- 数据模型测试
- 状态管理测试

### 🔗 集成测试
组件间交互和系统整体功能测试
- 策略执行流程测试
- 交易所接口测试
- 账户管理测试
- 配置加载测试

### 📊 策略回测
使用历史数据验证策略效果
- 历史数据回放
- 策略性能分析
- 风控机制验证
- 参数优化测试

## 🔧 测试框架

### 使用的测试库
- `unittest` - Python标准测试框架
- `pytest` - 高级测试框架（推荐）
- `mock` - 模拟对象库

### 测试命名规范
- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试方法: `test_*`

## 🎯 主要测试文件

### 📈 test_martingale_hedge.py
马丁对冲策略核心测试
- 状态管理器测试
- 计算逻辑测试
- 策略信号测试
- 风控机制测试

### 🏦 test_accounts.py
账户管理功能测试
- 账户配置加载
- API密钥验证
- 权限检查
- 安全性测试

### 🔄 test_recovery_strategy.py
解套策略功能测试
- 解套逻辑验证
- 状态持久化测试
- 配置兼容性测试
- 错误处理测试

## 🚀 运行测试

### 运行所有测试
```bash
# 使用pytest
pytest tests/

# 使用unittest
python -m unittest discover tests/
```

### 运行特定测试
```bash
# 运行策略测试
pytest tests/strategy/

# 运行单个测试文件
pytest tests/test_accounts.py

# 运行特定测试方法
pytest tests/test_accounts.py::TestAccountManager::test_load_config
```

### 测试覆盖率
```bash
# 生成覆盖率报告
pytest --cov=core tests/

# 生成HTML报告
pytest --cov=core --cov-report=html tests/
```

## 📝 编写测试

### 测试模板
```python
import unittest
from unittest.mock import Mock, patch

class TestMyComponent(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.component = MyComponent()
    
    def tearDown(self):
        """测试后清理"""
        pass
    
    def test_basic_functionality(self):
        """测试基本功能"""
        result = self.component.do_something()
        self.assertEqual(result, expected_value)
    
    @patch('external.dependency')
    def test_with_mock(self, mock_dependency):
        """使用模拟对象的测试"""
        mock_dependency.return_value = 'mocked_result'
        result = self.component.use_dependency()
        self.assertEqual(result, 'expected_result')
```

## ⚠️ 测试最佳实践

1. **隔离性**: 每个测试独立，不依赖其他测试
2. **可重复**: 多次运行结果一致
3. **快速性**: 单元测试应该快速执行
4. **清晰性**: 测试名称和断言清晰明确
5. **覆盖性**: 重要逻辑分支都要覆盖

## 🔍 调试测试

### 详细输出
```bash
pytest -v tests/
```

### 停在第一个失败
```bash
pytest -x tests/
```

### 调试模式
```bash
pytest --pdb tests/
```

## 📊 持续集成

测试应该集成到CI/CD流程中：
1. 代码提交时自动运行测试
2. 测试失败时阻止合并
3. 定期运行完整测试套件
4. 监控测试覆盖率变化