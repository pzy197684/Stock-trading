# Python环境配置指南

## 问题诊断
您的系统中虽然检测到Python，但命令行无法使用。这通常是以下原因：

### 1. Windows Store版本的Python
- Windows Store安装的Python有执行限制
- 建议安装官方版本的Python

### 2. PATH环境变量未配置
- Python已安装但未添加到系统PATH
- 需要手动配置环境变量

## 解决方案

### 方案A: 重新安装Python（推荐）

1. **下载官方Python**
   - 访问: https://www.python.org/downloads/
   - 下载Python 3.8或更新版本

2. **安装时的重要设置**
   - ✅ 勾选 "Add Python to PATH"
   - ✅ 勾选 "Install for all users"
   - 选择 "Customize installation"
   - ✅ 勾选 "pip"
   - ✅ 勾选 "Add Python to environment variables"

3. **验证安装**
   ```cmd
   python --version
   pip --version
   ```

### 方案B: 修复PATH环境变量

1. **找到Python安装目录**
   - 通常在: `C:\Users\[用户名]\AppData\Local\Programs\Python\Python3x\`
   - 或: `C:\Python3x\`

2. **添加到PATH**
   - 右键"此电脑" → "属性"
   - "高级系统设置" → "环境变量"
   - 系统变量中找到"Path"，点击"编辑"
   - 添加Python安装目录
   - 添加Python Scripts目录 (如: `C:\Python3x\Scripts\`)

3. **重启命令提示符**
   - 关闭所有cmd/PowerShell窗口
   - 重新打开测试

### 方案C: 使用Anaconda（适合数据科学）

1. **下载Anaconda**
   - 访问: https://www.anaconda.com/products/distribution

2. **安装Anaconda**
   - 自动配置Python环境
   - 包含大量科学计算包

## 快速测试

安装完成后，运行以下命令测试：

```cmd
python --version
pip --version
python -c "print('Hello Python!')"
```

如果显示版本信息和"Hello Python!"，说明安装成功。

## 启动管理界面

Python环境配置好后，运行：
```
start-fixed.bat
```

该脚本会自动：
1. 查找可用的Python
2. 安装依赖包
3. 启动API服务
4. 启动前端界面
5. 自动打开浏览器