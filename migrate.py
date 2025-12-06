#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckyTheDuck 地图存档迁移工具
自动迁移星际争霸 II 国服账号的地图存档
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import json

# 配置常量
OLD_PUBLISHER_ID = "5-S2-1-11831282"  # 旧发布者 ID
NEW_PUBLISHER_ID = "5-S2-1-10786818"  # 新发布者 ID

# 需要迁移的存档文件列表
BANK_FILES = [
    "CrashRPGMaximum.SC2Bank",  # 紧急迫降 RPG
    "HSF.SC2Bank",              # 地狱特种部队
    "PBRPG.SC2Bank",            # 破灵者 RPG
    "CDRPG.SC2Bank",            # 十死无生 RPG
    "NeoStarBank.SC2Bank",      # 新星防卫 RPG
    "NeoStarLadder.SC2Bank",    # 新星防卫 RPG 排行榜
]

# 地图名称映射
BANK_NAMES = {
    "CrashRPGMaximum.SC2Bank": "紧急迫降 RPG",
    "HSF.SC2Bank": "地狱特种部队",
    "PBRPG.SC2Bank": "破灵者 RPG",
    "CDRPG.SC2Bank": "十死无生 RPG",
    "NeoStarBank.SC2Bank": "新星防卫 RPG",
    "NeoStarLadder.SC2Bank": "新星防卫 RPG 排行榜",
}


class Account:
    """代表一个星际争霸 II 账号"""
    
    def __init__(self, account_path: Path, battle_net_id: str, handle: str):
        self.path = account_path
        self.battle_net_id = battle_net_id
        self.handle = handle
        self.display_name = None  # 将从快捷方式反推
        self.old_bank_path = account_path / "Banks" / OLD_PUBLISHER_ID
        self.new_bank_path = account_path / "Banks" / NEW_PUBLISHER_ID
    
    def has_old_banks(self) -> bool:
        """检查是否有旧的存档文件"""
        if not self.old_bank_path.exists():
            return False
        
        for bank_file in BANK_FILES:
            if (self.old_bank_path / bank_file).exists():
                return True
        return False
    
    def get_migratable_files(self) -> List[str]:
        """获取可迁移的存档文件列表"""
        files = []
        if not self.old_bank_path.exists():
            return files
        
        for bank_file in BANK_FILES:
            if (self.old_bank_path / bank_file).exists():
                files.append(bank_file)
        return files
    
    def get_existing_target_files(self) -> List[str]:
        """获取目标位置已存在的存档文件列表"""
        files = []
        if not self.new_bank_path.exists():
            return files
        
        for bank_file in BANK_FILES:
            if (self.new_bank_path / bank_file).exists():
                files.append(bank_file)
        return files


def get_sc2_documents_path() -> Path:
    """获取星际争霸 II 文档路径"""
    documents = Path(os.path.expandvars("%USERPROFILE%")) / "Documents"
    sc2_path = documents / "StarCraft II"
    
    if not sc2_path.exists():
        print(f"错误: 未找到星际争霸 II 文档文件夹: {sc2_path}")
        sys.exit(1)
    
    return sc2_path


def find_display_name_from_shortcuts(sc2_path: Path, handle: str) -> Optional[str]:
    """从快捷方式反推显示名称"""
    # 遍历 StarCraft II 根目录下的所有 .lnk 文件
    for item in sc2_path.iterdir():
        if item.is_file() and item.suffix == ".lnk":
            # 解析快捷方式目标
            target_path = resolve_shortcut(item)
            if target_path:
                # 检查目标路径是否包含这个 handle
                if handle in str(target_path):
                    # 快捷方式的名称就是用户的显示名称
                    display_name = item.stem  # 不带 .lnk 扩展名
                    return display_name
    return None


def scan_accounts() -> List[Account]:
    """扫描所有国服账号"""
    sc2_path = get_sc2_documents_path()
    accounts_path = sc2_path / "Accounts"
    accounts = []
    
    print("正在扫描国服账号...")
    print(f"扫描路径: {accounts_path}\n")
    
    if not accounts_path.exists():
        print(f"错误: 未找到 Accounts 文件夹: {accounts_path}")
        return accounts
    
    # 遍历所有战网 ID 文件夹
    for battle_net_id_folder in accounts_path.iterdir():
        if not battle_net_id_folder.is_dir():
            continue
        
        battle_net_id = battle_net_id_folder.name
        
        # 遍历该战网 ID 下的所有 handle 文件夹
        for handle_folder in battle_net_id_folder.iterdir():
            if not handle_folder.is_dir():
                continue
            
            handle = handle_folder.name
            
            # 检查是否是国服账号 (handle 以 5-S2-1 开头)
            if handle.startswith("5-S2-1"):
                account = Account(handle_folder, battle_net_id, handle)
                
                # 检查是否有需要迁移的旧存档
                if account.has_old_banks():
                    # 尝试从快捷方式反推显示名称
                    account.display_name = find_display_name_from_shortcuts(sc2_path, handle)
                    accounts.append(account)
    
    return accounts


def resolve_shortcut(shortcut_path: Path) -> Optional[Path]:
    """解析 Windows 快捷方式"""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        target = shortcut.Targetpath
        return Path(target) if target else None
    except ImportError:
        # pywin32 未安装，跳过快捷方式解析
        return None
    except Exception as e:
        # 解析失败，跳过
        return None


