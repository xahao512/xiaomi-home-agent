#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 设备状态查询
"""

import sys
import os
import argparse

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_device_status(did):
    """获取设备状态"""
    try:
        from mijiaAPI import mijiaAPI
        
        api = mijiaAPI()
        
        # 从设备列表中查找
        devices = api.get_devices_list()
        device = None
        for d in devices:
            if d.get('did') == did:
                device = d
                break
        
        if not device:
            print(f"❌ 未找到设备: {did}")
            return
        
        name = device.get('name', '未知设备')
        model = device.get('model', 'N/A')
        online = device.get('isOnline', False)
        
        print(f"📱 设备状态: {name}")
        print(f"   型号: {model}")
        print(f"   状态: {'🟢 在线' if online else '🔴 离线'}")
        print(f"   IP: {device.get('localip', 'N/A')}")
        print(f"   WiFi: {device.get('ssid', 'N/A')}")
        print(f"   信号: {device.get('rssi', 'N/A')} dBm")
        print(f"   MAC: {device.get('mac', 'N/A')}")
        
        # 如果是传感器类设备，尝试获取数据
        if 'air' in model.lower() or 'sensor' in model.lower():
            print()
            print("🌡️  尝试获取传感器数据...")
            try:
                # 构造属性查询
                params = []
                for piid in range(1, 10):
                    params.append({
                        'did': did,
                        'siid': 2,
                        'piid': piid,
                    })
                
                result = api.get_devices_prop(params)
                
                if result:
                    print("   传感器数据:")
                    for item in result:
                        if item.get('code') == 0:
                            piid = item.get('piid')
                            value = item.get('value')
                            print(f"     - 属性 {piid}: {value}")
                else:
                    print("   ⚠️  无法获取实时数据")
                    print("   💡 请使用米家 APP 查看详细数据")
                    
            except Exception as e:
                print(f"   ⚠️  获取传感器数据失败: {e}")
        
    except ImportError:
        print("❌ 未安装 mijiaAPI")
    except Exception as e:
        print(f"❌ 查询失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='获取设备状态')
    parser.add_argument('--did', type=str, required=True, help='设备ID')
    args = parser.parse_args()
    
    get_device_status(args.did)

if __name__ == '__main__':
    main()
