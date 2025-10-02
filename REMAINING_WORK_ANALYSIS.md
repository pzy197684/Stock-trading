# 剩余工作计划和优先级分析

## 📊 当前进度总结

### ✅ 已完成工作 (Stage 1 & 2)
1. **测试文件清理**: 删除11个临时测试文件，清理1000+行测试代码
2. **API服务统一**: 创建apiService.ts，替换20+处重复fetch调用
3. **默认值配置统一**: 创建DEFAULT_CONFIG，消除硬编码默认值
4. **主要组件重构**:
   - ✅ CurrentRunning.tsx (API调用+默认值统一)
   - ✅ ConsoleTools.tsx (已经很干净)  
   - ✅ InstanceSettings.tsx (API调用+默认值统一)

## 🔄 剩余工作清单

### 🎯 高优先级 (立即执行)

#### 1. 冗余文件清理
```
📂 需要删除的文件:
- apps/ui/src/components/LogsPanel_old.tsx (468行，已过期)
- 可能存在的其他 *_old.* 或 *_backup.* 文件
- 过期的配置文件和模板
```

#### 2. 小组件重构验证
```
📂 需要检查的组件:
- AccountPanel.tsx (检查API调用和默认值)
- GlobalSettings.tsx (检查硬编码配置)
- PlatformConfig.tsx (检查模板和默认值)
- StrategyPanel.tsx (检查策略配置)
- LogsPanel.tsx (确认与old版本的区别)
```

### 🟡 中优先级 (后续执行)

#### 3. 后端API精炼
```
📂 需要分析:
- apps/api/main.py (检查重复API端点)
- core/state_store.py (清理备份和快照逻辑重复)
- core/strategy/ 目录 (清理legacy迁移代码)
```

#### 4. 配置文件整理
```
📂 需要清理:
- profiles/ 目录下的重复配置
- accounts/ 目录下的测试账户
- state/ 目录下的临时状态文件
- 模板文件去重和标准化
```

### 🟢 低优先级 (可选执行)

#### 5. 文档整理
```
📂 报告文件清理:
- 保留: REFACTORING_STAGE1_COMPLETE.md, REFACTORING_STAGE2_COMPLETE.md
- 考虑归档: NEW_INSTANCE_DEFAULT_FIX.md, PARAMETER_*_FIX.md 等修复报告
- 整合: CODE_ANALYSIS_INITIAL.md, CODE_REDUNDANCY_ANALYSIS.md
```

## 🚀 建议执行顺序

### 阶段3: 组件清理和验证 (1-2小时)
1. **删除过期文件**: LogsPanel_old.tsx 等
2. **小组件快速检查**: 确认是否使用统一API和配置
3. **编译验证**: 确保所有组件正常工作

### 阶段4: 后端代码精炼 (2-3小时)  
1. **API端点分析**: 查找重复和未使用的端点
2. **状态管理优化**: 清理备份和快照重复逻辑
3. **Legacy代码清理**: 删除旧版本迁移代码

### 阶段5: 配置和数据清理 (1-2小时)
1. **测试数据清理**: 删除测试账户和临时配置
2. **模板标准化**: 统一配置模板格式
3. **状态文件整理**: 清理临时状态文件

## 💡 关键发现

### 还未处理的重复问题
1. **备份逻辑重复**: state_store.py中多种备份机制
2. **模板配置重复**: PlatformConfig.tsx中硬编码模板
3. **Legacy代码残留**: recovery模块中的旧版本兼容代码

### 风险评估
- 🟢 **低风险**: 删除LogsPanel_old.tsx等明确过期文件
- 🟡 **中风险**: 后端API重构，需要仔细测试
- 🔴 **需谨慎**: 配置文件清理，可能影响现有实例

## 📋 下一步行动

基于"精炼代码，删除重复逻辑"的目标，建议：

1. **立即执行阶段3**: 删除过期文件，完成组件清理
2. **重点关注**: LogsPanel_old.tsx, PlatformConfig模板重复
3. **验证原则**: 每步都确保功能完整性不受影响
4. **持续监控**: 编译状态和运行时错误

---

**当前状态**: Stage 2 完成 ✅  
**下一目标**: Stage 3 组件清理 🎯  
**预计时间**: 1-2小时  
**风险等级**: 低 🟢