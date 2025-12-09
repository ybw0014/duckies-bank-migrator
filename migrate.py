#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckyTheDuck 地图存档迁移工具 - GUI 版本
自动迁移星际争霸 II 国服账号的地图存档
"""

import sys
import shutil
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPushButton, QMessageBox,
    QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from sc2bank import sc2bank  # type: ignore

# 配置常量
OLD_PUBLISHER_ID: str = "5-S2-1-11831282"
NEW_PUBLISHER_ID: str = "5-S2-1-10786818"

BANK_FILES: list[str] = [
    "CrashRPGMaximumBank.SC2Bank",
    "HSF.SC2Bank",
    "PBRPG.SC2Bank",
    "CDRPGBank.SC2Bank",
    "NeoStarBank.SC2Bank",
]

BANK_NAMES: dict[str, str] = {
    "CrashRPGMaximumBank.SC2Bank": "紧急迫降 RPG",
    "HSF.SC2Bank": "地狱特种部队",
    "PBRPG.SC2Bank": "破灵者 RPG",
    "CDRPGBank.SC2Bank": "十死无生 RPG",
    "NeoStarBank.SC2Bank": "新星防卫 RPG",
}


class Account:
    """代表一个星际争霸 II 账号"""
    
    def __init__(self, account_path: Path, battle_net_id: str, handle: str) -> None:
        self.path: Path = account_path
        self.battle_net_id: str = battle_net_id
        self.handle: str = handle
        self.old_bank_path: Path = account_path / "Banks" / OLD_PUBLISHER_ID
        self.new_bank_path: Path = account_path / "Banks" / NEW_PUBLISHER_ID
    
    def has_old_banks(self) -> bool:
        if not self.old_bank_path.exists():
            return False
        for bank_file in BANK_FILES:
            if (self.old_bank_path / bank_file).exists():
                return True
        return False
    
    def get_migratable_files(self) -> list[str]:
        files = []
        if not self.old_bank_path.exists():
            return files
        for bank_file in BANK_FILES:
            if (self.old_bank_path / bank_file).exists():
                files.append(bank_file)
        return files
    
    def get_existing_target_files(self) -> list[str]:
        files = []
        if not self.new_bank_path.exists():
            return files
        for bank_file in BANK_FILES:
            if (self.new_bank_path / bank_file).exists():
                files.append(bank_file)
        return files


class MigrationWorker(QThread):
    """后台迁移线程"""
    finished = pyqtSignal(bool, str)  # type: ignore
    
    def __init__(self, account: Account, selected_files: list[str]) -> None:
        super().__init__()
        self.account: Account = account
        self.selected_files: list[str] = selected_files
    
    def run(self) -> None:
        try:
            # 确保目标文件夹存在
            self.account.new_bank_path.mkdir(parents=True, exist_ok=True)
            
            migrated_count = 0
            backup_count = 0
            
            for bank_file in self.selected_files:
                source = self.account.old_bank_path / bank_file
                target = self.account.new_bank_path / bank_file
                
                try:
                    # 如果目标文件已存在，创建备份
                    if target.exists():
                        backup_num = 1
                        while True:
                            backup_path = target.parent / f"{target.name}.bak{backup_num}"
                            if not backup_path.exists():
                                _ = shutil.copy2(target, backup_path)
                                backup_count += 1
                                break
                            backup_num += 1
                    
                    # 复制文件
                    _ = shutil.copy2(source, target)
                    migrated_count += 1
                    
                    # 重新生成签名
                    _ = self.resign_bank_file(target, self.account.handle)
                    
                except Exception:
                    pass  # 忽略单个文件的错误，继续处理下一个
            
            msg = f"迁移完成！\n成功迁移: {migrated_count} 个文件"
            if backup_count > 0:
                msg += f"\n创建备份: {backup_count} 个文件"
            
            self.finished.emit(True, msg)
            
        except Exception as e:
            self.finished.emit(False, f"迁移失败: {str(e)}")
    
    def resign_bank_file(self, bank_file_path: Path, user_id: str) -> bool:
        """重新生成签名"""
        try:
            author_id = NEW_PUBLISHER_ID
            bank_name = bank_file_path.stem
            
            bank, old_signature = sc2bank.parse(str(bank_file_path))
            new_signature = sc2bank.sign(author_id, user_id, bank_name, bank)
            
            with open(bank_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_signature and old_signature in content:
                new_content = content.replace(old_signature, new_signature)
            else:
                if '</Bank>' in content:
                    signature_tag = f'    <Signature value="{new_signature}"/>\n</Bank>'
                    new_content = content.replace('</Bank>', signature_tag)
                else:
                    return False
            
            with open(bank_file_path, 'w', encoding='utf-8') as f:
                _ = f.write(new_content)
            
            return True
        except Exception:
            return False


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.accounts: list[Account] = []
        self.selected_account: Account | None = None
        self.account_list: QListWidget
        self.bank_group: QGroupBox
        self.bank_list: QListWidget
        self.migrate_btn: QPushButton
        self.worker: MigrationWorker | None = None
        self.init_ui()
        self.scan_accounts()
    
    def init_ui(self) -> None:
        self.setWindowTitle("DuckyTheDuck 地图存档迁移工具")
        self.setMinimumSize(700, 500)
        
        # 主widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("DuckyTheDuck 地图存档迁移工具")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 账号选择区域
        account_group = QGroupBox("1. 选择账号")
        account_layout = QVBoxLayout()
        
        self.account_list = QListWidget()
        self.account_list.setCursor(Qt.CursorShape.PointingHandCursor)
        _ = self.account_list.itemClicked.connect(self.on_account_selected)  # type: ignore
        account_layout.addWidget(self.account_list)
        
        account_group.setLayout(account_layout)
        layout.addWidget(account_group)
        
        # 存档选择区域
        self.bank_group = QGroupBox("2. 选择要迁移的存档")
        self.bank_group.setEnabled(False)
        bank_layout = QVBoxLayout()
        
        self.bank_list = QListWidget()
        self.bank_list.setCursor(Qt.CursorShape.PointingHandCursor)
        bank_layout.addWidget(self.bank_list)
        
        select_buttons = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _ = select_all_btn.clicked.connect(self.select_all_banks)  # type: ignore
        deselect_all_btn = QPushButton("全不选")
        deselect_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _ = deselect_all_btn.clicked.connect(self.deselect_all_banks)  # type: ignore
        select_buttons.addWidget(select_all_btn)
        select_buttons.addWidget(deselect_all_btn)
        select_buttons.addStretch()
        bank_layout.addLayout(select_buttons)
        
        self.bank_group.setLayout(bank_layout)
        layout.addWidget(self.bank_group)
        
        # 开始迁移按钮
        self.migrate_btn = QPushButton("开始迁移")
        self.migrate_btn.setEnabled(False)
        self.migrate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _ = self.migrate_btn.clicked.connect(self.start_migration)  # type: ignore
        self.migrate_btn.setMinimumHeight(40)
        layout.addWidget(self.migrate_btn)
    
    def scan_accounts(self) -> None:
        """扫描账号"""
        try:
            documents = Path(os.path.expandvars("%USERPROFILE%")) / "Documents"
            sc2_path = documents / "StarCraft II"
            
            if not sc2_path.exists():
                _ = QMessageBox.critical(self, "错误", f"未找到星际争霸 II 文档文件夹:\n{sc2_path}")
                return
            
            accounts_path = sc2_path / "Accounts"
            
            if not accounts_path.exists():
                _ = QMessageBox.critical(self, "错误", f"未找到 Accounts 文件夹:\n{accounts_path}")
                return
            
            # 遍历所有账号
            for battle_net_id_folder in accounts_path.iterdir():
                if not battle_net_id_folder.is_dir():
                    continue
                
                battle_net_id = battle_net_id_folder.name
                
                for handle_folder in battle_net_id_folder.iterdir():
                    if not handle_folder.is_dir():
                        continue
                    
                    handle = handle_folder.name
                    
                    if handle.startswith("5-S2-1"):
                        account = Account(handle_folder, battle_net_id, handle)
                        if account.has_old_banks():
                            self.accounts.append(account)
            
            # 显示账号列表
            if not self.accounts:
                _ = QMessageBox.information(self, "提示", "未找到需要迁移的账号。\n\n可能的原因:\n1. 所有账号的存档已经迁移完成\n2. 没有符合条件的国服账号\n3. 旧存档文件夹中没有需要迁移的存档文件")
                return
            
            for account in self.accounts:
                item = QListWidgetItem(f"句柄: {account.handle}\n战网 ID: {account.battle_net_id}")
                self.account_list.addItem(item)
        
        except Exception as e:
            _ = QMessageBox.critical(self, "错误", f"扫描账号时出错:\n{str(e)}")
    
    def on_account_selected(self, item: QListWidgetItem) -> None:
        """账号被选中"""
        index = self.account_list.row(item)
        self.selected_account = self.accounts[index]
        
        # 清空并填充存档列表
        self.bank_list.clear()
        
        migratable = self.selected_account.get_migratable_files()
        existing = self.selected_account.get_existing_target_files()
        
        for bank_file in migratable:
            bank_name = BANK_NAMES.get(bank_file, bank_file)
            
            # 创建复选框项
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 2, 5, 2)
            
            checkbox = QCheckBox(f"{bank_name} ({bank_file})")
            checkbox.setChecked(True)
            _ = checkbox.setProperty("bank_file", bank_file)
            item_layout.addWidget(checkbox)
            
            # 如果目标已存在，显示警告
            if bank_file in existing:
                warning = QLabel("⚠ 已有存档")
                warning.setStyleSheet("color: orange; font-weight: bold;")
                item_layout.addWidget(warning)
            
            item_layout.addStretch()
            
            list_item = QListWidgetItem(self.bank_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.bank_list.addItem(list_item)
            self.bank_list.setItemWidget(list_item, item_widget)
        
        self.bank_group.setEnabled(True)
        self.migrate_btn.setEnabled(True)
    
    def select_all_banks(self) -> None:
        """全选所有存档"""
        for i in range(self.bank_list.count()):
            item = self.bank_list.item(i)
            if item:
                widget = self.bank_list.itemWidget(item)
                if widget:
                    checkbox = widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(True)
    
    def deselect_all_banks(self) -> None:
        """取消全选"""
        for i in range(self.bank_list.count()):
            item = self.bank_list.item(i)
            if item:
                widget = self.bank_list.itemWidget(item)
                if widget:
                    checkbox = widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(False)
    
    def start_migration(self) -> None:
        """开始迁移"""
        if not self.selected_account:
            return
        
        # 获取选中的存档文件
        selected_files: list[str] = []
        for i in range(self.bank_list.count()):
            item = self.bank_list.item(i)
            if item:
                widget = self.bank_list.itemWidget(item)
                if widget:
                    checkbox = widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        bank_file_prop = checkbox.property("bank_file")  # type: ignore
                        if isinstance(bank_file_prop, str):
                            selected_files.append(bank_file_prop)
        
        if not selected_files:
            _ = QMessageBox.warning(self, "提示", "请至少选择一个存档进行迁移")
            return
        
        # 确认对话框
        existing = self.selected_account.get_existing_target_files()
        existing_selected = [f for f in selected_files if f in existing]
        
        msg = f"即将迁移 {len(selected_files)} 个存档文件"
        if existing_selected:
            msg += f"\n\n其中 {len(existing_selected)} 个文件在目标位置已存在，将创建备份后覆盖"
        msg += "\n\n确认开始迁移吗？"
        
        reply = QMessageBox.question(self, "确认迁移", msg, 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # 禁用控件
        self.account_list.setEnabled(False)
        self.bank_group.setEnabled(False)
        self.migrate_btn.setEnabled(False)
        
        # 启动迁移线程
        if self.selected_account:  # 确保不为 None
            self.worker = MigrationWorker(self.selected_account, selected_files)
            _ = self.worker.finished.connect(self.on_migration_finished)  # type: ignore
            self.worker.start()
    
    def on_migration_finished(self, success: bool, message: str) -> None:
        """迁移完成"""
        # 恢复控件
        self.account_list.setEnabled(True)
        self.bank_group.setEnabled(True)
        self.migrate_btn.setEnabled(True)
        
        if success:
            _ = QMessageBox.information(self, "迁移完成", message)
            # 刷新存档列表以更新警告状态
            current_item = self.account_list.currentItem()
            if current_item:
                self.on_account_selected(current_item)
        else:
            _ = QMessageBox.critical(self, "迁移失败", message)


def main():
    app = QApplication(sys.argv)
    
    # 检查操作系统
    if sys.platform != "win32":
        _ = QMessageBox.critical(None, "错误", "此程序仅支持 Windows 系统")
        sys.exit(1)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
