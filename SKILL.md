---
name: xiaomi-home-agent
description: |
  基于 ha_xiaomi_home 官方架构的小米米家智能设备控制 Skill。
  支持设备查询、状态监控、设备控制（开关/亮度/温度等）、场景执行。
  支持云端和本地两种控制模式，使用 OAuth2.0 安全认证。
  
  使用场景：
  - 用户说 "查看米家设备"、"列出所有智能设备"
  - 用户说 "打开客厅灯"、"关闭空调"、"调节亮度到50%"
  - 用户说 "执行回家场景"、"运行睡眠模式"
  - 用户说 "查看卧室温度"、"获取设备状态"
metadata:
  openclaw:
    emoji: "🏠"
    requires:
      bins:
        - python3
      pypi:
        - requests
        - paho-mqtt
        - pycryptodome
---

# Xiaomi Home Agent Skill

基于小米官方 ha_xiaomi_home 架构封装的 OpenClaw Agent Skill，用于控制小米米家智能设备和场景。

## 功能特性

- 🔐 **安全认证**：OAuth2.0 登录，Token 本地加密存储
- ☁️ **云端控制**：通过小米云 MQTT 订阅设备消息
- 🏠 **本地控制**：支持局域网直连（需中枢网关）
- 📱 **设备管理**：查询设备列表、获取设备状态
- 🎛️ **设备控制**：开关、亮度、温度、模式等属性调节
- 🎬 **场景执行**：触发米家场景/自动化
- 🔄 **实时同步**：设备状态变更实时推送

## 快速开始

### 1. 环境检查

```bash
python3 scripts/setup_env.py
```

### 2. 首次登录

```bash
python3 scripts/auth.py --login
```

使用米家 APP 扫描二维码完成 OAuth2.0 授权。

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

# 设置亮度
python3 scripts/control_device.py --did <设备ID> --action set_brightness --value 50

# 设置温度
python3 scripts/control_device.py --did <设备ID> --action set_temperature --value 26
```

## 决策逻辑

| 用户意图 | 执行脚本 | 说明 |
|---------|---------|------|
| "有哪些设备"、"设备列表" | `scripts/list_devices.py` | 获取所有设备快照 |
| "查看状态"、"获取状态" | `scripts/get_device_status.py --did <did>` | 查询指定设备状态 |
| "打开/关闭"、"调节亮度/温度" | `scripts/control_device.py` | 执行设备控制命令 |
| "执行场景"、"运行模式" | `scripts/trigger_scene.py` | 触发米家场景 |
| "刷新设备"、"同步设备" | `scripts/sync_devices.py` | 从云端同步设备列表 |

## 安全约束

- ⚠️ **窗帘、空调、门锁**等涉及安全和能耗的设备，操作前需口头确认
- 🔒 **绝不泄露** `config/auth.json` 中的敏感 Token
- 🏠 **本地模式**仅在局域网内可用，需小米中枢网关支持

## 配置文件

配置文件位于 `config/config.yaml`：

```yaml
# 小米账号配置
xiaomi:
  region: cn  # 区域: cn(中国), de(欧洲), us(美国), sg(新加坡), in(印度), ru(俄罗斯)
  
# 控制模式
control_mode: cloud  # cloud(云端) / local(本地) / auto(自动)

# 本地模式配置（仅当 control_mode 为 local 或 auto 时有效）
local:
  gateway_ip: auto  # 中枢网关IP，auto 表示自动发现
  
# MQTT 配置
mqtt:
  keepalive: 60
  reconnect_interval: 5
```

## 目录结构

```
xiaomi-home-agent/
├── SKILL.md                    # 本文件
├── requirements.txt            # Python 依赖
├── config/
│   ├── config.yaml            # 配置文件
│   └── auth.json              # 认证信息（自动生成，勿手动修改）
├── scripts/
│   ├── setup_env.py           # 环境检查与安装
│   ├── auth.py                # 认证管理
│   ├── list_devices.py        # 设备列表查询
│   ├── get_device_status.py   # 设备状态查询
│   ├── control_device.py      # 设备控制
│   ├── trigger_scene.py       # 场景执行
│   └── sync_devices.py        # 设备同步
└── reference/
    ├── device_types.json      # 设备类型映射表
    ├── miot_spec.md           # MIoT-Spec-V2 协议说明
    └── error_codes.md         # 错误码对照表
```

## 依赖说明

本 Skill 基于以下技术栈：
- **ha_xiaomi_home**: 小米官方 Home Assistant 集成架构
- **MIoT-Spec-V2**: 小米 IoT 设备协议规范
- **OAuth2.0**: 安全认证机制
- **MQTT**: 消息订阅与推送

## 更多信息

- 小米官方项目：https://github.com/XiaoMi/ha_xiaomi_home
- MIoT 协议文档：https://iot.mi.com/v2/new/doc/introduction/knowledge/spec
