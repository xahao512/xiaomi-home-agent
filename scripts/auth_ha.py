#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi Home Agent Skill - 基于 ha_xiaomi_home 的认证
通过小米官方 OAuth2.0 流程获取 Token
"""

import sys
import os
import json
import argparse
import time
import base64
import hashlib
import hmac
import requests
from urllib.parse import urlencode, parse_qs, urlparse

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(SKILL_ROOT, 'config')
AUTH_FILE = os.path.join(CONFIG_DIR, 'auth.json')

# OAuth2.0 配置（来自 ha_xiaomi_home）
OAUTH2_CLIENT_ID = '2882303761517852428'
OAUTH2_REDIRECT_URL = 'https://home.mi.com/ha_callback'
OAUTH2_AUTHORIZE_URL = 'https://account.xiaomi.com/oauth2/authorize'
OAUTH2_TOKEN_URL = 'https://account.xiaomi.com/oauth2/token'


class XiaomiHomeAuth:
    """基于 ha_xiaomi_home 的认证管理器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
    def _save_auth(self, auth_data):
        """保存认证信息"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        # 添加保存时间
        auth_data['saved_at'] = time.time()
        with open(AUTH_FILE, 'w', encoding='utf-8') as f:
            json.dump(auth_data, f, indent=2, ensure_ascii=False)
        print(f"✅ 认证信息已保存到: {AUTH_FILE}")
    
    def _load_auth(self):
        """加载认证信息"""
        if os.path.exists(AUTH_FILE):
            with open(AUTH_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def generate_oauth_url(self):
        """生成 OAuth2.0 授权 URL"""
        import secrets
        state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': OAUTH2_CLIENT_ID,
            'redirect_uri': OAUTH2_REDIRECT_URL,
            'response_type': 'code',
            'scope': '1 3 6000 16001',
            'state': state,
            'skip_confirm': 'false',
            'url': 'https://home.mi.com/ha_login',
        }
        
        auth_url = f"{OAUTH2_AUTHORIZE_URL}?{urlencode(params)}"
        return auth_url, state
    
    def login_with_oauth(self):
        """OAuth2.0 登录流程"""
        print("🔐 Xiaomi Home Agent - OAuth2.0 登录\n")
        print("="*60)
        
        # 生成授权 URL
        auth_url, state = self.generate_oauth_url()
        
        print("📱 请按以下步骤完成登录:\n")
        print("第 1 步: 在浏览器中打开以下链接:")
        print(f"\n{auth_url}\n")
        print("第 2 步: 使用小米账号登录并授权")
        print("第 3 步: 授权后浏览器会跳转到一个新链接")
        print("第 4 步: 复制新链接地址（包含 code=xxx 参数）")
        print("\n" + "="*60)
        
        # 提示用户输入回调 URL
        print("\n请输入授权后的回调 URL（包含 code 参数）:")
        print("(或直接输入 code 值)\n")
        
        callback_input = input("> ").strip()
        
        if not callback_input:
            print("❌ 未输入回调 URL")
            return False
        
        # 提取 code
        code = self._extract_code(callback_input)
        if not code:
            print("❌ 无法从输入中提取授权码")
            return False
        
        print(f"\n✅ 获取到授权码，正在换取 Token...")
        
        # 换取 Token
        return self._exchange_code_for_token(code)
    
    def _extract_code(self, input_str):
        """从输入中提取授权码"""
        # 如果是完整 URL
        if 'code=' in input_str:
            parsed = urlparse(input_str)
            params = parse_qs(parsed.query)
            if 'code' in params:
                return params['code'][0]
        
        # 如果只是 code 值
        if len(input_str) > 20 and ' ' not in input_str:
            return input_str
        
        return None
    
    def _exchange_code_for_token(self, code):
        """用授权码换取 Token"""
        data = {
            'client_id': OAUTH2_CLIENT_ID,
            'code': code,
            'redirect_uri': OAUTH2_REDIRECT_URL,
            'grant_type': 'authorization_code',
        }
        
        try:
            response = self.session.post(
                OAUTH2_TOKEN_URL,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                if 'access_token' in token_data:
                    # 保存认证信息
                    auth_info = {
                        'access_token': token_data.get('access_token'),
                        'refresh_token': token_data.get('refresh_token'),
                        'expires_in': token_data.get('expires_in'),
                        'token_type': token_data.get('token_type'),
                        'obtained_at': time.time(),
                    }
                    
                    self._save_auth(auth_info)
                    
                    print(f"✅ Token 获取成功!")
                    print(f"   Token 类型: {token_data.get('token_type')}")
                    print(f"   有效期: {token_data.get('expires_in')} 秒")
                    
                    # 获取用户信息
                    self._get_user_info(auth_info['access_token'])
                    
                    return True
                else:
                    print(f"❌ Token 响应异常: {token_data}")
                    return False
            else:
                print(f"❌ Token 请求失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Token 交换失败: {e}")
            return False
    
    def _get_user_info(self, access_token):
        """获取用户信息"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
            }
            
            # 调用小米 API 获取用户信息
            response = self.session.get(
                'https://api.io.mi.com/app/user/profile',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                if user_data.get('code') == 0:
                    profile = user_data.get('data', {})
                    print(f"   用户: {profile.get('nickname', 'Unknown')}")
                    
                    # 更新保存的认证信息
                    auth = self._load_auth()
                    if auth:
                        auth['user_id'] = profile.get('user_id')
                        auth['nickname'] = profile.get('nickname')
                        self._save_auth(auth)
                    
        except Exception as e:
            print(f"⚠️  获取用户信息失败: {e}")
    
    def check_status(self):
        """检查登录状态"""
        auth = self._load_auth()
        if not auth:
            print("❌ 未登录")
            print("\n登录方式:")
            print("  python3 scripts/auth_ha.py --login")
            return False
        
        print("✅ 已登录")
        print(f"   用户: {auth.get('nickname', 'Unknown')}")
        print(f"   用户ID: {auth.get('user_id', 'Unknown')}")
        
        # 检查 Token 是否过期
        obtained_at = auth.get('obtained_at', 0)
        expires_in = auth.get('expires_in', 0)
        expires_at = obtained_at + expires_in
        remaining = expires_at - time.time()
        
        if remaining > 0:
            hours = remaining / 3600
            print(f"   Token 有效期: {hours:.1f} 小时")
            return True
        else:
            print(f"   ⚠️ Token 已过期，请重新登录")
            return False
    
    def logout(self):
        """登出"""
        if os.path.exists(AUTH_FILE):
            os.remove(AUTH_FILE)
            print("✅ 已清除登录信息")
        else:
            print("ℹ️  没有登录信息需要清除")


def main():
    parser = argparse.ArgumentParser(description='Xiaomi Home OAuth2.0 认证')
    parser.add_argument('--login', action='store_true', help='登录')
    parser.add_argument('--status', action='store_true', help='检查登录状态')
    parser.add_argument('--logout', action='store_true', help='登出')
    args = parser.parse_args()
    
    auth = XiaomiHomeAuth()
    
    if args.logout:
        auth.logout()
    elif args.status:
        auth.check_status()
    elif args.login:
        auth.login_with_oauth()
    else:
        auth.check_status()


if __name__ == '__main__':
    main()
