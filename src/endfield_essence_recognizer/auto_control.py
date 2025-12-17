"""
终末地自动化控制脚本
功能：
- 按 "[" 键：对终末地窗口截图并保存
- 按 "]" 键：持续点击终末地窗口正中间，再次按 "]" 键中断
- 按 Alt+Delete：退出程序
"""

from __future__ import annotations

import importlib.resources
import json
import threading
import time
import warnings
import winsound
from datetime import datetime
from pathlib import Path

import keyboard
import numpy as np
import pyautogui
import pygetwindow
import win32gui

from endfield_essence_recognizer.data import (
    all_attribute_stats,
    all_secondary_stats,
    all_skill_stats,
    weapons,
)
from endfield_essence_recognizer.image import (
    linear_operation,
    load_image,
    save_image,
    scope_to_slice,
)
from endfield_essence_recognizer.log import logger
from endfield_essence_recognizer.recognizer import (
    Recognizer,
    preprocess_text_roi,
    preprocess_text_template,
)
from endfield_essence_recognizer.screenshot import (
    get_client_rect,
    get_client_rect_screen_by_ctypes,
    get_client_rect_screen_by_win32gui,
    screenshot_by_pyautogui,
    screenshot_by_win32ui,
    screenshot_window,
)

# 资源路径
enable_sound_path = Path("sounds/enable.wav")
disable_sound_path = Path("sounds/disable.wav")
screenshot_dir = Path("screenshots")
generated_template_dir = (
    importlib.resources.files("endfield_essence_recognizer") / "templates/generated"
)
screenshot_template_dir = (
    importlib.resources.files("endfield_essence_recognizer") / "templates/screenshot"
)

supported_window_titles = ["EndfieldTBeta2", "明日方舟：终末地"]
"""支持的窗口标题列表"""

# 全局变量
running = True
"""程序运行状态标志"""
essence_scanner_thread: EssenceScanner | None = None
"""基质扫描器线程实例"""

# 基质图标位置网格（客户区像素坐标）
# 5 行 9 列，共 45 个图标位置
essence_icon_x_list = np.linspace(128, 1374, 9).astype(int)
essence_icon_y_list = np.linspace(196, 819, 5).astype(int)

# 识别相关常量
RESOLUTION = (1920, 1080)
AREA = (1465, 79, 1883, 532)
DEPRECATE_BUTTON_POS = (1807, 284)
"""弃用按钮点击坐标"""
LOCK_BUTTON_POS = (1839, 286)
"""锁定按钮点击坐标"""
DEPRECATE_BUTTON_ROI = (1790, 270, 1823, 302)
"""弃用按钮截图区域"""
LOCK_BUTTON_ROI = (1825, 270, 1857, 302)
"""锁定按钮截图区域"""
STATS_0_ROI = (1508, 358, 1700, 390)
"""属性 0 截图区域"""
STATS_1_ROI = (1508, 416, 1700, 448)
"""属性 1 截图区域"""
STATS_2_ROI = (1508, 468, 1700, 500)
"""属性 2 截图区域"""

# 构造识别器实例
text_recognizer = Recognizer(
    labels=all_attribute_stats + all_secondary_stats + all_skill_stats,
    templates_dir=Path(str(generated_template_dir)),
    # preprocess_roi=preprocess_text_roi,
    # preprocess_template=preprocess_text_template,
)
icon_recognizer = Recognizer(
    labels=["deprecated", "not_deprecated", "locked", "not_locked"],
    templates_dir=Path(str(screenshot_template_dir)),
)


def get_active_support_window() -> pygetwindow.Window | None:
    active_window = pygetwindow.getActiveWindow()
    if active_window is not None and active_window.title in supported_window_titles:
        return active_window
    else:
        return None


