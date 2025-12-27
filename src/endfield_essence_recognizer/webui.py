import os
from pathlib import Path
from threading import Thread
from typing import Any, Literal

import uvicorn
import webview
from dotenv import load_dotenv
from fastapi import APIRouter, Body, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from endfield_essence_recognizer import supported_window_titles
from endfield_essence_recognizer.data import Weapons, weapons
from endfield_essence_recognizer.log import logger

# 加载 .env 文件
load_dotenv()

# 从环境变量读取配置
is_dev = os.getenv("DEV_MODE", "false").lower() in ("true", "1", "yes")
api_host = os.getenv("API_HOST", "127.0.0.1")
api_port = int(os.getenv("API_PORT", "8000"))
dev_url = os.getenv("DEV_URL", "http://localhost:3000")
prod_url = f"http://{api_host}:{api_port}"
webview_url = dev_url if is_dev else prod_url


# 定义API路由
router = APIRouter()


# 定义请求体模型
class TestRequest(BaseModel):
    code: int
    message: str
    data: Any


# @router.api_route(
#     "/{path:path}",
#     methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
# )
# async def proxy_yituliu(path: str, request: Request):
#     import urllib.request

#     url = f"https://ef.yituliu.cn/{path}"
#     query_params = str(request.url.query)
#     if query_params:
#         url += f"?{query_params}"

#     headers = {key: value for key, value in request.headers.items() if key != "host"}

#     with urllib.request.urlopen(
#         urllib.request.Request(
#             url,
#             data=await request.body()
#             if request.method in ("POST", "PUT", "PATCH")
#             else None,
#             headers=headers,
#             method=request.method,
#         )
#     ) as response:
#         content = response.read()
#         return StreamingResponse(
#             content=iter([content]),
#             status_code=response.status,
#             headers=dict(response.getheaders()),
#         )


@router.get("/weapons")
async def get_weapons() -> Weapons:
    return weapons


@router.get("/config")
async def get_config() -> dict[str, Any]:
    from endfield_essence_recognizer.config import config

    return config.model_dump()


@router.post("/config")
async def post_config(new_config: dict[str, Any] = Body()) -> dict[str, Any]:
    from endfield_essence_recognizer.config import config

    config.update_from_dict(new_config)
    config.save()
    return config.model_dump()


@router.get("/screenshot")
async def get_screenshot(
    width: int = 1920,
    height: int = 1080,
    format: Literal["jpg", "jpeg", "png", "webp"] = "jpg",  # noqa: A002
    quality: int = 75,
):
    import base64

    import cv2
    import numpy as np

    from endfield_essence_recognizer.window import (
        get_active_support_window,
        screenshot_window,
    )

    window = get_active_support_window(supported_window_titles)
    if window is None:
        image = np.zeros((height, width, 3), dtype=np.uint8)
    else:
        image = screenshot_window(window)
        image = cv2.resize(image, (width, height))
        logger.success("成功截取终末地窗口截图。")

    if format.lower() == "png":
        encode_param = [
            # cv2.IMWRITE_PNG_COMPRESSION,
            # min(9, max(0, quality // 10)),
        ]  # PNG compression 0-9
        ext = ".png"
        mime_type = "image/png"
    elif format.lower() == "webp":
        encode_param = [cv2.IMWRITE_WEBP_QUALITY, min(100, max(0, quality))]
        ext = ".webp"
        mime_type = "image/webp"
    elif format.lower() == "jpg" or format.lower() == "jpeg":
        encode_param = [cv2.IMWRITE_JPEG_QUALITY, min(100, max(0, quality))]
        ext = ".jpg"
        mime_type = "image/jpeg"

    _, encoded_bytes = cv2.imencode(ext, image, encode_param)

    # 返回 base64 编码的字符串
    base64_string = base64.b64encode(encoded_bytes.tobytes()).decode("utf-8")

    return f"data:{mime_type};base64,{base64_string}"


# 初始化FastAPI应用
app = FastAPI()

# 配置跨域（开发环境需允许Vite的3000端口）
app.add_middleware(
    CORSMiddleware,  # ty:ignore[invalid-argument-type]
    allow_origins=["*"],  # 生产环境可指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(router)

if not is_dev:
    # 挂载静态文件目录（生产环境）
    DIST_DIR = Path("frontend-vuetify/dist")
    if DIST_DIR.exists():
        app.mount(
            "/",
            StaticFiles(directory=DIST_DIR, html=True),
        )
    else:
        logger.error("未找到前端构建文件夹，请先执行前端构建！")


def start_pywebview(url: str):
    """启动 PyWebView 桌面窗口"""
    webview.create_window(
        title=f"终末地基质妙妙小工具 ({url})",
        url=url,
        width=1600,
        height=900,
        resizable=True,
    )
    webview.start()  # 自动选择最佳内核


def start_api_server(host: str, port: int):
    """启动FastAPI服务"""
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "default": {"class": "endfield_essence_recognizer.log.LoguruHandler"}
        },
        "loggers": {
            "uvicorn.error": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO"},
        },
    }
    uvicorn.run(app=app, host=host, port=port, log_config=LOGGING_CONFIG)


if __name__ == "__main__":
    api_thread = Thread(target=start_api_server, args=(api_host, api_port), daemon=True)
    api_thread.start()
    start_pywebview(webview_url)
