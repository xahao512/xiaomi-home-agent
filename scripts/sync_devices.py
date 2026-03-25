#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 设备与场景同步
从云端同步设备列表和场景列表
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


def save_devices(devices):
    """保存设备列表"""
    devices_file = os.path.join(CONFIG_DIR, 'devices_cache.json')
    with open(devices_file, 'w', encoding='utf-8') as f:
        json.dump(devices, f, indent=2, ensure_ascii=False)


def save_scenes(scenes):
    """保存场景列表"""
    scenes_file = os.path.join(CONFIG_DIR, 'scenes_cache.json')
    with open(scenes_file, 'w', encoding='utf-8') as f:
        json.dump(scenes, f, indent=2, ensure_ascii=False)


def sync_devices(auth):
    """同步设备列表"""
    import requests
    
    access_token = auth.get('access_token')
    if not access_token:
        print("❌ 未登录")
        return False
    
    region = auth.get('region', 'cn')
    base_url = f"https://api.io.mi.com/app"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print("☁️  正在同步设备列表...")
    
    try:
        response = requests.post(
            f"{base_url}/home/home_list",
            headers=headers,
            json={},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                devices = data.get('result', {}).get('list', [])
                save_devices(devices)
                print(f"✅ 已同步 {len(devices)} 个设备")
                return True
            else:
                print(f"❌ 同步失败: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 同步失败: {e}")
    
    return False


def sync_scenes(auth):
    """同步场景列表"""
    import requests
    
    access_token = auth.get('access_token')
    if not access_token:
        print("❌ 未登录")
        return False
    
    region = auth.get('region', 'cn')
    base_url = f"https://api.io.mi.com/app"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print("☁️  正在同步场景列表...")
    
    try:
        response = requests.post(
            f"{base_url}/scene/list",
            headers=headers,
            json={},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                scenes = data.get('result', {}).get('infos', [])
                save_scenes(scenes)
                print(f"✅ 已同步 {len(scenes)} 个场景")
                return True
            else:
                print(f"❌ 同步失败: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 同步失败: {e}")
    
    return False


def sync_all():
    """同步所有数据"""
    auth = load_auth()
    
    if not auth or not auth.get('access_token'):
        print("❌ 请先登录:")
        print(f"   python3 {SKILL_ROOT}/scripts/auth.py --login")
        return
    
    print("🔄 Xiaomi Home Agent - 数据同步\n")
    print("=" * 50)
    
    devices_ok = sync_devices(auth)
    scenes_ok = sync_scenes(auth)
    
    print("=" * 50)
    
    if devices_ok and scenes_ok:
        print("\n✅ 全部同步完成！")
        print("\n下一步:")
        print(f"   python3 {SKILL_ROOT}/scripts/list_devices.py  # 查看设备")
        print(f"   python3 {SKILL_ROOT}/scripts/trigger_scene.py --list  # 查看场景")
    else:
        print("\n⚠️  部分同步失败，请检查网络和登录状态")


def main():
    parser = argparse.ArgumentParser(description='同步米家数据')
    parser.add_argument('--devices', action='store_true', help='仅同步设备')
    parser.add_argument('--scenes', action='store_true', help='仅同步场景')
    parser.add_argument('--all', action='store_true', help='同步所有')
    args = parser.parse_args()
    
    if args.devices:
        auth = load_auth()
        sync_devices(auth)
    elif args.scenes:
        auth = load_auth()
        sync_scenes(auth)
    else:
        sync_all()


if __name__ == '__main__':
    main()