def display_accounts(accounts: List[Account]) -> None:
    """显示找到的账号"""
    print(f"找到 {len(accounts)} 个需要迁移的账号:\n")
    
    for i, account in enumerate(accounts, 1):
        display = f"{i}. Handle: {account.handle}"
        if account.display_name:
            display += f" | 名称: {account.display_name}"
        print(display)
        
        # 显示战网 ID
        print(f"   战网 ID: {account.battle_net_id}")
        
        # 显示可迁移的文件数量
        files = account.get_migratable_files()
        print(f"   可迁移存档: {len(files)} 个")
    
    print()


def select_account(accounts: List[Account]) -> Optional[Account]:
    """让用户选择要迁移的账号"""
    while True:
        try:
            choice = input("请选择要迁移的账号编号 (输入 0 取消): ").strip()
            
            if choice == "0":
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(accounts):
                return accounts[index]
            else:
                print(f"无效的选择，请输入 1-{len(accounts)} 之间的数字\n")
        except ValueError:
            print("请输入有效的数字\n")
        except KeyboardInterrupt:
            print("\n\n操作已取消")
            return None


def create_backup(file_path: Path) -> Path:
    """创建备份文件，返回备份文件路径"""
    backup_num = 1
    while True:
        backup_path = file_path.parent / f"{file_path.name}.bak{backup_num}"
        if not backup_path.exists():
            shutil.copy2(file_path, backup_path)
            return backup_path
        backup_num += 1


def migrate_account(account: Account) -> bool:
    """迁移账号的存档"""
    print(f"\n{'='*60}")
    print(f"开始迁移账号: {account.handle}")
    if account.display_name:
        print(f"名称: {account.display_name}")
    print(f"{'='*60}\n")
    
    # 获取可迁移的文件
    source_files = account.get_migratable_files()
    print(f"可迁移的存档文件 ({len(source_files)} 个):")
    for f in source_files:
        print(f"  ✓ {f} ({BANK_NAMES.get(f, '未知地图')})")
    print()
    
    # 检查目标位置已存在的文件
    existing_files = account.get_existing_target_files()
    if existing_files:
        print(f"目标位置已存在的存档文件 ({len(existing_files)} 个):")
        for f in existing_files:
            print(f"  ! {f} ({BANK_NAMES.get(f, '未知地图')})")
        print()
    
    # 确认迁移
    print("即将执行以下操作:")
    print(f"  源文件夹: {account.old_bank_path}")
    print(f"  目标文件夹: {account.new_bank_path}")
    
    if existing_files:
        print(f"  ⚠ 将为 {len(existing_files)} 个已存在的文件创建备份")
    
    confirm = input("\n确认开始迁移? (y/n): ").strip().lower()
    if confirm != 'y':
        print("迁移已取消")
        return False
    
    # 确保目标文件夹存在
    account.new_bank_path.mkdir(parents=True, exist_ok=True)
    
    # 开始迁移
    print("\n开始迁移...")
    migrated_count = 0
    backup_count = 0
    
    for bank_file in source_files:
        source = account.old_bank_path / bank_file
        target = account.new_bank_path / bank_file
        
        try:
            # 如果目标文件已存在，创建备份
            if target.exists():
                backup_path = create_backup(target)
                print(f"  备份: {bank_file} -> {backup_path.name}")
                backup_count += 1
            
            # 复制文件
            shutil.copy2(source, target)
            print(f"  迁移: {bank_file} ({BANK_NAMES.get(bank_file, '未知地图')})")
            migrated_count += 1
            
        except Exception as e:
            print(f"  错误: 迁移 {bank_file} 失败: {e}")
    
    # 显示结果
    print(f"\n{'='*60}")
    print(f"迁移完成!")
    print(f"  成功迁移: {migrated_count} 个文件")
    if backup_count > 0:
        print(f"  创建备份: {backup_count} 个文件")
    print(f"{'='*60}\n")
    
    return True


def main():
    """主函数"""
    print("="*60)
    print(" DuckyTheDuck 地图存档迁移工具 ".center(60))
    print("="*60)
    print()
    
    # 检查操作系统
    if sys.platform != "win32":
        print("错误: 此脚本仅支持 Windows 系统")
        sys.exit(1)
    
    # 扫描账号
    accounts = scan_accounts()
    
    if not accounts:
        print("未找到需要迁移的账号。")
        print("\n可能的原因:")
        print("  1. 所有账号的存档已经迁移完成")
        print("  2. 没有符合条件的国服账号 (handle 以 5-S2-1 开头)")
        print("  3. 旧存档文件夹中没有需要迁移的存档文件")
        print(f"  4. Accounts 文件夹不存在或为空")
        input("\n按回车键退出...")
        return
    
    # 显示账号列表
    display_accounts(accounts)
    
    # 让用户选择账号
    selected = select_account(accounts)
    
    if selected:
        # 执行迁移
        success = migrate_account(selected)
        
        if success:
            print("迁移成功! 你现在可以在游戏中使用新的地图了。")
        else:
            print("迁移已取消或失败。")
    else:
        print("未选择账号，退出。")
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        sys.exit(1)
