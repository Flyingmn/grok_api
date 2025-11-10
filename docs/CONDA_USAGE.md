# Camoufox爬虫框架 - Conda环境使用指南

## 🚀 快速开始

### 1. 设置环境
```bash
# 运行设置脚本
./setup_conda_env.sh
```

### 2. 激活环境
```bash
# 方法1: 使用激活脚本
./activate_env.sh

# 方法2: 手动激活
conda activate camoufox-crawler
```

### 3. 验证安装
```bash
python setup_and_verify.py
```

### 4. 快速测试
```bash
python quick_test.py
```

## 📋 环境管理

### 查看环境信息
```bash
# 列出所有环境
conda env list

# 查看当前环境包列表
conda list

# 查看特定环境包列表
conda list -n camoufox-crawler
```

### 更新环境
```bash
# 更新环境（如果修改了environment.yml）
conda env update -n camoufox-crawler -f environment.yml

# 更新特定包
conda update -n camoufox-crawler package_name
```

### 导出环境
```bash
# 导出环境配置
conda env export -n camoufox-crawler > environment_backup.yml
```

### 删除环境
```bash
conda env remove -n camoufox-crawler
```

## 🔧 故障排除

### 1. conda命令不可用
```bash
# 初始化conda
conda init bash  # 或 conda init zsh
source ~/.bashrc  # 或 source ~/.zshrc
```

### 2. 环境激活失败
```bash
# 重新创建环境
conda env remove -n camoufox-crawler
./setup_conda_env.sh
```

### 3. Camoufox不可用
```bash
# 在环境中重新安装
conda activate camoufox-crawler
conda install camoufox -c conda-forge
```

### 4. Playwright浏览器问题
```bash
# 重新安装浏览器
conda activate camoufox-crawler
playwright install firefox
```

### 5. 权限问题
```bash
# 给脚本执行权限
chmod +x setup_conda_env.sh
chmod +x activate_env.sh
```

## 💡 最佳实践

1. **始终在激活的环境中工作**
   ```bash
   conda activate camoufox-crawler
   python your_script.py
   ```

2. **定期更新环境**
   ```bash
   conda update -n camoufox-crawler --all
   ```

3. **备份重要数据**
   - cookies/ 目录中的登录信息
   - screenshots/ 目录中的截图
   - 自定义配置文件

4. **使用版本控制**
   - 将environment.yml加入版本控制
   - 排除logs/, cookies/, screenshots/目录

## 🎯 开发工作流

```bash
# 1. 激活环境
conda activate camoufox-crawler

# 2. 开发和测试
python quick_test.py

# 3. 运行完整测试
python examples/test_google_ai_studio.py

# 4. 完成后退出环境
conda deactivate
```
