---
name: xiaomi-home-agent
description: |
  基于 mijiaAPI 的小米米家智能设备控制 Skill。
  支持设备查询、状态监控、设备控制（开关/亮度/温度等）、自动化场景。
  使用 mijiaAPI OAuth2.0 安全认证。
  
  使用场景：
  - 用户说 "查看米家设备"、"列出所有智能设备"
  - 用户说 "打开客厅灯"、"关闭空调"、"调节亮度到50%"
  - 用户说 "执行床头灯联动场景"
  - 用户说 "查看卧室温度"、"获取设备状态"
metadata:
  openclaw:
    emoji: "🏠"
    requires:
      bins:
        - python3
      pypi:
        - mijiaAPI
        - pyyaml
        - qrcode
        - pillow
---

# Xiaomi Home Agent Skill

基于 mijiaAPI 封装的 OpenClaw Agent Skill，用于控制小米米家智能设备和场景。

## ✅ 功能特性

- 🔐 **安全认证**：mijiaAPI OAuth2.0 扫码登录
- 📱 **设备管理**：查询设备列表、获取设备状态
- 🎛️ **设备控制**：开关、亮度、温度等属性调节
- 🤖 **自动化场景**：支持自定义联动规则
- 🏠 **多家庭支持**：支持多个米家家庭切换

## 🚀 快速开始

### 1. 环境安装

```bash
cd /Applications/QClaw.app/Contents/Resources/openclaw/config/skills/xiaomi-home-agent
python3 scripts/setup_env.py
```

### 2. 登录米家账号

```bash
# 使用 mijiaAPI 登录（推荐）
/Users/$(whoami)/Library/Python/3.9/bin/mijiaAPI -l

# 扫码后，使用米家 APP 扫描二维码完成授权
```

### 3. 查看设备列表

```bash
python3 scripts/list_devices.py
```

### 4. 控制设备

```bash
# 打开设备
python3 scripts/control_device.py --did <设备ID> --action turn_on

# 关闭设备
python3 scripts/control_device.py --did <设备ID> --action turn_off

# 使用设备名称
python3 scripts/control_device.py --name "床头灯" --action turn_on
```

## 📖 使用说明

### 设备控制

```bash
# 打开/关闭设备
python3 scripts/control_device.py --did <did> --action turn_on
python3 scripts/control_device.py --did <did> --action turn_off

# 设置亮度 (0-100)
python3 scripts/control_device.py --did <did> --action set_brightness --value 50

# 设置温度
python3 scripts/control_device.py --did <did> --action set_temperature --value 26

# 使用设备名称（模糊匹配）
python3 scripts/control_device.py --name "吸顶灯" --action turn_off
```

### 自动化场景

```bash
# 场景1: 床头灯打开时，自动关闭吸顶灯
python3 scripts/auto_scene_bedside.py

# 场景2: 吸顶灯打开时，自动关闭床头灯
python3 scripts/auto_scene_ceiling.py
```

### 设备状态查询

```bash
# 查询设备详细信息
python3 scripts/get_device_status.py --did <设备ID>

# 查询传感器数据（如青萍空气检测仪）
python3 -c "
from mijiaAPI import mijiaAPI
api = mijiaAPI()
# 获取温度、湿度、PM2.5等数据
params = [{'did': '<设备ID>', 'siid': 3, 'piid': i} for i in range(1, 11)]
result = api.get_devices_prop(params)
for item in result:
    if item.get('code') == 0:
        print(f\"piid={item.get('piid')}: {item.get('value')}\")
"
```

## 🔧 技术实现细节

### 设备控制方式

根据设备类型，使用不同的控制方式：

1. **插座/开关类设备**（如 xiaomi.switch.w1）:
   - 使用 `set_devices_prop` 设置 power 属性
   - 参数: `[{'did': did, 'siid': 2, 'piid': 1, 'value': True/False}]`

2. **动作类设备**（如 cuco.plug.v3）:
   - 使用 `run_action` 执行动作
   - 参数: `{'did': did, 'siid': 2, 'aiid': 1}` (开启) / `aiid: 2` (关闭)

3. **传感器类设备**（如青萍空气检测仪）:
   - 使用 `get_devices_prop` 查询属性
   - 温度通常在 siid=3, piid=7
   - CO2 通常在 siid=3, piid=8

### 在线状态字段

**重要**: 小米 API 返回的在线状态字段是 `isOnline` 而不是 `online`。

```python
online = device.get('isOnline', False)  # 正确
# online = device.get('online', False)  # 错误
```

### 错误码处理

常见错误码：
- `-704040003`: 属性不存在
- `-704040005`: Action 不存在
- `-8`: 数据类型无效（通常是设备离线）

## 📁 目录结构

```
xiaomi-home-agent/
├── SKILL.md                    # 本文件
├── README.md                   # 项目介绍
├── LICENSE                     # MIT 许可证
├── requirements.txt            # Python 依赖
├── config/
│   └── config.yaml            # 配置文件
├── scripts/
│   ├── setup_env.py           # 环境检查与安装
│   ├── auth_mijia.py          # mijiaAPI 认证指引
│   ├── list_devices.py        # 设备列表查询
│   ├── get_device_status.py   # 设备状态查询
│   ├── control_device.py      # 设备控制（支持多种方式）
│   ├── auto_scene_bedside.py  # 场景1: 床头灯联动
│   ├── auto_scene_ceiling.py  # 场景2: 吸顶灯联动
│   └── generate_qr.py         # 二维码生成
└── reference/
    ├── device_types.json      # 设备类型映射表
    ├── miot_spec.md           # MIoT-Spec-V2 协议说明
    └── error_codes.md         # 错误码对照表
```

## 🔒 安全说明

- mijiaAPI Token 存储在 `~/.miot/` 目录下
- 支持本地局域网控制和云端控制
- 绝不泄露敏感 Token

## 📝 更新日志

### v1.0.0 (2026-03-24)
- ✅ 初始版本发布
- ✅ 支持 mijiaAPI OAuth2.0 登录
- ✅ 支持设备列表查询
- ✅ 支持设备控制（开关、亮度、温度）
- ✅ 支持自动化场景
- ✅ 修复吸顶灯控制方式（set_devices_prop）
- ✅ 修复在线状态字段（isOnline）

## 🔗 相关链接

- [mijiaAPI](https://github.com/Do1e/mijiaAPI) - 小米米家 API 封装
- [MIoT-Spec-V2](https://iot.mi.com/v2/new/doc/introduction/knowledge/spec) - 小米 IoT 协议规范
- [OpenClaw](https://docs.openclaw.ai) - OpenClaw 文档

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件
