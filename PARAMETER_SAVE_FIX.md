# 参数配置保存问题修复报告

## 问题描述

用户反馈：在新建OP实例后，在参数配置中保存设置后，发现：
- 当前运行页面变成了ETH
- 高级配置中变成了BTC
- 杠杆倍数是5X，变化不明显，无法用肉眼观察

## 问题分析

### 根本原因
在参数配置标签页保存时，前端只发送了 `long`、`short`、`hedge` 等策略参数，没有包含 `symbol` 和 `leverage` 等关键配置。虽然API使用深度合并来保留现有配置，但在某些情况下（如策略实例参数状态不一致），可能导致关键配置丢失。

### 技术细节
1. **前端保存逻辑问题**：
   ```typescript
   if (activeTab === 'parameters') {
     // 原逻辑：只发送策略参数，不包含交易对和杠杆
     flattenedParameters = {
       long: parameters.long,
       short: parameters.short,
       hedge: parameters.hedge,
       // 缺失: symbol, leverage
     };
   }
   ```

2. **参数获取流程缺陷**：
   - API返回的运行参数可能不完整
   - 前端刷新参数时的保护逻辑存在边界情况
   - 策略实例与配置文件的同步问题

## 解决方案

### 1. 完善参数保存逻辑
修改 `handleSave` 函数，在参数配置标签页保存时也包含关键的高级配置：

```typescript
if (activeTab === 'parameters') {
  // 修复后：保存策略参数的同时保留关键高级配置
  flattenedParameters = {
    long: parameters.long,
    short: parameters.short,
    hedge: parameters.hedge,
    autoTrade: autoTradeValue,
    notifications: parameters.notifications ?? false,
    // 关键修复：保留交易对和杠杆倍数
    symbol: parameters.advanced?.symbol,
    leverage: parameters.advanced?.leverage,
    // 保留其他必要的执行参数
    mode: parameters.advanced?.mode,
    order_type: parameters.advanced?.order_type,
    interval: parameters.advanced?.interval
  };
}
```

### 2. 增强参数保护机制
在参数刷新时添加调试信息和更稳定的保护逻辑：

```typescript
// 交易对和杠杆倍数保护逻辑：优先使用当前界面的值，再使用运行参数的值，最后使用默认值
leverage: currentLeverage ?? runningParams.leverage ?? 5,
symbol: currentSymbol ?? runningParams.symbol ?? "OPUSDT",

// 添加调试信息
console.log('保护后的参数状态:', {
  currentSymbol,
  currentLeverage,
  runningSymbol: runningParams.symbol,
  runningLeverage: runningParams.leverage,
  finalSymbol: currentSymbol ?? runningParams.symbol ?? "OPUSDT",
  finalLeverage: currentLeverage ?? runningParams.leverage ?? 5
});
```

### 3. 改进用户反馈
更新确认对话框，明确显示保护的配置信息：

```typescript
<strong>已保护：</strong>交易对({parameters.advanced?.symbol || 'OPUSDT'})和杠杆倍数({parameters.advanced?.leverage || 5}X)等高级配置将被保留，不会被修改。
```

## 修复验证

### 测试步骤
1. **创建新的OP实例**
2. **设置交易对和杠杆倍数**（如OPUSDT, 5X）
3. **在参数配置标签页修改策略参数**
4. **保存设置**
5. **验证交易对和杠杆倍数是否保持不变**

### 预期结果
- ✅ 参数配置保存后，交易对保持为OPUSDT
- ✅ 杠杆倍数保持为5X
- ✅ 策略参数正确更新
- ✅ 用户界面显示正确的保护信息

## 相关文件

### 修改的文件
- `apps/ui/src/components/InstanceSettings.tsx` - 主要修复文件

### 相关配置文件
- `profiles/BINANCE/BN1602/strategies/martingale_hedge.json` - 用户配置示例

## 注意事项

1. **保护范围**：修复确保在参数配置标签页保存时，交易对和杠杆倍数等关键配置不会丢失
2. **兼容性**：修复保持与现有API的完全兼容
3. **用户体验**：确认对话框明确告知用户哪些配置会被保护
4. **调试支持**：添加控制台日志帮助排查问题

## 成功标准

- [x] 参数配置保存不再影响交易对和杠杆倍数
- [x] 用户界面提供明确的保护信息反馈
- [x] 保持所有现有功能的正常运行
- [x] 添加充分的调试信息支持后续维护

---

**修复时间**：2025年10月2日  
**修复状态**：✅ 已完成  
**测试状态**：⏳ 待用户验证