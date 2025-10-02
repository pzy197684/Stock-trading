# 参数设置重构方案

## 现状分析

基于用户修改的策略配置文件 `martingale_hedge.json`，当前系统存在以下问题：

### 1. 当前配置文件结构
```json
{
  "symbol": "OPUSDT",
  "leverage": 5,
  "mode": "dual", 
  "long": { /* 多头参数 */ },
  "short": { /* 空头参数 */ },
  "hedge": { /* 对冲参数 */ },
  "safety": { /* 安全设置 */ },
  "risk_control": { /* 风险控制 */ },
  "execution": { /* 执行参数 */ },
  "monitoring": { /* 监控设置 */ }
}
```

### 2. 功能需求
- **刷新**：只刷新当前标签页的相关参数
- **重置**：只重置当前标签页的参数为默认值
- **保存**：只对当前页面的功能负责
- **消息通知**：统一处理通知设置

## 重构方案

### 一次性解决问题的策略

#### 1. 参数分类管理
```typescript
interface TabParameters {
  parameters: {  // 参数配置标签页
    long: LongParameters;
    short: ShortParameters; 
    hedge: HedgeParameters;
  };
  
  advanced: {   // 高级配置标签页
    symbol: string;
    leverage: number;
    mode: string;
    safety: SafetyConfig;
    risk_control: RiskControlConfig;
    execution: ExecutionConfig;
  };
  
  notifications: boolean; // 消息通知，所有标签页共享
}
```

#### 2. 操作权责分离
- **刷新**：`refreshCurrentTab()` - 只刷新当前标签页数据
- **重置**：`resetCurrentTab()` - 只重置当前标签页为默认值  
- **保存**：`saveCurrentTab()` - 只保存当前标签页修改

#### 3. 数据源统一
```typescript
const PARAMETER_DEFAULTS = {
  long: { /* 从 DEFAULT_CONFIG.parameters.long */ },
  short: { /* 从 DEFAULT_CONFIG.parameters.short */ },
  hedge: { /* 从 DEFAULT_CONFIG.parameters.hedge */ },
  advanced: { /* 从 DEFAULT_CONFIG 其他配置 */ }
};
```

## 实施步骤

### 第一步：重构参数初始化逻辑
- 简化参数状态管理
- 去除复杂的兜底逻辑
- 使用直接的默认值覆盖

### 第二步：实现标签页特定操作
- 根据activeTab确定操作范围
- 实现参数级别的精确控制
- 统一错误处理

### 第三步：消息通知统一化
- 统一notifications和enable_alerts字段
- 避免重复状态管理
- 确保前后端数据一致

## 预期效果

1. **责任明确**：每个功能只处理自己标签页的数据
2. **逻辑简化**：去除复杂的兜底和保护逻辑
3. **操作精确**：按需刷新、重置、保存
4. **维护友好**：代码结构清晰，易于扩展

## 关键原则

- **一次性解决**：通过架构设计避免后续重复问题
- **精确操作**：每个操作只影响应该影响的部分
- **状态简化**：减少状态管理的复杂性
- **默认值统一**：所有默认值来源于统一配置