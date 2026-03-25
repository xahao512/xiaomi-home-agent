# MIoT-Spec-V2 协议说明

## 概述

MIoT-Spec-V2 (MIoT Specification Version 2) 是小米 IoT 平台制定的物联网设备功能描述标准协议。

## 基本概念

### URN 格式

```
urn:<namespace>:<type>:<name>:<value>[:<vendor-product>:<version>]
```

- `namespace`: 命名空间
  - `miot-spec-v2`: 小米官方定义
  - `bluetooth-spec`: 蓝牙 SIG 定义
  - 其他: 第三方厂商定义

### 层级结构

```
Device (设备)
├── Service (服务)
│   ├── Property (属性)
│   ├── Event (事件)
│   └── Action (动作)
```

## 设备示例

### 灯具设备

```
urn:miot-spec-v2:device:light:0000A001:xiaomi-lightbulb:1
├── siid=2: Switch Sensor (开关服务)
│   ├── piid=1: switch_status (开关状态)
│   └── piid=2: brightness (亮度)
├── siid=3: Color Temperature (色温服务)
│   └── piid=1: color_temperature (色温值)
└── siid=4: Extension (扩展服务)
    └── piid=1: mode (模式)
```

### 空调设备

```
urn:miot-spec-v2:device:air-condition:0000A004:xiaomi-ac:1
├── siid=2: Switch Sensor (开关服务)
│   └── piid=1: switch_status
├── siid=3: Temperature (温度服务)
│   ├── piid=1: target_temperature
│   └── piid=2: ambient_temperature
├── siid=4: Fan Control (风速服务)
│   ├── piid=1: fan_level
│   └── piid=2: vertical_swing
└── siid=5: Mode (模式服务)
    └── piid=1: mode
```

## 常用 siid/piid 参考

### 通用服务 (siid=2)

| piid | 属性 | 类型 | 说明 |
|------|------|------|------|
| 1 | switch_status | bool | 开关状态 |
| 2 | brightness | int | 亮度 (0-100) |
| 3 | color_temperature | int | 色温 (2700-6500) |

### 空调服务 (siid=3)

| piid | 属性 | 类型 | 说明 |
|------|------|------|------|
| 1 | target_temperature | int | 目标温度 (16-30) |
| 2 | ambient_temperature | int | 环境温度 |

### 模式服务 (siid=5)

| 值 | 模式 |
|----|------|
| 0 | 自动 |
| 1 | 制冷 |
| 2 | 制热 |
| 3 | 送风 |
| 4 | 除湿 |

## API 调用格式

### 云端控制

```http
POST https://api.io.mi.com/app/device/trigger/{did}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "did": "设备ID",
  "siid": 服务ID,
  "piid": 属性ID,
  "value": 属性值
}
```

### 本地控制 (MQTT)

```json
{
  "did": "设备ID",
  "command": {
    "siid": 服务ID,
    "piid": 属性ID,
    "value": 属性值
  }
}
```

## 错误码

| code | 说明 |
|------|------|
| 0 | 成功 |
| -1 | 通用错误 |
| -2 | 参数错误 |
| -3 | 设备不在线 |
| -4 | Token 过期 |
| -5 | 无权限 |
| -6 | 设备不支持该操作 |
