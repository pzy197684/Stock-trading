#!/usr/bin/env python3

import sys
sys.path.append('.')

# 导入模块
import os
import json
from core.logger import logger

def test_api_accounts():
    """模拟API中的账号获取逻辑"""
    accounts = []
    
    # 方法2：扫描新的profiles目录获取配置的账号
    profiles_dir = 'profiles'
    logger.log_info(f'Checking profiles directory: {profiles_dir}')
    
    if os.path.exists(profiles_dir):
        logger.log_info(f'New profiles directory exists, scanning...')
        # 扫描平台目录 (BINANCE, COINW, OKX, DEEP)
        for platform_dir in os.listdir(profiles_dir):
            if platform_dir.startswith('_'):  # 跳过 _shared_defaults
                continue
            platform_path = os.path.join(profiles_dir, platform_dir)
            if os.path.isdir(platform_path):
                logger.log_info(f'Scanning platform: {platform_dir}')
                # 扫描账号目录
                for account in os.listdir(platform_path):
                    account_path = os.path.join(platform_path, account)
                    if os.path.isdir(account_path):
                        profile_file = os.path.join(account_path, 'profile.json')
                        logger.log_info(f'Checking profile file: {profile_file}')
                        if os.path.exists(profile_file):
                            logger.log_info(f'Profile file exists, reading...')
                            try:
                                with open(profile_file, 'r', encoding='utf-8') as f:
                                    profile = json.load(f)
                                    account_platform = profile.get('profile_info', {}).get('platform', 'unknown')
                                    logger.log_info(f'Loaded profile for {account}, platform: {account_platform}')
                                    
                                    # 检查是否已在列表中
                                    if not any(acc['id'] == account for acc in accounts):
                                        accounts.append({
                                            'id': account,
                                            'name': profile.get('profile_info', {}).get('display_name', account),
                                            'platform': account_platform,
                                            'status': 'configured',
                                            'balance': 0.0,
                                            'last_active': None,
                                            'config': profile
                                        })
                            except Exception as e:
                                logger.log_error(f'Failed to read profile for account {account}: {e}')
    
    logger.log_info(f'Total accounts found: {len(accounts)}')
    for acc in accounts:
        logger.log_info(f'Account: {acc["id"]}, Platform: {acc["platform"]}, Status: {acc["status"]}')
    
    return accounts

if __name__ == "__main__":
    test_api_accounts()