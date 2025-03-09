# -*- coding: utf-8 -*-
"""
打包脚本，用于将应用打包为可执行文件。
"""
import os
import sys
import shutil
import subprocess
import platform


def main():
    """主函数"""
    print("开始打包LLM基准测试工具...")
    
    # 检查PyInstaller是否已安装
    try:
        import PyInstaller
        print(f"PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 检查依赖包是否已安装
    required_packages = [
        "numpy",
        "aiohttp",
        "tqdm",
        "transformers",
        "cryptography",
        "psutil",
        "matplotlib"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"{package} 已安装")
        except ImportError:
            print(f"{package} 未安装，正在安装...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    # 清理旧的构建文件
    for dir_name in ["build", "dist"]:
        if os.path.exists(dir_name):
            print(f"清理 {dir_name} 目录...")
            shutil.rmtree(dir_name)
    
    # 创建spec文件
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['logging_main.py'],  # 使用带日志记录的主文件
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'numpy',
        'aiohttp',
        'tqdm',
        'transformers',
        'cryptography',
        'psutil',
        'matplotlib',
        'matplotlib.backends.backend_tkagg'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LLM基准测试工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
"""
    
    # 写入spec文件
    with open("llm_benchmark.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    # 创建一个简单的图标
    if not os.path.exists("icon.ico"):
        try:
            # 尝试使用PIL创建一个简单的图标
            from PIL import Image, ImageDraw
            
            # 创建一个100x100的图像
            img = Image.new('RGB', (100, 100), color=(73, 109, 137))
            d = ImageDraw.Draw(img)
            
            # 绘制一些简单的图形
            d.rectangle([(20, 20), (80, 80)], fill=(255, 255, 255))
            d.text((30, 40), "LLM", fill=(0, 0, 0))
            
            # 保存为ICO文件
            img.save("icon.ico")
            print("已创建图标文件")
        except ImportError:
            print("PIL未安装，无法创建图标文件")
            # 继续而不创建图标
    
    # 执行PyInstaller
    print("正在执行PyInstaller...")
    pyinstaller_cmd = ["pyinstaller", "--clean", "llm_benchmark.spec"]
    subprocess.check_call(pyinstaller_cmd)
    
    # 创建配置目录
    dist_dir = os.path.join("dist", "LLM基准测试工具")
    if platform.system() == "Windows":
        dist_dir = os.path.join("dist", "LLM基准测试工具")
    else:
        dist_dir = os.path.join("dist", "LLM基准测试工具")
    
    config_dir = os.path.join(dist_dir, "config")
    os.makedirs(config_dir, exist_ok=True)
    
    print(f"打包完成！可执行文件位于: {dist_dir}")
    
    # 创建README文件
    readme_content = """# LLM基准测试工具

这是一个用于测试LLM服务性能的基准测试工具。

## 功能特点

- 支持多种后端（OpenAI API、vLLM等）
- 自定义测试场景
- 邮件通知功能
- API密钥管理
- 详细的性能指标

## 使用方法

1. 配置API密钥
2. 创建测试场景
3. 运行测试
4. 查看结果

## 注意事项

- 对于QQ邮箱，请使用授权码而不是登录密码
- 测试结果保存在程序目录下的benchmark_logs_*目录中
"""
    
    with open(os.path.join(dist_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("已创建README文件")


if __name__ == "__main__":
    main() 