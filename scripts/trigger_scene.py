#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 场景执行
触发米家智能场景和自动化
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


def load_scenes():
    """加载缓存的场景列表"""
    scenes_file = os.path.join(CONFIG_DIR, 'scenes_cache.json')
    if os.path.exists(scenes_file):
        with open(scenes_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_scenes(scenes):
    """保存场景列表缓存"""
    scenes_file = os.path.join(CONFIG_DIR, 'scenes_cache.json')
    with open(scenes_file, 'w', encoding='utf-8') as f:
        json.dump(scenes, f, indent=2, ensure_ascii=False)


def fetch_scenes_from_cloud(auth):
    """从云端获取场景列表"""
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
            f"{base_url}/scene/list",
            headers=headers,
            json={},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                return data.get('result', {}).get('infos', [])
            
    except Exception as e:
        print(f"⚠️  获取场景列表失败: {e}")
    
    return None


def list_scenes():
    """列出所有场景"""
    auth = load_auth()
    scenes = load_scenes()
    
    if not scenes and auth and auth.get('access_token'):
        print("☁️  正在从云端获取场景列表...")
        scenes = fetch_scenes_from_cloud(auth)
        if scenes:
            save_scenes(scenes)
    
    if not scenes:
        print("📭 暂无可用场景")
        print("\n请先登录后刷新场景列表:")
        print(f"   python3 {SKILL_ROOT}/scripts/sync_devices.py --scenes")
        return
    
    print(f"\n🎬 米家场景列表 (共 {len(scenes)} 个场景)\n")
    print("=" * 70)
    
    # 分类显示
    manual_scenes = [s for s in scenes if s.get('type') == 0]
    auto_scenes = [s for s in scenes if s.get('type') == 1]
    
    if manual_scenes:
        print(f"\n📋 手动场景 ({len(manual_scenes)} 个)")
        print("-" * 40)
        for scene in manual_scenes:
            sid = scene.get('sid', 'N/A')
            name = scene.get('name', '未命名')
            print(f"  • {name}")
            print(f"    ID: {sid}")
    
    if auto_scenes:
        print(f"\n⚙️  自动场景 ({len(auto_scenes)} 个)")
        print("-" * 40)
        for scene in auto_scenes:
            sid = scene.get('sid', 'N/A')
            name = scene.get('name', '未命名')
            print(f"  • {name}")
            print(f"    ID: {sid}")
    
    print("\n" + "=" * 70)
    print("\n💡 使用示例:")
    print(f"   python3 {SKILL_ROOT}/scripts/trigger_scene.py --name '回家模式'")
    print(f"   python3 {SKILL_ROOT}/scripts/trigger_scene.py --sid <场景ID>")


def trigger_scene(name=None, sid=None):
    """执行场景"""
    auth = load_auth()
    
    if not auth or not auth.get('access_token'):
        print("❌ 未登录，请先运行 auth.py --login")
        return False
    
    # 查找场景
    scenes = load_scenes()
    if not scenes:
        scenes = fetch_scenes_from_cloud(auth)
        if scenes:
            save_scenes(scenes)
    
    target_scene = None
    
    if sid:
        for scene in scenes:
            if scene.get('sid') == sid:
                target_scene = scene
                break
    elif name:
        for scene in scenes:
            if name in scene.get('name', ''):
                target_scene = scene
                break
    
    if not target_scene:
        print(f"❌ 未找到场景: {name or sid}")
        print("\n可用场景:")
        list_scenes()
        return False
    
    scene_name = target_scene.get('name', '未命名')
    scene_sid = target_scene.get('sid')
    
    print(f"🎬 执行场景: {scene_name}")
    
    # 发送到云端执行
    success = execute_scene(auth, scene_sid)
    
    if success:
        print(f"✅ 场景执行成功: {scene_name}")
        return True
    else:
        print(f"❌ 场景执行失败: {scene_name}")
        return False


def execute_scene(auth, sid):
    """执行场景"""
    import requests
    
    access_token = auth.get('access_token')
    region = auth.get('region', 'cn')
    base_url = f"https://api.io.mi.com/app"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{base_url}/scene/execute",
            headers=headers,
            json={'sid': sid},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('code') == 0
        
    except Exception as e:
        print(f"⚠️  场景执行失败: {e}")
    
    return False


# 常用场景快捷映射
QUICK_SCENES = {
    '回家': ['回家模式', '欢迎回家', 'Home'],
    '离家': ['离家模式', '出门', 'Away'],
    '睡眠': ['睡眠模式', '晚安', 'Sleep'],
    '起床': ['起床模式', '早安', 'Morning'],
    '观影': ['观影模式', '电影模式', 'Movie'],
    '浪漫': ['浪漫模式', '烛光晚餐', 'Romantic'],
    '阅读': ['阅读模式', '看书', 'Reading'],
    '派对': ['派对模式', 'Party'],
}


def main():
    parser = argparse.ArgumentParser(description='执行米家场景')
    parser.add_argument('--list', action='store_true', help='列出所有场景')
    parser.add_argument('--name', type=str, help='场景名称（模糊匹配）')
    parser.add_argument('--sid', type=str, help='场景ID')
    args = parser.parse_args()
    
    if args.list:
        list_scenes()
    elif args.name or args.sid:
        trigger_scene(name=args.name, sid=args.sid)
    else:
        # 默认列出场景
        list_scenes()


if __name__ == '__main__':
    main()
