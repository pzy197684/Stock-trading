#!/usr/bin/env python3
# 测试profile扫描逻辑

import os
import json
import sys

def test_profile_scan():
    """测试profile文件扫描"""
    accounts = []
    profiles_dir = "profiles"
    
    print(f"检查profiles目录: {profiles_dir}")
    print(f"目录存在: {os.path.exists(profiles_dir)}")
    
    if os.path.exists(profiles_dir):
        print(f"扫描平台目录...")
        # 扫描平台目录 (BINANCE, COINW, OKX, DEEP)
        for platform_dir in os.listdir(profiles_dir):
            if platform_dir.startswith('_'):  # 跳过 _shared_defaults
                continue
            platform_path = os.path.join(profiles_dir, platform_dir)
            if os.path.isdir(platform_path):
                print(f"扫描平台: {platform_dir}")
                # 扫描账号目录
                for account in os.listdir(platform_path):
                    account_path = os.path.join(platform_path, account)
                    if os.path.isdir(account_path):
                        profile_file = os.path.join(account_path, 'profile.json')
                        print(f"检查profile文件: {profile_file}")
                        if os.path.exists(profile_file):
                            print(f"Profile文件存在，读取...")
                            try:
                                with open(profile_file, 'r', encoding='utf-8') as f:
                                    profile = json.load(f)
                                    account_platform = profile.get('profile_info', {}).get('platform', 'unknown')
                                    print(f"加载账号 {account}, 平台: {account_platform}")
                                    
                                    accounts.append({
                                        "id": account,
                                        "name": profile.get('profile_info', {}).get('display_name', account),
                                        "platform": account_platform,
                                        "status": "configured",
                                        "balance": 0.0,
                                        "last_active": None,
                                        "config": profile
                                    })
                            except Exception as e:
                                print(f"读取账号 {account} 的profile失败: {e}")
    
    print(f"总共找到账号: {len(accounts)}")
    for acc in accounts:
        print(f"- {acc['id']}: {acc['name']} ({acc['platform']})")
    
    return accounts

if __name__ == "__main__":
    test_profile_scan()