#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 自动化场景2
当主卧吸顶灯打开时，自动关闭卧室床头灯
"""

import sys
import os
import time

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 设备ID配置
DEVICES = {
    'ceiling_light': '2112743502',    # 主卧吸顶灯
    'bedside_light': '2051165525',    # 卧室床头灯
}

def auto_scene_ceiling_on():
    """
    场景：主卧吸顶灯打开时，自动关闭卧室床头灯
    """
    try:
        from mijiaAPI import mijiaAPI
        
        api = mijiaAPI()
        
        print("🎬 执行自动化场景：主卧吸顶灯联动")
        print("=" * 50)
        print()
        
        # 1. 打开吸顶灯
        print("💡 步骤 1: 打开主卧吸顶灯...")
        try:
            # 方式1: run_action
            data = {'did': DEVICES['ceiling_light'], 'siid': 2, 'aiid': 1}
            result = api.run_action(data)
            if result.get('code') != 0:
                raise Exception("run_action 失败")
        except:
            # 方式2: set_devices_prop
            data = [{'did': DEVICES['ceiling_light'], 'siid': 2, 'piid': 1, 'value': True}]
            api.set_devices_prop(data)
        print("   ✅ 主卧吸顶灯已开启")
        print()
        
        # 2. 等待一下确保命令执行
        time.sleep(1)
        
        # 3. 关闭床头灯
        print("💡 步骤 2: 关闭卧室床头灯...")
        try:
            data = {'did': DEVICES['bedside_light'], 'siid': 2, 'aiid': 2}
            result = api.run_action(data)
            if result.get('code') != 0:
                raise Exception("run_action 失败")
        except:
            data = [{'did': DEVICES['bedside_light'], 'siid': 2, 'piid': 1, 'value': False}]
            api.set_devices_prop(data)
        print("   ✅ 卧室床头灯已关闭")
        print()
        
        print("=" * 50)
        print("✅ 自动化场景执行完成！")
        print()
        print("场景说明：")
        print("  • 主卧吸顶灯：已开启 💡")
        print("  • 卧室床头灯：已关闭 🌙")
        
        return True
        
    except Exception as e:
        print(f"❌ 场景执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    auto_scene_ceiling_on()

if __name__ == '__main__':
    main()
