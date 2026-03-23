#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 设备列表查询
获取并展示所有已绑定的米家设备
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
    """加载缓存的设备列表"""
    devices_file = os.path.join(CONFIG_DIR, 'devices_cache.json')
    if os.path.exists(devices_file):
        with open(devices_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_devices(devices):
    """保存设备列表缓存"""
    devices_file = os.path.join(CONFIG_DIR, 'devices_cache.json')
    with open(devices_file, 'w', encoding='utf-8') as f:
        json.dump(devices, f, indent=2, ensure_ascii=False)


def fetch_devices_from_cloud(auth):
    """从云端获取设备列表"""
    import requests
    
    access_token = auth.get('access_token')
    if not access_token:
        print("❌ 未登录或 Token 无效")
        return None
    
    region = auth.get('region', 'cn')
    base_url = f"https://api.io.mi.com/app"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # 调用小米云API获取设备列表
        response = requests.post(
            f"{base_url}/home/home_list",
            headers=headers,
            json={},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                return data.get('result', {}).get('list', [])
            else:
                print(f"❌ API 返回错误: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 获取设备列表失败: {e}")
    
    return None


def list_devices(remote=False):
    """列出所有设备"""
    auth = load_auth()
    
    if not remote:
        # 从缓存加载
        devices = load_devices()
        if devices:
            display_devices(devices)
            return True
    
    if not auth or not auth.get('access_token'):
        print("❌ 未登录，请先运行 auth.py --login")
        print("\n📋 您的设备列表为空（离线模式）")
        print("   运行以下命令登录后获取完整设备列表:")
        print(f"   python3 {SKILL_ROOT}/scripts/auth.py --login")
        return False
    
    print("☁️  正在从云端获取设备列表...")
    devices = fetch_devices_from_cloud(auth)
    
    if devices:
        save_devices(devices)
        display_devices(devices)
        return True
    else:
        # 尝试使用缓存
        devices = load_devices()
        if devices:
            print("⚠️  云端获取失败，显示缓存的设备列表:")
            display_devices(devices)
            return True
        
        print("❌ 无法获取设备列表")
        return False


def display_devices(devices):
    """格式化展示设备列表"""
    if not devices:
        print("📭 暂无可用设备")
        return
    
    print(f"\n🏠 米家设备列表 (共 {len(devices)} 个设备)\n")
    print("=" * 80)
    
    # 按房间分组
    rooms = {}
    for device in devices:
        room_name = device.get('room_name', '未分组')
        if room_name not in rooms:
            rooms[room_name] = []
        rooms[room_name].append(device)
    
    for room_name, room_devices in rooms.items():
        print(f"\n📍 {room_name}")
        print("-" * 40)
        
        for device in room_devices:
            did = device.get('did', 'N/A')
            name = device.get('name', '未知设备')
            model = device.get('model', 'N/A')
            online = device.get('online', False)
            status = "🟢 在线" if online else "🔴 离线"
            
            # 获取设备类型
            device_type = get_device_type(model)
            
            print(f"  {status} {name}")
            print(f"         ID: {did}")
            print(f"         类型: {device_type}")
    
    print("\n" + "=" * 80)
    print("\n💡 使用示例:")
    print(f"   python3 {SKILL_ROOT}/scripts/get_device_status.py --did <设备ID>")
    print(f"   python3 {SKILL_ROOT}/scripts/control_device.py --did <设备ID> --action turn_on")


def get_device_type(model):
    """根据设备模型识别设备类型"""
    if not model:
        return "未知设备"
    
    model_lower = model.lower()
    
    type_mapping = {
        'light': '💡 灯具',
        'lamp': '💡 灯具',
        'bulb': '💡 灯泡',
        'strip': '💡 灯带',
        'switch': '🔌 开关',
        'outlet': '🔌 插座',
        'plug': '🔌 插头',
        'sensor': '📊 传感器',
        'thermostat': '🌡️ 温控',
        'aircondition': '❄️ 空调',
        'ac': '❄️ 空调',
        'humidifier': '💨 加湿器',
        'fan': '🌀 风扇',
        'purifier': '🌿 空气净化器',
        'vacuum': '🤖 扫地机器人',
        'lock': '🔒 智能门锁',
        'camera': '📷 摄像头',
        'doorbell': '🔔 门铃',
        'curtain': '🪟 窗帘电机',
        'curtains': '🪟 窗帘电机',
        'speaker': '🔊 音箱',
        'tv': '📺 电视',
        'remote': '🎮 遥控器',
        'washer': '🧺 洗衣机',
        'fridge': '🧊 冰箱',
        'cooker': '🍳 电饭煲',
        'oven': '🍗 烤箱',
        'microwave': '📦 微波炉',
        'water': '💧 水壶',
        'kettle': '💧 电热水壶',
    }
    
    for key, device_type in type_mapping.items():
        if key in model_lower:
            return device_type
    
    return "📱 其他设备"


def main():
    parser = argparse.ArgumentParser(description='查看米家设备列表')
    parser.add_argument('--refresh', action='store_true', help='强制从云端刷新')
    parser.add_argument('--room', type=str, help='按房间筛选')
    args = parser.parse_args()
    
    if args.refresh:
        auth = load_auth()
        if not auth or not auth.get('access_token'):
            print("❌ 需要先登录才能刷新设备列表")
            sys.exit(1)
        devices = fetch_devices_from_cloud(auth)
        if devices:
            save_devices(devices)
            print(f"✅ 已刷新设备列表，共 {len(devices)} 个设备")
    
    list_devices(remote=args.refresh)


if __name__ == '__main__':
    main()
