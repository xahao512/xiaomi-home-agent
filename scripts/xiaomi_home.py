#!/usr/bin/env python3
"""
xiaomi_home.py - 小米米家智能家居控制核心脚本

支持功能:
- 设备列表查询
- 设备状态获取
- 设备控制 (开关/亮度/温度/模式等)
- 场景执行
- 本地/云端双模式

用法:
    python3 xiaomi_home.py list
    python3 xiaomi_home.py status <did>
    python3 xiaomi_home.py control <did> <siid>.<piid>=<value>
    python3 xiaomi_home.py scene <scene_id>
    python3 xiaomi_home.py local <ip> <command>
    python3 xiaomi_home.py diag
"""

import sys
import os
import json
import argparse
import logging
from pathlib import Path

# Add skill dir to path
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SKILL_DIR))

from scripts.xiaomi_api import XiaomiAPI
from scripts.xiaomi_local import XiaomiLocal

DEFAULT_CONFIG = Path.home() / ".qclaw" / "skills" / "xiaomi-home-config.yaml"


def load_config():
    config_path = DEFAULT_CONFIG
    if not config_path.exists():
        # Try skill dir
        config_path = SKILL_DIR / "config.yaml"
    if not config_path.exists():
        print(f"[ERROR] 配置文件未找到: {DEFAULT_CONFIG}")
        print(f"请复制 {SKILL_DIR}/config.yaml 到 {DEFAULT_CONFIG}")
        sys.exit(1)
    import yaml
    with open(config_path) as f:
        return yaml.safe_load(f)


def setup_logging(config):
    log_cfg = config.get("logging", {})
    level = getattr(logging, log_cfg.get("level", "INFO"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
        ]
    )
    return logging.getLogger("xiaomi_home")


def cmd_list(api: XiaomiAPI, args):
    """查询设备列表"""
    print("[INFO] 正在查询设备列表...")
    devices = api.list_devices()
    if not devices:
        print("[WARN] 未找到任何设备，请检查 access_token 是否有效")
        return

    print(f"\n共找到 {len(devices)} 个设备:\n")
    print(f"{'名称':<20} {'类型':<15} {'在线':<6} {'DID':<15} {'型号'}")
    print("-" * 90)
    for d in devices:
        online = "🟢 在线" if d.get("online") else "⚠️ 离线"
        dtype = d.get("type", d.get("device_type", "unknown"))
        name = d.get("name", d.get("alias_name", "未知设备"))
        model = d.get("model", "-")
        did = d.get("did", "-")
        print(f"{name:<20} {dtype:<15} {online:<8} {did:<15} {model}")
    print()
    return devices


def cmd_status(api: XiaomiAPI, args):
    """获取设备状态"""
    did = args.did
    print(f"[INFO] 查询设备 {did} 状态...")
    status = api.get_device_status(did)
    if "error" in status:
        print(f"[ERROR] 获取状态失败: {status['error']}")
        return None
    print(json.dumps(status, indent=2, ensure_ascii=False))
    return status


def cmd_control(api: XiaomiAPI, args):
    """控制设备"""
    did = args.did
    props = args.properties

    # 解析 siid.piid=value 格式
    controls = []
    for prop in props:
        if "=" in prop:
            key, val = prop.split("=", 1)
            if "." in key:
                siid, piid = key.split(".", 1)
                controls.append({
                    "siid": int(siid),
                    "piid": int(piid),
                    "value": parse_value(val)
                })
            else:
                print(f"[WARN] 忽略无效属性格式: {prop}，应为 siid.piid=value")
        else:
            print(f"[WARN] 忽略无效参数: {prop}，应为 siid.piid=value")

    if not controls:
        print("[ERROR] 未提供有效的控制参数")
        return None

    print(f"[INFO] 向设备 {did} 下发 {len(controls)} 条控制指令...")
    result = api.control_device(did, controls)
    if result.get("code") == 0:
        print(f"[OK] 控制成功")
    else:
        print(f"[ERROR] 控制失败: {result}")
    return result


def cmd_scene(api: XiaomiAPI, args):
    """执行场景"""
    scene_id = args.scene_id
    print(f"[INFO] 执行场景 {scene_id}...")
    result = api.execute_scene(scene_id)
    if result.get("code") == 0:
        print(f"[OK] 场景执行成功")
    else:
        print(f"[ERROR] 场景执行失败: {result}")
    return result


