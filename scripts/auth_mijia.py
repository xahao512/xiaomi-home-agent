#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 使用 mijiaAPI 登录
这是最简单可靠的登录方式
"""

import sys
import os
import json
import subprocess

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(SKILL_ROOT, 'config')
AUTH_FILE = os.path.join(CONFIG_DIR, 'auth.json')

def login_with_mijia_api():
    """使用 mijiaAPI 登录"""
    print("🔐 Xiaomi Home Agent - 登录\n")
    print("="*60)
    print("使用 mijiaAPI 进行登录（最可靠的方式）")
    print("="*60)
    
    # 检查 mijiaAPI 是否安装
    result = subprocess.run(['pip3', 'show', 'mijiaAPI'], capture_output=True, text=True)
    if 'Name: mijiaAPI' not in result.stdout:
        print("\n📦 正在安装 mijiaAPI...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'mijiaAPI'], check=True)
        print("✅ mijiaAPI 安装完成")
    
    print("\n📱 登录方式:")
    print("\n方式 1: 二维码登录（推荐）")
    print("  请运行: mijiaAPI -l")
    print("  然后使用米家 APP 扫描终端显示的二维码")
    
    print("\n方式 2: 自动登录（如果已登录过）")
    print("  mijiaAPI 会自动使用已保存的凭证")
    
    print("\n方式 3: 手动输入 Token")
    print("  如果你已有小米 Token，可以直接输入")
    
    print("\n" + "="*60)
    print("\n由于 mijiaAPI 需要交互式终端，请手动执行:")
    print(f"\n  cd {SKILL_ROOT}")
    print("  mijiaAPI -l")
    print("\n登录成功后，Token 会自动保存，然后可以运行:")
    print("  python3 scripts/list_devices.py")
    print("="*60)

def check_mijia_api_status():
    """检查 mijiaAPI 登录状态"""
    try:
        # 尝试导入 mijiaAPI
        from mijiaAPI import mijiaAPI
        
        # 尝试创建 API 实例（会自动加载已保存的凭证）
        api = mijiaAPI()
        
        # 尝试获取设备列表验证登录状态
        devices = api.get_devices()
        
        if devices:
            print(f"✅ 已登录 mijiaAPI")
            print(f"   设备数量: {len(devices)}")
            return True
        else:
            print("⚠️  已登录但没有设备")
            return False
            
    except Exception as e:
        print(f"❌ 未登录或登录已过期: {e}")
        return False

def main():
    print("\n🔧 Xiaomi Home Agent - 认证管理\n")
    
    # 先检查是否已登录
    if check_mijia_api_status():
        print("\n✅ 登录状态正常，可以开始使用！")
        print("\n常用命令:")
        print("  python3 scripts/list_devices.py     # 查看设备列表")
        print("  python3 scripts/control_device.py   # 控制设备")
        return
    
    # 未登录，提示用户登录
    login_with_mijia_api()

if __name__ == '__main__':
    main()