def click_on_window(
    window: pygetwindow.Window, relative_x: int, relative_y: int
) -> None:
    """在指定窗口的客户区坐标 (x, y) 位置点击"""
    client_rect = get_client_rect(window)
    screen_x = client_rect["left"] + relative_x
    screen_y = client_rect["top"] + relative_y
    pyautogui.click(screen_x, screen_y)


class EssenceScanner(threading.Thread):
    """
    基质图标扫描器后台线程。

    此线程负责自动遍历游戏界面中的 45 个基质图标位置，
    对每个位置执行"点击 -> 截图 -> 识别"的流程。
    """

    def __init__(
        self,
    ) -> None:
        super().__init__(daemon=True)
        self._scanning = threading.Event()

    def run(self) -> None:
        logger.info("开始基质扫描线程...")
        self._scanning.set()
        for i, j in np.ndindex(len(essence_icon_y_list), len(essence_icon_x_list)):
            relative_x = essence_icon_x_list[j]
            relative_y = essence_icon_y_list[i]

            window = get_active_support_window()
            if window is None:
                logger.info("终末地窗口不在前台，停止基质扫描。")
                self._scanning.clear()
                break

            if not self._scanning.is_set():
                logger.info("基质扫描被中断。")
                break

            click_on_window(window, relative_x, relative_y)

            # 等待短暂时间以确保界面更新
            time.sleep(0.3)

            stats: list[str | None] = []

            for k, roi in enumerate([STATS_0_ROI, STATS_1_ROI, STATS_2_ROI]):
                screenshot_image = screenshot_window(window, roi)
                result, max_val = text_recognizer.recognize_roi(screenshot_image)
                stats.append(result)
                logger.debug(
                    f"第 {i + 1} 行第 {j + 1} 列基质的属性 {k} 识别结果: {result} (置信度: {max_val:.3f})"
                )

            screenshot_image = screenshot_window(window, DEPRECATE_BUTTON_ROI)
            deprecated_str, max_val = icon_recognizer.recognize_roi(screenshot_image)
            deprecated = deprecated_str == "deprecated"
            logger.debug(
                f"第 {i + 1} 行第 {j + 1} 列基质的废弃按钮识别结果: {deprecated_str} (置信度: {max_val:.3f})"
            )

            screenshot_image = screenshot_window(window, LOCK_BUTTON_ROI)
            locked_str, max_val = icon_recognizer.recognize_roi(screenshot_image)
            locked = locked_str == "locked"
            logger.debug(
                f"第 {i + 1} 行第 {j + 1} 列基质的锁定按钮识别结果: {locked_str} (置信度: {max_val:.3f})"
            )

            logger.opt(colors=True).info(
                f"已识别第 {i + 1} 行第 {j + 1} 列的基质，属性: <magenta>{stats}</>, 废弃: <magenta>{deprecated}</>, 锁定: <magenta>{locked}</>"
            )

            for weapon_id, weapon_data in weapons.items():
                if (
                    weapon_data["stats"]["attribute"] == stats[0]
                    and weapon_data["stats"]["secondary"] == stats[1]
                    and weapon_data["stats"]["skill"] == stats[2]
                ):
                    logger.opt(colors=True).success(
                        f"第 {i + 1} 行第 {j + 1} 列的基质是<green><bold><underline>宝贝</></></>，它完美契合武器<bold>{weapon_data['weaponName']}</>。"
                    )
                    if not locked:
                        click_on_window(window, *LOCK_BUTTON_POS)
                    logger.success("给你自动锁上了，记得保管好哦！(*/ω＼*)")
                    break
            else:
                logger.opt(colors=True).success(
                    f"第 {i + 1} 行第 {j + 1} 列的基质是<red><bold><underline>垃圾</></></>，它不匹配任何已实装武器。"
                )
                if locked:
                    click_on_window(window, *LOCK_BUTTON_POS)
                logger.success("给你自动解锁了，可以放心当狗粮用啦！ヾ(≧▽≦*)o")

            # datetime_str = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
            # save_image(
            #     screenshot_image,
            #     screenshot_dir / f"essence_scan_{datetime_str}.png",
            # )

            time.sleep(0.0)

        else:
            # 扫描完成
            logger.info("基质扫描完成。")

    def stop(self) -> None:
        logger.info("停止基质扫描线程...")
        self._scanning.clear()


