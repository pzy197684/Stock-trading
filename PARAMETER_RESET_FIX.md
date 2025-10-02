# 参数重置功能修复测试

## 问题描述
在参数配置中重置时，交易对(symbol)和杠杆倍数(leverage)会被一起重置，但这两个参数属于高级配置，不应该在参数配置重置中被影响。

## 修复内容
修改了 `apps/ui/src/components/InstanceSettings.tsx` 文件中的 `handleReset` 函数：

### 修复前
```typescript
leverage: currentParameters.advanced?.leverage ?? 5,  // 会重置为默认值5
symbol: currentParameters.advanced?.symbol ?? '',    // 会重置为空字符串
```

### 修复后
```typescript
leverage: currentParameters.advanced?.leverage,      // 保持当前杠杆倍数
symbol: currentParameters.advanced?.symbol,          // 保持当前交易对
```

## 测试步骤

1. **设置初始值**
   - 在高级配置中设置交易对为 "ETHUSDT"
   - 设置杠杆倍数为 10
   - 在参数配置中设置一些交易参数

2. **执行重置操作**
   - 切换到"参数配置"标签页
   - 点击"重置"按钮
   - 确认重置操作

3. **验证结果**
   - ✅ 多头参数应该被清零
   - ✅ 空头参数应该被清零  
   - ✅ 对冲参数应该被清零
   - ✅ 风控参数应该被清零
   - ✅ 交易对应该保持为 "ETHUSDT"
   - ✅ 杠杆倍数应该保持为 10
   - ✅ 自动交易应该被设为 false

## 用户界面改进
更新了重置确认对话框的文案，明确告知用户：
"注意：交易对和杠杆倍数作为高级配置将保持不变。"

## 影响范围
- 只影响参数配置标签页的重置功能
- 高级配置标签页不受影响
- 不影响其他重置功能（如账户面板的重置）

## 修复状态
✅ 已完成
✅ 已测试编译无错误
✅ 用户界面文案已更新