def cmd_local(args):
    """本地局域网控制"""
    ip = args.ip
    command = args.command

    # 尝试从配置加载 local_key
    config = {}
    try:
        config = load_config()
    except Exception:
        pass

    local_key = config.get("local", {}).get("local_key", "")

    print(f"[INFO] 向本地设备 {ip} 发送命令...")
    local = XiaomiLocal(ip, local_key)
    result = local.send_command(command)

    if result.get("ok"):
        print(f"[OK] {result.get('result', result)}")
    else:
        print(f"[ERROR] {result}")
    return result


def cmd_discovery(api: XiaomiAPI, args):
    """发现本地设备"""
    print("[INFO] 正在发现局域网内设备...")
    from scripts.discovery import discover_devices
    devices = discover_devices(timeout=args.timeout)
    print(f"\n发现 {len(devices)} 个设备:\n")
    for d in devices:
        print(f"  IP: {d['ip']:<16} 设备ID: {d.get('deviceId','-')}  型号: {d.get('model','-')}")
    return devices


def parse_value(val: str):
    """解析控制值，自动推断类型"""
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    if val.lower() in ("on", "off"):
        return val.lower() == "on"
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        return val


def main():
    parser = argparse.ArgumentParser(
        description="小米米家智能家居控制工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 xiaomi_home.py list                                  # 列出所有设备
  python3 xiaomi_home.py status 123456789                      # 查询设备状态
  python3 xiaomi_home.py control 123456789 2.1=true            # 开灯
  python3 xiaomi_home.py control 123456789 2.2=60              # 调亮度60%
  python3 xiaomi_home.py control 123456789 2.3=3500            # 调色温3500K
  python3 xiaomi_home.py scene home                            # 执行场景
  python3 xiaomi_home.py local 192.168.1.100 '{"method":"set_power","params":["on"]}'
  python3 xiaomi_home.py discovery                             # 发现本地设备
  python3 xiaomi_home.py diag                                  # 诊断工具
        """
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # list
    p_list = sub.add_parser("list", help="查询设备列表")
    p_list.add_argument("--type", help="按类型过滤 (light/ac/plug)")

    # status
    p_status = sub.add_parser("status", help="获取设备状态")
    p_status.add_argument("did", help="设备 DID")

    # control
    p_ctrl = sub.add_parser("control", help="控制设备")
    p_ctrl.add_argument("did", help="设备 DID")
    p_ctrl.add_argument("properties", nargs="+", help="属性控制，格式: siid.piid=value")

    # scene
    p_scene = sub.add_parser("scene", help="执行场景")
    p_scene.add_argument("scene_id", help="场景 ID 或名称")

    # local
    p_local = sub.add_parser("local", help="本地局域网控制")
    p_local.add_argument("ip", help="设备 IP 地址")
    p_local.add_argument("command", help="JSON 命令")

    # discovery
    p_disc = sub.add_parser("discovery", help="发现局域网设备")
    p_disc.add_argument("--timeout", type=int, default=10, help="发现超时(秒)")

    # diag
    sub.add_parser("diag", help="诊断工具")

    args = parser.parse_args()

    # 加载配置
    config = load_config()
    logger = setup_logging(config)

    # 初始化 API
    xiaomi_cfg = config.get("xiaomi", {})
    cloud_cfg = config.get("cloud", {})

    api = XiaomiAPI(
        app_key=xiaomi_cfg.get("app_key", ""),
        app_secret=xiaomi_cfg.get("app_secret", ""),
        access_token=xiaomi_cfg.get("access_token", ""),
        user_id=xiaomi_cfg.get("user_id", ""),
        api_base=cloud_cfg.get("api_base", "https://api.io.mi.com/app"),
    )

    # 执行命令
    if args.cmd == "list":
        return cmd_list(api, args)
    elif args.cmd == "status":
        return cmd_status(api, args)
    elif args.cmd == "control":
        return cmd_control(api, args)
    elif args.cmd == "scene":
        return cmd_scene(api, args)
    elif args.cmd == "local":
        return cmd_local(args)
    elif args.cmd == "discovery":
        return cmd_discovery(api, args)
    elif args.cmd == "diag":
        from scripts.diagnostic import run_diagnostic
        return run_diagnostic(api, config)


if __name__ == "__main__":
    main()
