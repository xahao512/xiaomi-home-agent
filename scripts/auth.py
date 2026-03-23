#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - OAuth2.0 认证管理
基于 ha_xiaomi_home 架构，支持米家账号 OAuth2.0 登录
"""

import sys
import os
import json
import argparse
import qrcode
from io import BytesIO
from PIL import Image

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(SKILL_ROOT, 'config')
AUTH_FILE = os.path.join(CONFIG_DIR, 'auth.json')

# 小米 OAuth2.0 配置
XIAOMI_OAUTH_URL = "https://account.xiaomi.com/oauth2/authorize"
XIAOMI_TOKEN_URL = "https://account.xiaomi.com/oauth2/token"
XIAOMI_API_BASE = "https://api.io.mi.com/app"


class XiaomiAuth:
    """小米 OAuth2.0 认证管理器"""
    
    def __init__(self, config_file=AUTH_FILE):
        self.auth_file = config_file
        self.config = self._load_config()
        
    def _load_config(self):
        """加载配置文件"""
        config_path = os.path.join(CONFIG_DIR, 'config.yaml')
        if os.path.exists(config_path):
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {'xiaomi': {'region': 'cn'}}
    
    def _load_auth(self):
        """加载认证信息"""
        if os.path.exists(self.auth_file):
            with open(self.auth_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _save_auth(self, auth_data):
        """保存认证信息"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(self.auth_file, 'w', encoding='utf-8') as f:
            json.dump(auth_data, f, indent=2, ensure_ascii=False)
    
    def generate_qr_url(self):
        """生成 OAuth2.0 二维码 URL"""
        import secrets
        self.state = secrets.token_urlsafe(16)
        
        region = self.config.get('xiaomi', {}).get('region', 'cn')
        callback_url = f"https://{region}.io.mi.com/static/res/chrome-extension/{self.state}"
        
        params = {
            'client_id': 'xiaomi-home',
            'redirect_uri': callback_url,
            'response_type': 'code',
            'scope': 'profile',
            'state': self.state
        }
        
        import urllib.parse
        query = urllib.parse.urlencode(params)
        return f"{XIAOMI_OAUTH_URL}?{query}", callback_url, self.state
    
    def generate_qr_image(self):
        """生成二维码图片"""
        url, callback, state = self.generate_qr_url()
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 保存图片
        qr_file = os.path.join(CONFIG_DIR, 'qr_code.png')
        img.save(qr_file)
        
        return qr_file, url
    
    def login_interactive(self):
        """交互式登录"""
        print("🔐 Xiaomi Home Agent - 登录米家账号\n")
        
        # 检查是否已登录
        auth = self._load_auth()
        if auth and auth.get('access_token'):
            print("✅ 已登录账号:", auth.get('username', 'Unknown'))
            print("   Token 有效期至:", auth.get('expires_at', 'Unknown'))
            return True
        
        # 生成二维码
        print("📱 正在生成登录二维码...\n")
        try:
            qr_file, auth_url = self.generate_qr_image()
            print(f"二维码已保存到: {qr_file}")
            print(f"\n🔗 授权链接:\n{auth_url}")
            print("\n请使用米家 APP 扫描上方二维码完成授权")
            print("\n提示：也可以访问以下链接获取二维码:")
            print(f"{auth_url}")
            
            # 显示ASCII二维码
            print("\n或者访问:")
            print(f"https://account.xiaomi.com/pass/qr/login?sid=mijia&_qrsize=240")
            
        except Exception as e:
            print(f"❌ 生成二维码失败: {e}")
            print("\n请手动访问以下链接完成授权:")
            print(f"https://account.xiaomi.com/pass/qr/login?sid=mijia&_qrsize=240")
        
        return False
    
    def check_status(self):
        """检查登录状态"""
        auth = self._load_auth()
        if not auth:
            print("❌ 未登录，请先运行 --login")
            return False
        
        import time
        if auth.get('expires_at'):
            expires_at = auth.get('expires_at')
            remaining = expires_at - time.time()
            if remaining > 0:
                hours = remaining // 3600
                print(f"✅ 已登录: {auth.get('username', 'Unknown')}")
                print(f"   Token 剩余有效期: {hours:.1f} 小时")
                return True
            else:
                print("⚠️  Token 已过期，请重新登录")
                return False
        
        print(f"✅ 已登录: {auth.get('username', 'Unknown')}")
        return True
    
    def logout(self):
        """登出"""
        if os.path.exists(self.auth_file):
            os.remove(self.auth_file)
            print("✅ 已清除登录信息")
        else:
            print("ℹ️  没有登录信息需要清除")


def main():
    parser = argparse.ArgumentParser(description='Xiaomi Home 认证管理')
    parser.add_argument('--login', action='store_true', help='登录米家账号')
    parser.add_argument('--status', action='store_true', help='检查登录状态')
    parser.add_argument('--logout', action='store_true', help='清除登录信息')
    args = parser.parse_args()
    
    auth = XiaomiAuth()
    
    if args.logout:
        auth.logout()
    elif args.status:
        auth.check_status()
    elif args.login:
        auth.login_interactive()
    else:
        auth.check_status()


if __name__ == '__main__':
    main()
