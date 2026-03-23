#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 设备控制
支持开关、亮度、温度等多种控制命令
"""

import sys
import os
import json
import argparse

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(SKILL_ROOT, 'config')
AUTH_FILE = os.path.join(CONFIG_DIR, 'auth.json')


def load_auth():
    """加载认证信息"""
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def load_devices():
    """加载设备缓存"""
    devices_file = os.path.join(CONFIG_DIR, 'devices_cache.json')
    if os.path.exists(devices_file):
        with open(devices_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def find_device(did):
    """根据设备ID查找设备"""
    devices = load_devices()
    for device in devices:
        if device.get('did') == did:
            return device
    return None


def control_device(did, action, value=None, param=None):
    """
    控制设备
    
    Args:
        did: 设备ID
        action: 控制动作
        value: 控制值（如亮度百分比、温度值）
        param: 额外参数
    """
    auth = load_auth()
    
    if not auth or not auth.get('access_token'):
        print("❌ 未登录，请先运行 auth.py --login")
        return False
    
    device = find_device(did)
    device_name = device.get('name', did) if device else did
    
    # 构建控制命令
    command = build_command(action, value, param)
    
    if not command:
        print(f"❌ 不支持的动作: {action}")
        print("\n支持的动作为:")
        print("  turn_on, turn_off - 开关")
        print("  set_brightness - 设置亮度 (0-100)")
        print("  set_temperature - 设置温度")
        print("  set_mode - 设置模式")
        print("  custom - 自定义命令")
        return False
    
    print(f"🎛️  控制设备: {device_name}")
    print(f"   动作: {action}")
    if value is not None:
        print(f"   值: {value}")
    
    # 发送到云端
    success = send_command_to_cloud(auth, did, command)
    
    if success:
        print(f"✅ 命令已发送: {device_name} -> {action}")
        return True
    else:
        print(f"❌ 命令发送失败")
        return False


def build_command(action, value, param):
    """根据动作构建MIoT命令"""
    commands = {
        'turn_on': {
            'siid': 2,
            'piid': 1,
            'value': True
        },
        'turn_off': {
            'siid': 2,
            'piid': 1,
            'value': False
        },
        'set_brightness': {
            'siid': 2,
            'piid': 2,
            'value': int(value) if value else 100
        },
        'set_temperature': {
            'siid': 2,
            'piid': 3,
            'value': int(value) if value else 26
        },
        'set_mode': {
            'siid': 2,
            'piid': 4,
            'value': int(value) if value else 0
        }
    }
    
    if action in commands:
        return commands[action]
    
    if action == 'custom' and param:
        try:
            return json.loads(param)
        except:
            print("❌ 自定义命令格式错误，请使用JSON格式")
            return None
    
    return None


def send_command_to_cloud(auth, did, command):
    """发送控制命令到云端"""
    import requests
    
    access_token = auth.get('access_token')
    region = auth.get('region', 'cn')
    base_url = f"https://api.io.mi.com/app"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # 构建请求
    payload = {
        'did': did,
        'siid': command.get('siid'),
        'piid': command.get('piid'),
        'value': command.get('value')
    }
    
    try:
        response = requests.post(
            f"{base_url}/device/trigger/{did}",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('code') == 0
        
    except Exception as e:
        print(f"⚠️  云端控制失败: {e}")
    
    return False


def send_command_local(did, command, gateway_ip='auto'):
    """本地局域网控制（需要中枢网关）"""
    import socket
    
    if gateway_ip == 'auto':
        # 自动发现网关
        gateway_ip = discover_gateway()
        if not gateway_ip:
            print("❌ 未发现本地中枢网关，请检查网络配置")
            return False
    
    # 发送到本地网关
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        msg = json.dumps({
            'did': did,
            'command': command
        }).encode()
        
        sock.sendto(msg, (gateway_ip, 8053))
        sock.close()
        
        print(f"✅ 本地命令已发送")
        return True
        
    except Exception as e:
        print(f"❌ 本地控制失败: {e}")
        return False


def discover_gateway():
    """发现本地中枢网关"""
    # 简化实现，实际应该使用 mDNS/UDP 广播
    devices = load_devices()
    for device in devices:
        model = device.get('model', '').lower()
        if 'hub' in model or 'gateway' in model:
            local_ip = device.get('local_ip')
            if local_ip:
                return local_ip
    return None


# 常用设备快捷命令映射
QUICK_ACTIONS = {
    # 灯具
    '开灯': ('turn_on', None),
    '关灯': ('turn_off', None),
    '亮一点': ('set_brightness', 80),
    '暗一点': ('set_brightness', 30),
    '最亮': ('set_brightness', 100),
    '最暗': ('set_brightness', 10),
    
    # 空调
    '开空调': ('turn_on', None),
    '关空调': ('turn_off', None),
    '制冷': ('set_mode', 1),
    '制热': ('set_mode', 2),
    '26度': ('set_temperature', 26),
    '24度': ('set_temperature', 24),
    '28度': ('set_temperature', 28),
    
    # 通用
    '打开': ('turn_on', None),
    '关闭': ('turn_off', None),
}


def main():
    parser = argparse.ArgumentParser(description='控制米家设备')
    parser.add_argument('--did', type=str, required=True, help='设备ID')
    parser.add_argument('--action', type=str, required=True, 
                       choices=['turn_on', 'turn_off', 'set_brightness', 
                               'set_temperature', 'set_mode', 'custom'],
                       help='控制动作')
    parser.add_argument('--value', type=str, help='控制值')
    parser.add_argument('--param', type=str, help='自定义参数(JSON格式)')
    parser.add_argument('--local', action='store_true', help='使用本地控制模式')
    args = parser.parse_args()
    
    # 转换值为合适类型
    value = None
    if args.value:
        try:
            if args.action in ['set_brightness']:
                value = int(args.value)
            elif args.action in ['set_temperature', 'set_mode']:
                value = int(args.value)
            else:
                value = args.value
        except ValueError:
            value = args.value
    
    if args.local:
        # 本地控制
        device = find_device(args.did)
        device_name = device.get('name', args.did) if device else args.did
        command = build_command(args.action, value, args.param)
        send_command_local(args.did, command)
    else:
        # 云端控制
        control_device(args.did, args.action, value, args.param)


if __name__ == '__main__':
    main()
