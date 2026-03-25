#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 环境检查与安装脚本
"""

import sys
import subprocess
import os

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check_python_version():
    """检查 Python 版本"""
    if sys.version_info < (3, 8):
        print("❌ Python 版本过低，需要 3.8+")
        return False
    print(f"✅ Python 版本: {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_dependencies():
    """检查依赖包"""
    required = ['requests', 'paho.mqtt.client', 'Crypto', 'yaml', 'qrcode']
    missing = []
    
    for pkg in required:
        try:
            if pkg == 'Crypto':
                __import__('Crypto.Cipher')
            elif pkg == 'paho.mqtt.client':
                __import__('paho.mqtt.client')
            else:
                __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"⚠️  缺少依赖: {', '.join(missing)}")
        return False
    
    print("✅ 所有依赖已安装")
    return True

def install_dependencies():
    """安装依赖"""
    req_file = os.path.join(SKILL_ROOT, 'requirements.txt')
    print(f"📦 安装依赖 from {req_file}...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req_file], 
                      check=True, capture_output=False)
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {e}")
        return False

def setup_config():
    """初始化配置目录"""
    config_dir = os.path.join(SKILL_ROOT, 'config')
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, 'config.yaml')
    if not os.path.exists(config_file):
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("""# Xiaomi Home Agent 配置文件
xiaomi:
  region: cn  # cn, de, us, sg, in, ru

control_mode: cloud  # cloud, local, auto

local:
  gateway_ip: auto

mqtt:
  keepalive: 60
  reconnect_interval: 5
""")
        print(f"✅ 配置文件已创建: {config_file}")
    else:
        print(f"✅ 配置文件已存在: {config_file}")

def main():
    print("🔧 Xiaomi Home Agent - 环境检查\n")
    
    # 检查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查/安装依赖
    if not check_dependencies():
        print("\n📦 正在安装依赖...")
        if not install_dependencies():
            sys.exit(1)
    
    # 初始化配置
    print("\n⚙️  初始化配置...")
    setup_config()
    
    print("\n✨ 环境检查完成！")
    print(f"\n下一步：运行登录命令")
    print(f"  python3 {SKILL_ROOT}/scripts/auth.py --login")

if __name__ == '__main__':
    main()
