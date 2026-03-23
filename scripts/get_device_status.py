#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 设备状态查询
获取指定设备的实时状态
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


def get_device_status(did, refresh=False):
    """获取设备状态"""
    auth = load_auth()
    device = find_device(did)
    
    if not device:
        print(f"❌ 未找到设备: {did}")
        return None
    
    device_name = device.get('name', did)
    print(f"🔍 获取设备状态: {device_name}")
    
    if refresh or not auth or not auth.get('access_token'):
        # 显示本地缓存的状态
        return display_device_status(device)
    
    # 从云端获取实时状态
    status = fetch_status_from_cloud(auth, did)
    
    if status:
        # 合并云端状态和本地信息
        device['status'] = status
        display_device_status(device)
        return status
    else:
        # 回退到本地缓存
        print("⚠️  无法获取云端状态，显示缓存信息")
        display_device_status(device)
        return device.get('status')


def fetch_status_from_cloud(auth, did):
    """从云端获取设备状态"""
    import requests
    
    access_token = auth.get('access_token')
    if not access_token:
        return None
    
    region = auth.get('region', 'cn')
    base_url = f"https://api.io.mi.com/app"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{base_url}/device/info/{did}",
            headers=headers,
            json={},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                return data.get('result', {})
        
    except Exception as e:
        print(f"⚠️  云端查询失败: {e}")
    
    return None


def display_device_status(device):
    """格式化展示设备状态"""
    did = device.get('did', 'N/A')
    name = device.get('name', '未知设备')
    model = device.get('model', 'N/A')
    online = device.get('online', False)
    status = device.get('status', {})
    
    print(f"\n{'='*60}")
    print(f"📱 设备状态详情")
    print(f"{'='*60}")
    print(f"名称: {name}")
    print(f"ID: {did}")
    print(f"型号: {model}")
    print(f"在线状态: {'🟢 在线' if online else '🔴 离线'}")
    
    # 显示属性
    if status:
        print(f"\n📊 当前属性:")
        for key, value in status.items():
            # 美化属性名称
            display_key = {
                'power': '电源',
                'brightness': '亮度',
                'temperature': '温度',
                'humidity': '湿度',
                'mode': '模式',
                'speed': '风速',
                'power_consumption': '功耗',
            }.get(key, key)
            
            # 美化属性值
            if key == 'power':
                display_value = '开启' if value else '关闭'
            elif key == 'brightness':
                display_value = f'{value}%'
            elif key == 'temperature':
                display_value = f'{value}°C'
            elif key == 'humidity':
                display_value = f'{value}%'
            elif key == 'mode':
                display_value = ['自动', '制冷', '制热', '送风', '除湿'][value] if isinstance(value, int) else value
            else:
                display_value = value
            
            print(f"  {display_key}: {display_value}")
    else:
        print("\n📊 暂无属性数据")
    
    print(f"{'='*60}\n")
    
    return status


def main():
    parser = argparse.ArgumentParser(description='获取米家设备状态')
    parser.add_argument('--did', type=str, required=True, help='设备ID')
    parser.add_argument('--refresh', action='store_true', help='强制从云端刷新')
    args = parser.parse_args()
    
    get_device_status(args.did, refresh=args.refresh)


if __name__ == '__main__':
    main()
