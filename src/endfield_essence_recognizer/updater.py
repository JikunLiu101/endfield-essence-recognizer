"""自动更新模块，用于从 GitHub 下载和安装最新版本"""

import asyncio
import os
import platform
import shutil
from sqlite3 import Date
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import httpx
from loguru import logger

from endfield_essence_recognizer.path import ROOT_DIR
from endfield_essence_recognizer.version import __version__

GITHUB_REPO = "JikunLiu101/endfield-essence-recognizer"
VERSION_CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


class UpdateError(Exception):
    """更新过程中的错误"""

    pass


class UpdateManager:
    """更新管理器"""

    def __init__(self):
        self.download_progress = 0.0
        self.is_downloading = False
        self.is_installing = False
        self.error_message: str | None = None

    async def get_latest_release(self) -> dict[str, Any]:
        """获取最新的 Release 信息
        
        返回格式:
        {
            "latestVersion": "0.5.0",
            "downloadUrl": "https://cos.yituliu.cn/endfield/endfield-essence-recognizer/endfield-essence-recognizer-v0.5.0-windows.zip"
        }
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(VERSION_CHECK_URL)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.exception(f"获取最新版本信息失败: {e}")
            raise UpdateError(f"获取最新版本信息失败: {e}") from e

    async def download_update(
        self, download_url: str, dest_path: Path
    ) -> Path:
        """下载更新文件，返回下载的文件路径"""
        self.is_downloading = True
        self.download_progress = 0.0
        self.error_message = None

        try:
            async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
                logger.info(f"开始下载更新: {download_url}")
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get("content-length", 0))

                    with open(dest_path, "wb") as f:
                        downloaded = 0
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                self.download_progress = (downloaded / total_size) * 100
                                if downloaded % (1024 * 1024) == 0:  # 每 MB 记录一次
                                    logger.info(
                                        f"下载进度: {self.download_progress:.1f}%"
                                    )

                logger.success(f"下载完成: {dest_path}")
                self.download_progress = 100.0
                return dest_path

        except Exception as e:
            logger.exception(f"下载更新失败: {e}")
            self.error_message = str(e)
            raise UpdateError(f"下载更新失败: {e}") from e
        finally:
            self.is_downloading = False

    async def extract_update(self, zip_path: Path, extract_to: Path) -> Path:
        """解压更新文件，返回解压后的目录"""
        try:
            logger.info(f"开始解压更新: {zip_path} -> {extract_to}")
            extract_to.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_to)

            logger.success(f"解压完成: {extract_to}")
            return extract_to

        except Exception as e:
            logger.exception(f"解压更新失败: {e}")
            raise UpdateError(f"解压更新失败: {e}") from e

    async def install_update(self, extract_dir: Path) -> None:
        """安装更新（替换当前程序文件）"""
        self.is_installing = True
        self.error_message = None

        try:
            logger.info("开始安装更新")

            # 检查是否是打包后的可执行文件
            if getattr(sys, "frozen", False):
                # 打包后的程序
                current_exe = Path(sys.executable)
                app_dir = current_exe.parent

                # 查找解压目录中的实际程序目录
                # 通常结构是: extract_dir/endfield-essence-recognizer/...
                inner_dirs = list(extract_dir.iterdir())
                if len(inner_dirs) == 1 and inner_dirs[0].is_dir():
                    source_dir = inner_dirs[0]
                else:
                    source_dir = extract_dir

                # 创建更新脚本
                update_script = self._create_update_script(source_dir, app_dir)

                logger.info(f"创建更新脚本: {update_script}")
                logger.info("程序将在 3 秒后关闭并自动更新...")

                # 等待 3 秒让用户看到提示
                await asyncio.sleep(3)

                # 执行更新脚本并退出程序
                if platform.system() == "Windows":
                    subprocess.Popen(
                        ["cmd", "/c", str(update_script)],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                        | subprocess.DETACHED_PROCESS,
                    )
                else:
                    subprocess.Popen(["bash", str(update_script)])

                # 退出当前程序
                logger.success("更新脚本已启动，程序即将退出")
                os._exit(0)

            else:
                # 开发环境，不执行实际更新
                logger.warning("检测到开发环境，跳过实际更新操作")
                raise UpdateError("开发环境不支持自动更新")

        except Exception as e:
            logger.exception(f"安装更新失败: {e}")
            self.error_message = str(e)
            raise UpdateError(f"安装更新失败: {e}") from e
        finally:
            self.is_installing = False

    def _create_update_script(self, source_dir: Path, app_dir: Path) -> Path:
        """创建更新脚本"""
        if platform.system() == "Windows":
            script_path = app_dir / "update.bat"
            script_content = f"""@echo off
