# DuckyTheDuck 地图存档迁移工具

自动迁移 DuckyTheDuck 系列地图的存档文件。

## 支持的地图

- 紧急迫降 RPG (CrashRPGMaximum.SC2Bank)
- 地狱特种部队 (HSF.SC2Bank)
- 破灵者 RPG (PBRPG.SC2Bank)
- 十死无生 RPG (CDRPG.SC2Bank)
- 新星防卫 RPG (NeoStarBank.SC2Bank, NeoStarLadder.SC2Bank)

## 系统要求

- Windows 操作系统
- Python 3.7+
- 星际争霸 II

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 方式一：下载可执行文件（推荐）

1. 前往 [Releases](../../releases) 页面
2. 下载最新的 `duckies-bank-migrator.exe`
3. 双击运行，无需安装 Python

### 方式二：从源码运行

运行脚本：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行脚本
python migrate.py
```

脚本将自动：
1. 扫描所有国服账号（以 @5 结尾的快捷方式）
2. 检查哪些账号需要迁移
3. 显示账号信息（handle 和名称）
4. 让用户选择要迁移的账号
5. 列出可迁移的存档文件
6. 检查目标位置是否已有存档
7. 如果需要，创建备份（.bak1, .bak2, ...）
8. 执行迁移

## 迁移说明

脚本会将存档从旧的发布者文件夹迁移到新的发布者文件夹：
- 源文件夹：`5-S2-1-11831282`
- 目标文件夹：`5-S2-1-10786818`

## 备份

如果目标位置已存在存档文件，脚本会自动创建备份：
- 第一个备份：`文件名.SC2Bank.bak1`
- 第二个备份：`文件名.SC2Bank.bak2`
- 以此类推...

## 许可证

MIT License

## 开发

### 本地构建

```bash
# 安装构建依赖
pip install pyinstaller

# 使用 spec 文件构建
pyinstaller build.spec

# 或使用命令行构建
pyinstaller --onefile --name duckies-bank-migrator --console migrate.py
```

### 自动构建

每次推送到主分支时，GitHub Actions 会自动：
1. 使用 PyInstaller 构建 Windows 可执行文件
2. 创建一个以 commit hash 为标签的 pre-release
3. 将 `duckies-bank-migrator.exe` 上传到 release

创建正式版本：
```bash
git tag v1.0.0
git push origin v1.0.0
```
