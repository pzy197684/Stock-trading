# 🔐 API密钥安全配置指南

## ⚠️ 重要安全提示

**请务必遵循以下安全原则，确保您的资金安全！**

## 🔑 Binance API密钥设置步骤

### 1. 登录Binance账户
1. 访问 [Binance官网](https://www.binance.com)
2. 登录您的账户

### 2. 创建API密钥
1. 进入【账户管理】→【API管理】
2. 点击【创建API】
3. 选择【系统生成】
4. 输入API标签名称（如：`马丁对冲策略`）

### 3. ⚡ 关键权限设置
```
✅ 必须启用的权限:
   • 启用期货交易 (Enable Futures)
   • 启用读取 (Enable Reading)

❌ 严禁启用的权限:  
   • 启用现货和杠杆交易 (Spot & Margin Trading) - 禁用
   • 启用提现 (Enable Withdrawals) - 禁用  
   • 启用内部转账 (Enable Internal Transfer) - 禁用
   • 启用期权交易 (Enable Options) - 禁用
```

### 4. 🌐 IP白名单设置
**强烈建议设置IP白名单限制:**
1. 在API设置页面点击【编辑】
2. 添加您的服务器IP地址
3. 保存设置

## 🔒 配置文件安全

### 1. 文件权限设置
```bash
# Windows PowerShell
icacls "accounts\*\*.json" /grant:r "$($env:USERNAME):F" /T
icacls "accounts\*\*.json" /remove "Users" /T
```

### 2. Git忽略设置
确保 `.gitignore` 文件包含:
```
# API密钥配置
accounts/*/binance_api.json
accounts/*/coinw_api.json  
accounts/*/okx_api.json
*.key
*.secret

# 不要忽略模板和说明文件
!accounts/README.md
!accounts/**/template_*.json
```

### 3. 环境变量替代方案
对于生产环境，建议使用环境变量:
```json
{
  "API_KEY": "${BINANCE_API_KEY}",
  "API_SECRET": "${BINANCE_API_SECRET}"
}
```

## 🛡️ 安全检查清单

### 部署前检查
- [ ] API权限设置正确（仅期货交易+读取）
- [ ] IP白名单已设置（生产环境必须）
- [ ] 配置文件权限正确设置
- [ ] 密钥文件已添加到.gitignore
- [ ] 使用独立的交易专用子账户

### 定期安全维护
- [ ] 每季度轮换API密钥
- [ ] 监控API使用日志
- [ ] 检查账户余额变动
- [ ] 更新IP白名单（如有变化）

## 🚨 风险控制建议

### 1. 资金管理
- 仅在专用子账户中放入策略运行所需资金
- 设置合理的最大仓位限制
- 启用账户余额告警

### 2. 监控告警
- 启用异常登录通知
- 设置大额交易提醒
- 配置API调用频率监控

### 3. 应急处理
- 记录API密钥创建时间和权限
- 准备紧急停止脚本
- 建立资金安全联系人

## 📞 紧急情况处理

如果怀疑API密钥泄露:
1. **立即禁用** Binance后台的API密钥
2. **检查交易记录** 确认是否有异常交易
3. **联系Binance客服** 如有资金安全问题
4. **重新生成密钥** 使用新的API密钥
5. **分析泄露原因** 加强安全防护

## ☎️ 技术支持

- Binance API文档: https://binance-docs.github.io/apidocs/
- Binance客服: https://www.binance.com/zh-CN/support
- 项目技术支持: 检查项目README或联系维护者

---

**🔴 重要提醒**: 任何人都无法确保100%的安全，请始终遵循最佳安全实践，仅投入可承受损失的资金进行交易！