chcp 65001 >nul
echo 等待程序退出...
timeout /t 2 /nobreak >nul

echo 正在更新文件...
xcopy /E /I /Y /Q "{source_dir}" "{app_dir}"

echo 清理临时文件...
rd /s /q "{source_dir.parent}"

echo 更新完成！程序将在 3 秒后重新启动...
timeout /t 3 /nobreak >nul

echo 重新启动程序...
start "" "{app_dir / 'endfield-essence-recognizer.exe'}"

del "%~f0"
"""
        else:
            script_path = app_dir / "update.sh"
            script_content = f"""#!/bin/bash
echo "等待程序退出..."
sleep 2

echo "正在更新文件..."
cp -rf "{source_dir}"/* "{app_dir}/"

echo "清理临时文件..."
rm -rf "{source_dir.parent}"

echo "更新完成！程序将在 3 秒后重新启动..."
sleep 3

echo "重新启动程序..."
cd "{app_dir}"
./endfield-essence-recognizer &

rm -- "$0"
"""
            script_path.chmod(0o755)

        script_path.write_text(script_content, encoding="utf-8")
        return script_path

    async def check_and_download_update(self) -> dict[str, Any]:
        """检查更新并下载（如果有新版本）"""
        try:
            # 获取最新版本信息
            release_info = await self.get_latest_release()
            latest_version = release_info["tag_name"].lstrip("v")
            current_version = __version__ or "0.0.0"

            logger.info(f"当前版本: {current_version}, 最新版本: {latest_version}")

            # 比较版本
            if self._compare_versions(latest_version, current_version) <= 0:
                return {
                    "has_update": False,
                    "current_version": current_version,
                    "latest_version": latest_version,
                }

            # 获取下载地址
            download_url = release_info["downloadUrl"]
            if not download_url:
                raise UpdateError("未找到更新包的下载地址")

            # 下载更新
            temp_dir = Path(tempfile.gettempdir()) / "endfield-essence-recognizer-update"
            temp_dir.mkdir(parents=True, exist_ok=True)
            # 从 URL 中提取文件名
            filename = download_url.split("/")[-1]
            zip_path = temp_dir / filename

            await self.download_update(download_url, zip_path)

            # 解压更新
            extract_dir = temp_dir / "extracted"
            await self.extract_update(zip_path, extract_dir)

            return {
                "has_update": True,
                "current_version": current_version,
                "latest_version": latest_version,
                "download_url": download_url,
                "extract_dir": str(extract_dir),
                "ready_to_install": True,
            }

        except Exception as e:
            logger.exception(f"检查或下载更新失败: {e}")
            self.error_message = str(e)
            return {
                "has_update": False,
                "error": str(e),
            }

    def _compare_versions(self, v1: str, v2: str) -> int:
        """比较版本号，返回 1 表示 v1 > v2, -1 表示 v1 < v2, 0 表示相等"""
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]

        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            if p1 > p2:
                return 1
            if p1 < p2:
                return -1
        return 0

    def get_status(self) -> dict[str, Any]:
        """获取当前更新状态"""
        return {
            "is_downloading": self.is_downloading,
            "is_installing": self.is_installing,
            "download_progress": self.download_progress,
            "error_message": self.error_message,
        }


# 全局更新管理器实例
update_manager = UpdateManager()
