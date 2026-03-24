# Xiaomi Home Agent Skill

小米智能家居管理 Agent，支持设备查询、控制、状态监测。

## 功能

- ✅ 查询设备列表（按家庭筛选）
- ✅ 获取设备状态（在线/离线、属性）
- ✅ 控制设备（开/关）
- ✅ Home Assistant 集成（设备状态感知 + 自动化）
- ✅ 定时轮询监测 + 微信通知

## 环境要求

- Python 3.12+（Home Assistant 2025+ 需要）
- Node.js 22+（如需）
- 米家账号

## 快速命令

```bash
# 1. 认证登录
python3 scripts/auth.py --username <手机号/ID> --password <密码>

# 2. 查看设备列表
python3 scripts/list_devices.py

# 3. 查看北京之家设备（home_id: 841001001988）
python3 scripts/list_devices.py --home-id 841001001988

# 4. 获取设备属性
python3 scripts/get_device_status.py --did <设备ID>

# 5. 控制设备
python3 scripts/control_device.py --did <设备ID> --action turn_on
```

## Home Assistant 集成（推荐）

### 环境信息

- **HA 版本**: 2025.1.4
- **Python**: 3.12.8
- **HA 配置目录**: `~/.homeassistant`
- **虚拟环境**: `~/.homeassistant312`

### 安装步骤

#### 1. 安装 Python 3.12

从 https://www.python.org/downloads/ 下载安装 macOS 版本。

```bash
# 验证安装
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 --version
```

#### 2. 创建虚拟环境

```bash
# 创建虚拟环境
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 -m venv ~/.homeassistant312

# 激活并安装 HA
~/.homeassistant312/bin/pip install --upgrade pip
~/.homeassistant312/bin/pip install homeassistant

# 关键：安装兼容的 DNS 解析库（Python 3.12 必须）
~/.homeassistant312/bin/pip install aiodns==3.2.0 pycares==4.4.0
```

#### 3. 启动 Home Assistant

```bash
# 启动 HA
~/.homeassistant312/bin/hass --config ~/.homeassistant

# 访问 http://localhost:8123
# 首次访问需要创建账号
```

#### 4. 获取 HA API Token

1. 打开 http://localhost:8123
2. 点击左下角 **Settings**
3. 点击 **Profile**（头像）
4. 滚动到底部 **Long-Lived Access Tokens**
5. 点击 **Create Token**，输入名称，复制 Token

#### 5. 配置小米集成

**方式一：通过 UI 配置（推荐）**

1. Settings → Devices & Services → Add Integration
2. 搜索 "Xiaomi Miot Auto"
3. 输入小米账号密码登录
4. 选择要接入的家庭/设备

**方式二：通过配置文件**

```yaml
# ~/.homeassistant/secrets.yaml
xiaomi_username: "账号"
xiaomi_password: "密码"

# ~/.homeassistant/configuration.yaml
xiaomi_miot:
  username: !secret xiaomi_username
  password: !secret xiaomi_password
  cloud:
    server: cn
    country_code: 86
```

#### 6. 安装 Xiaomi Miot Auto 自定义组件

```bash
# 下载集成
cd ~/.homeassistant/custom_components
curl -L "https://github.com/al-one/hass-xiaomi-miot/archive/refs/heads/master.zip" -o xiaomi.zip
unzip -q xiaomi.zip
mv hass-xiaomi-miot-master/custom_components/xiaomi_miot .
rm -rf hass-xiaomi-miot-master xiaomi.zip
```

#### 7. 重启 HA

```bash
pkill -f "hass"
sleep 3
~/.homeassistant312/bin/hass --config ~/.homeassistant
```

### 常见问题

**Q: 启动报错 "Channel.getaddrinfo() takes 3 positional arguments"**

A: aiodns 版本冲突。执行：
```bash
~/.homeassistant312/bin/pip install aiodns==3.2.0 pycares==4.4.0
```

**Q: 小米账号登录失败**

A: 
1. 确认账号密码正确
2. 如开启两步验证，需使用**应用专用密码**
3. 访问 https://account.xiaomi.com/pass/service_config 生成

**Q: HA 启动成功但 Web 无法访问**

A: 等待 60 秒让 HA 完成初始化。检查日志：
```bash
tail -f /tmp/ha.log
```

### API 调用示例

```bash
# HA API Token
HA_TOKEN="your_token_here"

# 获取所有实体
curl -s -X GET "http://localhost:8123/api/states" \
  -H "Authorization: Bearer $HA_TOKEN"

# 获取特定设备状态
curl -s -X GET "http://localhost:8123/api/states/sensor.xxx" \
  -H "Authorization: Bearer $HA_TOKEN"
```

## 设备属性映射

### 青萍空气检测仪 Lite (cgllc.airm.cgd1st)

| 属性 | SIID | PIID | 说明 |
|------|------|------|------|
| 温度 | 3 | 7 | °C |
| 湿度 | 3 | 1 | % |
| PM2.5 | 3 | 4 | μg/m³ |
| PM10 | 3 | 5 | μg/m³ |
| CO2 | 3 | 8 | ppm |

### 常用设备 ID

- **北京之家 home_id**: 841001001988
- **青萍空气检测仪 did**: 584207351
- **小爱音箱 did**: 89419821
- **床头灯 did**: 2051165525
- **吸顶灯 did**: 2112743502

## 定时轮询方案（轻量替代）

如果不使用 HA，可以用定时轮询：

```python
# cron job 或定时任务
*/5 * * * * python3 /path/to/check_devices.py
```

check_devices.py 实现：
1. 获取设备列表
2. 对比上次状态
3. 有变化则推送微信通知

## 路径速查

| 项目 | 路径 |
|------|------|
| Skill 根目录 | `/Applications/QClaw/app/Contents/Resources/openclaw/config/skills/xiaomi-home-agent` |
| HA 配置 | `~/.homeassistant` |
| HA 虚拟环境 | `~/.homeassistant312` |
| HA 日志 | `/tmp/ha.log` |
| Token 文件 | `~/.homeassistant/.storage/auth` |

## 维护命令

```bash
# 检查 HA 状态
curl -s -o /dev/null -w "%{http_code}" http://localhost:8123

# 重启 HA
pkill -f "hass" && sleep 3 && ~/.homeassistant312/bin/hass --config ~/.homeassistant

# 升级 HA
~/.homeassistant312/bin/pip install --upgrade homeassistant

# 检查日志
tail -50 /tmp/ha.log
```

## 相关文档

- 米家 API: https://github.com/openhab/openhab-jsapi
- Xiaomi Miot Auto: https://github.com/al-one/hass-xiaomi-miot
- Home Assistant: https://www.home-assistant.io
