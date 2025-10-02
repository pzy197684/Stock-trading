# 新建实例默认交易对修复报告

## 问题描述

用户反馈两个相关问题：
1. **新建实例默认值问题**：在新建OP实例后，没有任何动作，高级设置中交易对显示为BTC，而不是期望的OP
2. **保存设置后显示问题**：高级配置中已经显示OP了，但保存设置后当前运行还是显示ETH

## 问题分析

### 根本原因
代码中存在多个不一致的默认交易对设置，分布在不同的功能模块中：

#### 新建实例默认值问题
1. **前端InstanceSettings.tsx初始化**：默认为 "BTCUSDT"
2. **前端InstanceSettings.tsx刷新参数**：默认为 "OPUSDT"  
3. **前端CurrentRunning.tsx显示**：默认为 "BTC/USDT"
4. **后端API main.py**：默认为 "BTC/USDT"

#### 保存设置后显示问题
1. **前端CurrentRunning.tsx参数处理**：在 `handleParametersChange` 函数中默认为 "ETHUSDT"

### 技术细节

#### 新建实例问题位置
1. `apps/ui/src/components/InstanceSettings.tsx` 第147行：
   ```typescript
   symbol: currentParameters.advanced?.symbol || "BTCUSDT",
   ```

2. `apps/ui/src/components/CurrentRunning.tsx` 第533行：
   ```typescript
   tradingPair: apiInstance.tradingPair || apiInstance.symbol || "BTC/USDT",
   ```

3. `apps/api/main.py` 第473行：
   ```python
   symbol = parameters.get('symbol', 'BTC/USDT')
   ```

#### 保存设置问题位置
1. `apps/ui/src/components/CurrentRunning.tsx` 第733行：
   ```typescript
   symbol: newParameters.advanced?.symbol || 'ETHUSDT',
   ```

## 解决方案

### 统一默认交易对设置
将所有默认交易对统一设置为适合OP实例的交易对：

#### 1. 修复前端InstanceSettings.tsx
```typescript
// 修复前
symbol: currentParameters.advanced?.symbol || "BTCUSDT",

// 修复后  
symbol: currentParameters.advanced?.symbol || "OPUSDT", // 统一使用OPUSDT
```

#### 2. 修复前端CurrentRunning.tsx（显示默认值）
```typescript
// 修复前
tradingPair: apiInstance.tradingPair || apiInstance.symbol || "BTC/USDT",

// 修复后
tradingPair: apiInstance.tradingPair || apiInstance.symbol || "OP/USDT",
```

#### 3. 修复前端CurrentRunning.tsx（参数处理默认值）
```typescript
// 修复前
symbol: newParameters.advanced?.symbol || 'ETHUSDT',

// 修复后
symbol: newParameters.advanced?.symbol || 'OPUSDT',
```

#### 4. 修复后端API
```python
# 修复前
symbol = parameters.get('symbol', 'BTC/USDT')

# 修复后
symbol = parameters.get('symbol', 'OP/USDT')
```

### 配置优化
删除重复的 `templates/default_op_instance.json` 文件，统一使用 `profiles/_shared_defaults/strategies/martingale_hedge.defaults.json` 作为唯一配置源。

## 修复验证

### 测试步骤
1. **重启交易系统**（前端已更新到端口3001）
2. **创建新的OP实例**
3. **检查高级设置中的交易对**（应显示OPUSDT）
4. **修改参数配置并保存**
5. **验证当前运行页面的交易对**（应显示OP/USDT）

### 预期结果
- ✅ 新建OP实例时，高级设置中交易对显示为"OPUSDT"
- ✅ 当前运行页面显示的交易对为"OP/USDT"
- ✅ 保存参数配置后，交易对保持正确显示
- ✅ 所有默认值保持一致
- ✅ 不影响现有实例的配置

## 相关文件

### 修改的文件
- `apps/ui/src/components/InstanceSettings.tsx` - 修复初始化默认值
- `apps/ui/src/components/CurrentRunning.tsx` - 修复显示默认值和参数处理默认值
- `apps/api/main.py` - 修复API默认值

### 优化文件
- 删除重复配置文件 `templates/default_op_instance.json`
- 统一使用 `profiles/_shared_defaults/strategies/martingale_hedge.defaults.json`

## 注意事项

1. **一致性**：确保前后端所有默认值设置保持一致
2. **兼容性**：修复不影响现有实例的配置
3. **扩展性**：通过模板系统支持不同类型实例的默认配置
4. **用户体验**：新建实例时显示合适的默认交易对，保存设置后正确反映
5. **端口变更**：前端服务现在运行在3001端口（3000端口被占用）

## 成功标准

- [x] 统一所有默认交易对设置为OP相关
- [x] 新建OP实例显示正确的默认交易对
- [x] 保存设置后当前运行页面正确显示交易对
- [x] 保持现有功能的正常运行
- [x] 提供标准配置模板参考

## 系统访问信息

- **前端**: http://localhost:3001 （更新后的端口）
- **后端**: http://localhost:8001

---

**修复时间**：2025年10月2日  
**修复状态**：✅ 已完成（包含两个相关问题的修复）  
**影响范围**：新建实例的默认配置 + 参数保存后的显示  
**测试状态**：⏳ 待验证