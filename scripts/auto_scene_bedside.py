#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 自动化场景
当床头灯打开时，自动关闭吸顶灯
"""

import sys
import os
import time
import argparse

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 设备ID配置
DEVICES = {
    'bedside_light': '2051165525',    # 床头灯
    'ceiling_light': '2112743502',    # 吸顶灯
}

def auto_scene_bedside_on():
    """
    场景：床头灯打开时，自动关闭吸顶灯
    """
    try:
        from mijiaAPI import mijiaAPI
        
        api = mijiaAPI()
        
        print("🎬 执行自动化场景：床头灯联动")
        print("=" * 50)
        print()
        
        # 1. 打开床头灯
        print("💡 步骤 1: 打开床头灯...")
        bedside_data = {
            'did': DEVICES['bedside_light'],
            'siid': 2,
            'aiid': 1,  # 开启动作
        }
        result = api.run_action(bedside_data)
        print("   ✅ 床头灯已开启")
        print()
        
        # 2. 等待一下确保命令执行
        time.sleep(1)
        
        # 3. 关闭吸顶灯
        print("💡 步骤 2: 关闭吸顶灯...")
        ceiling_data = {
            'did': DEVICES['ceiling_light'],
            'siid': 2,
            'aiid': 2,  # 关闭动作
        }
        result = api.run_action(ceiling_data)
        print("   ✅ 吸顶灯已关闭")
        print()
        
        print("=" * 50)
        print("✅ 自动化场景执行完成！")
        print()
        print("场景说明：")
        print("  • 床头灯：已开启 💡")
        print("  • 吸顶灯：已关闭 🌙")
        
        return True
        
    except Exception as e:
        print(f"❌ 场景执行失败: {e}")
        return False

def check_devices_status():
    """检查设备当前状态"""
    try:
        from mijiaAPI import mijiaAPI
        
        api = mijiaAPI()
        devices = api.get_devices_list()
        
        print("📊 当前设备状态：")
        print("-" * 40)
        
        for device_name, did in DEVICES.items():
            for device in devices:
                if device.get('did') == did:
                    name = device.get('name', 'Unknown')
                    online = device.get('isOnline', False)
                    status = '🟢 在线' if online else '🔴 离线'
                    print(f"  {name}: {status}")
                    break
        
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ 获取状态失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='自动化场景')
    parser.add_argument('--run', action='store_true', help='执行场景')
    parser.add_argument('--status', action='store_true', help='查看设备状态')
    args = parser.parse_args()
    
    if args.status:
        check_devices_status()
    elif args.run:
        auto_scene_bedside_on()
    else:
        print("🎬 床头灯联动场景")
        print()
        print("场景描述：当床头灯打开时，自动关闭吸顶灯")
        print()
        print("使用方法：")
        print("  python3 scripts/auto_scene_bedside.py --run    # 执行场景")
        print("  python3 scripts/auto_scene_bedside.py --status # 查看状态")

if __name__ == '__main__':
    main()
