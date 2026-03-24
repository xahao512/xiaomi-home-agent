#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 认证管理
支持小米账号登录
"""

import sys
import os
import json
import argparse
import time
import hashlib
import requests

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(SKILL_ROOT, 'config')
AUTH_FILE = os.path.join(CONFIG_DIR, 'auth.json')


class XiaomiAuth:
    """小米认证管理器"""
    
    def __init__(self, config_file=AUTH_FILE):
        self.auth_file = config_file
        self.config = self._load_config()
        self.region = self.config.get('xiaomi', {}).get('region', 'cn')
        self.session = requests.Session()
        
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
    
    def _get_sign(self, data, key=''):
        """生成签名"""
        params = sorted(data.items())
        sign_str = '&'.join([f"{k}={v}" for k, v in params]) + key
        return hashlib.md5(sign_str.encode()).hexdigest().upper()
    
    def login_with_credentials(self, username, password):
        """使用用户名密码登录"""
        print(f"🔐 正在登录: {username}")
        
        try:
            # 第一步：获取登录页面和初始参数
            login_page_url = "https://account.xiaomi.com/pass/serviceLogin"
            params = {
                'sid': 'mijia',
                '_json': 'true',
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            }
            
            # 获取登录页面
            response = self.session.get(login_page_url, params=params, headers=headers, timeout=30)
            
            # 第二步：提交登录
            auth_url = "https://account.xiaomi.com/pass/serviceLoginAuth2"
            
            login_data = {
                'user': username,
                'password': password,
                'sid': 'mijia',
                '_json': 'true',
                'callback': 'https://api.io.mi.com/app',
            }
            
            response = self.session.post(auth_url, data=login_data, headers=headers, timeout=30)
            
            # 解析响应
            result = response.text
            if result.startswith('&&&START&&&'):
                result = result[11:]
            
            login_result = json.loads(result)
            
            if login_result.get('code') == 0:
                # 登录成功
                auth_info = {
                    'username': username,
                    'user_id': login_result.get('userId'),
                    'pass_token': login_result.get('passToken'),
                    'ssecurity': login_result.get('ssecurity'),
                    'location': login_result.get('location'),
                    'login_time': time.time(),
                    'region': self.region,
                }
                
                # 获取 serviceToken
                if login_result.get('location'):
                    service_token = self._get_service_token(login_result['location'])
                    if service_token:
                        auth_info['service_token'] = service_token
                
                self._save_auth(auth_info)
                print(f"✅ 登录成功: {username}")
                return True
            else:
                desc = login_result.get('desc', login_result.get('description', 'Unknown error'))
                print(f"❌ 登录失败: {desc}")
                print(f"   错误码: {login_result.get('code')}")
                return False
                
        except Exception as e:
            print(f"❌ 登录出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_service_token(self, location):
        """获取 serviceToken"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            }
            response = self.session.get(location, headers=headers, allow_redirects=False, timeout=30)
            
            # 从响应中提取 serviceToken
            if 'serviceToken' in response.text:
                import re
                match = re.search(r'serviceToken=([^&]+)', response.text)
                if match:
                    return match.group(1)
            
            # 从 cookies 中获取
            for cookie in self.session.cookies:
                if cookie.name == 'serviceToken':
                    return cookie.value
                    
        except Exception as e:
            print(f"⚠️  获取 serviceToken 失败: {e}")
        
        return None
    
    def generate_qr_login(self):
        """生成二维码登录"""
        import qrcode
        
        print("🔐 Xiaomi Home Agent - 二维码登录\n")
        print("⚠️  二维码登录需要浏览器配合完成，当前版本建议使用密码登录\n")
        
        # 生成小米登录二维码链接
        qr_url = "https://account.xiaomi.com/pass/qr/login?sid=mijia&_qrsize=240"
        
        try:
            qr = qrcode.QRCode(version=3, box_size=10, border=2)
            qr.add_data(qr_url)
            qr.make(fit=True)
            
            qr_file = os.path.join(CONFIG_DIR, 'qr_code.png')
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(qr_file)
            
            print(f"✅ 二维码已保存: {qr_file}")
            print(f"\n📱 请使用米家 APP 扫描")
            print(f"\n🔗 或访问: {qr_url}")
            
            print("\n" + "="*50)
            qr.print_ascii(invert=True)
            print("="*50)
            
            print("\n💡 提示：扫码后请在浏览器中完成授权")
            print("   授权完成后，请使用密码方式登录以获取 Token")
            
        except Exception as e:
            print(f"❌ 生成二维码失败: {e}")
    
    def check_status(self):
        """检查登录状态"""
        auth = self._load_auth()
        if not auth:
            print("❌ 未登录")
            print("\n登录方式:")
            print("  python3 scripts/auth.py --username <手机号/邮箱> --password <密码>")
            return False
        
        username = auth.get('username', 'Unknown')
        login_time = auth.get('login_time', 0)
        days = (time.time() - login_time) / 86400
        
        print(f"✅ 已登录: {username}")
        print(f"   登录时间: {time.strftime('%Y-%m-%d %H:%M', time.localtime(login_time))}")
        print(f"   已登录: {days:.1f} 天")
        
        # 检查必要字段
        has_token = bool(auth.get('pass_token') or auth.get('service_token'))
        if has_token:
            print("   Token: 已获取")
            return True
        else:
            print("   Token: 缺失，建议重新登录")
            return False
    
    def logout(self):
        """登出"""
        if os.path.exists(self.auth_file):
            os.remove(self.auth_file)
            print("✅ 已清除登录信息")
        else:
            print("ℹ️  没有登录信息需要清除")


def main():
    parser = argparse.ArgumentParser(description='Xiaomi Home 认证管理')
    parser.add_argument('--username', type=str, help='小米账号（手机号/邮箱）')
    parser.add_argument('--password', type=str, help='密码')
    parser.add_argument('--qr', action='store_true', help='二维码登录')
    parser.add_argument('--status', action='store_true', help='检查登录状态')
    parser.add_argument('--logout', action='store_true', help='清除登录信息')
    args = parser.parse_args()
    
    auth = XiaomiAuth()
    
    if args.logout:
        auth.logout()
    elif args.status:
        auth.check_status()
    elif args.qr:
        auth.generate_qr_login()
    elif args.username and args.password:
        auth.login_with_credentials(args.username, args.password)
    else:
        auth.check_status()


if __name__ == '__main__':
    main()
