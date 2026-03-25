# Xiaomi Home Agent Skill for OpenClaw

基于 mijiaAPI 的小米米家智能设备控制 Skill，支持设备查询、状态监控、设备控制、自动化场景。

## ✨ 功能特性

- 🔐 **mijiaAPI OAuth2.0 认证**：安全扫码登录
- 📱 **设备管理**：查询设备列表、获取实时状态
- 🎛️ **设备控制**：开关、亮度、温度等属性调节
- 🤖 **自动化场景**：支持自定义联动规则
- 🏠 **多家庭支持**：支持多个米家家庭

## 🚀 快速开始

### 安装

```bash
cd /Applications/QClaw.app/Contents/Resources/openclaw/config/skills/
git clone https://github.com/xahao512/xiaomi-home-agent.git
cd xiaomi-home-agent
python3 scripts/setup_env.py
```

### 登录

```bash
# 使用 mijiaAPI 登录
/Users/$(whoami)/Library/Python/3.9/bin/mijiaAPI -l

# 使用米家 APP 扫描二维码完成授权
```

### 使用

```bash
# 查看设备列表
python3 scripts/list_devices.py

# 控制设备
python3 scripts/control_device.py --name "床头灯" --action turn_on
python3 scripts/control_device.py --name "吸顶灯" --action turn_off

# 执行自动化场景
python3 scripts/auto_scene_bedside.py  # 床头灯开 -> 吸顶灯关
python3 scripts/auto_scene_ceiling.py  # 吸顶灯开 -> 床头灯关
```

## 📖 详细文档

详见 [SKILL.md](SKILL.md)

## 🔧 技术亮点

### 智能设备控制
- 自动识别设备类型，选择最佳控制方式
- 支持 `set_devices_prop` 和 `run_action` 两种控制模式
- 自动处理错误码，提供友好的错误提示

### 传感器数据读取
- 支持青萍空气检测仪等传感器设备
- 正确解析温度、湿度、PM2.5、CO2 等数据
- 使用 siid/piid 精确定位属性

### 在线状态检测
- 正确处理 `isOnline` 字段（不是 `online`）
- 实时显示设备在线/离线状态

## 📝 更新日志

### v1.0.0 (2026-03-24)
- 初始版本发布
- 支持 mijiaAPI 登录
- 支持设备列表查询和控制
- 支持自动化场景
- 修复吸顶灯控制方式
- 修复在线状态字段

## 📄 License

MIT License
