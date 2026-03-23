# Xiaomi Home Agent Skill for OpenClaw

基于小米官方 ha_xiaomi_home 架构封装的 OpenClaw Agent Skill，用于控制小米米家智能设备和场景。

## ✨ 功能特性

- 🔐 **OAuth2.0 安全认证**：米家账号扫码登录，Token 本地加密存储
- ☁️ **云端控制**：通过小米云 API 控制设备
- 🏠 **本地控制**：支持局域网直连（需小米中枢网关）
- 📱 **设备管理**：查询设备列表、获取实时状态
- 🎛️ **设备控制**：开关、亮度、温度、模式等属性调节
- 🎬 **场景执行**：触发米家智能场景和自动化

## 📦 安装

### 方式 1：直接克隆

```bash
cd /Applications/QClaw.app/Contents/Resources/openclaw/config/skills/
git clone https://github.com/yourusername/xiaomi-home-agent.git
```

### 方式 2：手动安装

1. 下载本仓库到 OpenClaw 的 skills 目录
2. 安装依赖：`pip install -r requirements.txt`

## 🚀 快速开始

```bash
cd xiaomi-home-agent

# 1. 环境检查
python3 scripts/setup_env.py

# 2. 登录米家账号
python3 scripts/auth.py --login

# 3. 同步设备列表
python3 scripts/sync_devices.py

# 4. 查看设备
python3 scripts/list_devices.py

# 5. 控制设备
python3 scripts/control_device.py --did <设备ID> --action turn_on
```

## 📖 使用说明

### 设备控制

```bash
# 开灯
python3 scripts/control_device.py --did <did> --action turn_on

# 关灯
python3 scripts/control_device.py --did <did> --action turn_off

# 设置亮度 (0-100)
python3 scripts/control_device.py --did <did> --action set_brightness --value 50

# 设置温度
python3 scripts/control_device.py --did <did> --action set_temperature --value 26
```

### 场景执行

```bash
# 列出所有场景
python3 scripts/trigger_scene.py --list

# 执行场景
python3 scripts/trigger_scene.py --name "回家模式"
```

### 设备状态查询

```bash
python3 scripts/get_device_status.py --did <设备ID>
```

## 🔧 配置

编辑 `config/config.yaml`：

```yaml
xiaomi:
  region: cn  # cn, de, us, sg, in, ru

control_mode: cloud  # cloud, local, auto

local:
  gateway_ip: auto  # 或指定 IP 如 192.168.1.100
```

## 📁 目录结构

```
xiaomi-home-agent/
├── SKILL.md                    # 技能描述
├── requirements.txt            # Python 依赖
├── config/
│   └── config.yaml            # 配置文件
├── scripts/
│   ├── setup_env.py           # 环境检查
│   ├── auth.py                # 认证管理
│   ├── list_devices.py        # 设备列表
│   ├── get_device_status.py   # 状态查询
│   ├── control_device.py      # 设备控制
│   ├── trigger_scene.py       # 场景执行
│   └── sync_devices.py        # 数据同步
└── reference/
    ├── device_types.json      # 设备类型映射
    ├── miot_spec.md          # MIoT 协议说明
    └── error_codes.md        # 错误码对照
```

## 🔒 安全说明

- OAuth2.0 Token 存储在本地 `config/auth.json`，请勿泄露
- 窗帘、空调、门锁等设备操作前会提示确认
- 支持本地模式，数据不经过云端

## 📚 技术架构

本 Skill 基于以下技术栈：
- [ha_xiaomi_home](https://github.com/XiaoMi/ha_xiaomi_home) - 小米官方 Home Assistant 集成
- [MIoT-Spec-V2](https://iot.mi.com/v2/new/doc/introduction/knowledge/spec) - 小米 IoT 协议规范
- OAuth2.0 - 安全认证机制
- MQTT - 消息订阅与推送

## 📝 License

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 PR！

## 🔗 相关链接

- [小米 ha_xiaomi_home](https://github.com/XiaoMi/ha_xiaomi_home)
- [MIoT 协议文档](https://iot.mi.com/v2/new/doc/introduction/knowledge/spec)
- [OpenClaw 文档](https://docs.openclaw.ai)
