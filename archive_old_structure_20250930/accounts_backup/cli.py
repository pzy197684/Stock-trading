# -*- coding: utf-8 -*-
# accounts/cli.py
# 功能：账户管理命令行工具

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from account_manager import AccountManager

class AccountCLI:
    """账户管理命令行接口"""
    
    def __init__(self):
        self.manager = AccountManager()
    
    def cmd_list(self, args) -> None:
        """列出所有账户"""
        accounts = self.manager.list_accounts()
        if not accounts:
            print("没有找到任何账户")
            return
        
        print(f"找到 {len(accounts)} 个账户:")
        for account in accounts:
            # 获取基本信息
            info = self.manager.get_account_info(account)
            status = "✓" if info["validation"]["passed"] else "✗"
            env = info.get("settings", {}).get("environment", "unknown")
            platform = info.get("settings", {}).get("platform", "unknown")
            
            print(f"  {status} {account:20s} [{platform:8s}] [{env:8s}]")
    
    def cmd_info(self, args) -> None:
        """显示账户详细信息"""
        if not args.account:
            print("错误: 请指定账户名称")
            return
        
        info = self.manager.get_account_info(args.account)
        if not info["exists"]:
            print(f"错误: 账户 '{args.account}' 不存在")
            return
        
        print(f"账户信息: {args.account}")
        print("=" * 50)
        
        # 基本信息
        settings = info.get("settings", {})
        print(f"平台:     {settings.get('platform', 'unknown')}")
        print(f"环境:     {settings.get('environment', 'unknown')}")
        print(f"描述:     {settings.get('description', '无')}")
        print(f"创建时间: {settings.get('created_date', '未知')}")
        
        # API密钥状态
        print(f"\nAPI密钥状态:")
        api_keys = info.get("api_keys", {})
        if not api_keys:
            print("  无API密钥文件")
        else:
            for exchange, key_info in api_keys.items():
                status = "✓ 可用" if key_info["available"] else f"✗ {key_info.get('error', '未知错误')}"
                print(f"  {exchange:10s}: {status}")
        
        # 验证状态
        validation = info.get("validation", {})
        validation_status = "✓ 通过" if validation["passed"] else f"✗ {validation['message']}"
        print(f"\n验证状态: {validation_status}")
        
        # 交易设置
        if "trading_settings" in settings:
            print(f"\n交易设置:")
            trading = settings["trading_settings"]
            print(f"  默认交易对: {trading.get('default_symbol', '未设置')}")
            print(f"  持仓模式:   {trading.get('position_mode', '未设置')}")
            print(f"  保证金类型: {trading.get('margin_type', '未设置')}")
            print(f"  杠杆倍数:   {trading.get('leverage', '未设置')}")
        
        # 风险限制
        if "risk_limits" in settings:
            print(f"\n风险限制:")
            risk = settings["risk_limits"]
            print(f"  最大日亏损: {risk.get('max_daily_loss', '未设置')}")
            print(f"  最大持仓:   {risk.get('max_total_position', '未设置')}")
            print(f"  最大委托:   {risk.get('max_open_orders', '未设置')}")
    
    def cmd_validate(self, args) -> None:
        """验证账户配置"""
        if not args.account:
            print("错误: 请指定账户名称")
            return
        
        success, message = self.manager.validate_account(args.account)
        status = "通过" if success else "失败"
        print(f"验证结果: {status}")
        print(f"详细信息: {message}")
        
        if not success:
            sys.exit(1)
    
    def cmd_summary(self, args) -> None:
        """显示账户摘要"""
        summary = self.manager.export_account_summary()
        
        print("账户摘要")
        print("=" * 50)
        print(f"账户总数: {summary['total_accounts']}")
        
        stats = summary["statistics"]
        print(f"验证通过: {stats['validated_accounts']}")
        print(f"验证失败: {stats['error_accounts']}")
        print(f"测试环境: {stats['testnet_accounts']}")
        print(f"实盘环境: {stats['live_accounts']}")
        
        if args.verbose:
            print(f"\n详细列表:")
            for account_name, account_data in summary["accounts"].items():
                status = "✓" if account_data["validation_passed"] else "✗"
                platform = account_data.get("platform", "unknown")
                env = account_data.get("environment", "unknown")
                print(f"  {status} {account_name:20s} [{platform:8s}] [{env:8s}]")
    
    def cmd_create(self, args) -> None:
        """创建新账户模板"""
        if not args.account:
            print("错误: 请指定账户名称")
            return
        
        exchange = args.exchange or "binance"
        environment = args.environment or "testnet"
        
        print(f"创建账户模板: {args.account}")
        print(f"交易所: {exchange}")
        print(f"环境: {environment}")
        
        success = self.manager.create_account_template(
            account_name=args.account,
            exchange=exchange,
            environment=environment
        )
        
        if success:
            print(f"✓ 账户模板创建成功")
            print(f"请编辑以下文件填入实际配置:")
            account_dir = self.manager.accounts_dir / args.account
            print(f"  - {account_dir / f'template_{exchange}_api.json'}")
            print(f"  - {account_dir / 'account_settings.json'}")
        else:
            print("✗ 账户模板创建失败")
            sys.exit(1)
    
    def cmd_check_api(self, args) -> None:
        """检查API密钥连通性（不执行实际交易）"""
        if not args.account:
            print("错误: 请指定账户名称")
            return
        
        print(f"检查账户 '{args.account}' 的API连通性...")
        
        # 加载API密钥
        success, api_data = self.manager.load_api_keys(args.account, args.exchange or "binance")
        if not success:
            print(f"✗ API密钥加载失败: {api_data.get('error')}")
            return
        
        print("✓ API密钥加载成功")
        print("注意: 实际连通性测试需要集成到交易框架中")
        
        # 显示API权限配置
        settings = api_data.get("settings", {})
        if settings:
            print(f"API设置:")
            print(f"  测试网:   {settings.get('testnet', False)}")
            print(f"  基础URL:  {settings.get('base_url', '未设置')}")
            print(f"  超时时间: {settings.get('timeout', 30)}秒")
    
    def run(self):
        """运行命令行工具"""
        parser = argparse.ArgumentParser(description='账户管理工具')
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # list命令
        list_parser = subparsers.add_parser('list', help='列出所有账户')
        
        # info命令
        info_parser = subparsers.add_parser('info', help='显示账户详细信息')
        info_parser.add_argument('account', help='账户名称')
        
        # validate命令
        validate_parser = subparsers.add_parser('validate', help='验证账户配置')
        validate_parser.add_argument('account', help='账户名称')
        
        # summary命令
        summary_parser = subparsers.add_parser('summary', help='显示账户摘要')
        summary_parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
        
        # create命令
        create_parser = subparsers.add_parser('create', help='创建新账户模板')
        create_parser.add_argument('account', help='账户名称')
        create_parser.add_argument('-e', '--exchange', default='binance', help='交易所 (默认: binance)')
        create_parser.add_argument('--environment', choices=['testnet', 'live'], default='testnet', help='环境类型')
        
        # check-api命令
        api_parser = subparsers.add_parser('check-api', help='检查API密钥')
        api_parser.add_argument('account', help='账户名称')
        api_parser.add_argument('-e', '--exchange', default='binance', help='交易所')
        
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        try:
            # 执行相应命令
            command_method = getattr(self, f'cmd_{args.command.replace("-", "_")}')
            command_method(args)
        except Exception as e:
            print(f"执行命令失败: {e}")
            sys.exit(1)


def main():
    """程序入口点"""
    try:
        cli = AccountCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()