def on_bracket_left():
    """处理 "[" 键按下事件 - 仅识别不操作"""
    window = get_active_support_window()
    if window is None:
        logger.debug("终末地窗口不在前台，忽略 '[' 键。")
        return
    else:
        logger.info("检测到 '[' 键，开始截图...")

        screenshot_image = screenshot_window(window, STATS_0_ROI)
        save_image(
            text_recognizer.preprocess_roi(screenshot_image),
            screenshot_dir / "attribute_stats_roi.png",
        )
        result, max_val = text_recognizer.recognize_roi(screenshot_image)
        logger.success(f"基础属性识别结果: {result} (置信度: {max_val:.3f})")

        screenshot_image = screenshot_window(window, STATS_1_ROI)
        save_image(
            text_recognizer.preprocess_roi(screenshot_image),
            screenshot_dir / "secondary_stats_roi.png",
        )
        result, max_val = text_recognizer.recognize_roi(screenshot_image)
        logger.success(f"附加属性识别结果: {result} (置信度: {max_val:.3f})")

        screenshot_image = screenshot_window(window, STATS_2_ROI)
        save_image(
            text_recognizer.preprocess_roi(screenshot_image),
            screenshot_dir / "skill_stats_roi.png",
        )
        result, max_val = text_recognizer.recognize_roi(screenshot_image)
        logger.success(f"技能属性识别结果: {result} (置信度: {max_val:.3f})")


def on_bracket_right():
    """处理 "]" 键按下事件 - 切换自动点击"""
    global essence_scanner_thread

    if get_active_support_window() is None:
        logger.debug('终末地窗口不在前台，忽略 "]" 键。')
        return
    else:
        if essence_scanner_thread is None or not essence_scanner_thread.is_alive():
            logger.info('检测到 "]" 键，开始扫描基质')
            essence_scanner_thread = EssenceScanner()
            essence_scanner_thread.start()
            winsound.PlaySound(
                str(enable_sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC
            )
        else:
            logger.info('检测到 "]" 键，停止扫描基质')
            essence_scanner_thread.stop()
            essence_scanner_thread = None
            winsound.PlaySound(
                str(disable_sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC
            )


def on_exit():
    """处理 Alt+Delete 按下事件 - 退出程序"""
    global running, essence_scanner_thread
    logger.info('检测到 "Alt+Delete"，正在退出程序...')
    running = False
    if essence_scanner_thread is not None:
        essence_scanner_thread.stop()
        essence_scanner_thread = None


def main():
    """主函数"""
    global running

    message = """

<white>==================================================</>
<white>终末地基质妙妙小工具已启动</>
<white>==================================================</>
<green><bold>使用前阅读：</></>
  <white>请打开终末地<yellow><bold>贵重品库</></>并切换到<yellow><bold>武器基质</></>页面</>
  <white>在运行过程中，请确保终末地窗口<yellow><bold>置于前台</></></>
<green><bold>功能介绍：</></>
  <white>按 "<green><bold>]</></>" 键开始 / 停止扫描基质</>
  <white>按 "<green><bold>Alt+Delete</></>" 退出程序</>
<white>==================================================</>
"""
    logger.opt(colors=True).success(message)

    logger.info("开始监听热键...")

    # 注册热键
    # keyboard.add_hotkey("[", on_bracket_left)
    keyboard.add_hotkey("]", on_bracket_right)
    keyboard.add_hotkey("alt+delete", on_exit)

    # 保持程序运行
    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        logger.info("程序被中断，正在退出...")
    finally:
        # 清理
        keyboard.unhook_all()
        logger.info("程序已退出")


if __name__ == "__main__":
    main()
