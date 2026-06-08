import json
import mimetypes
import os
import re
import sys
import traceback
import uuid
import webbrowser
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests
from PyQt5.QtCore import QObject, QRunnable, QSettings, QSize, Qt, QThreadPool, QTimer, QUrl, pyqtSignal
from PyQt5.QtGui import QDesktopServices, QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "Agnes Agent"
DEFAULT_BASE_URL = "https://apihub.agnes-ai.com"
TEXT_MODEL = "agnes-2.0-flash"
TEXT_CONTEXT_WINDOW = 256000
TEXT_MAX_OUTPUT_TOKENS = 65500
DEFAULT_CONTEXT_COMPRESS_THRESHOLD = 90
DEFAULT_RECENT_CONTEXT_MESSAGES = 24
IMAGE_MODEL_21 = "agnes-image-2.1-flash"
IMAGE_MODEL_20 = "agnes-image-2.0-flash"
IMAGE_MODEL = IMAGE_MODEL_21
IMAGE_MODEL_OPTIONS = (
    ("Agnes Image 2.1 Flash（默认，免费）", IMAGE_MODEL_21),
    ("Agnes Image 2.0 Flash", IMAGE_MODEL_20),
)
VIDEO_MODEL = "agnes-video-v2.0"
HTTP_URL_RE = re.compile(r"https?://[^\s\"'<>]+")
VIDEO_URL_KEYS = (
    "video_url",
    "videoUrl",
    "videoURL",
    "download_url",
    "downloadUrl",
    "output_url",
    "outputUrl",
    "file_url",
    "fileUrl",
)
VIDEO_CONTAINER_KEYS = (
    "data",
    "result",
    "results",
    "output",
    "outputs",
    "video",
    "videos",
    "asset",
    "assets",
    "content",
)
VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".m3u8", ".avi", ".mkv")
SCDN_UPLOAD_ENDPOINT = "https://img.scdn.io/api/v1.php"
CATBOX_UPLOAD_ENDPOINT = "https://catbox.moe/user/api.php"
NULL_POINTER_UPLOAD_ENDPOINT = "https://0x0.st"
TMPFILES_UPLOAD_ENDPOINT = "https://tmpfiles.org/api/v1/upload"
DEFAULT_IMAGE_UPLOAD_ENDPOINT = "auto"
AUTO_IMAGE_UPLOAD_ENDPOINTS = (SCDN_UPLOAD_ENDPOINT, CATBOX_UPLOAD_ENDPOINT, TMPFILES_UPLOAD_ENDPOINT)
IMAGE_UPLOAD_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


def default_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        root = Path(sys.executable).resolve().parent
    else:
        root = Path(__file__).resolve().parent
    return root / "agnes_data"


def legacy_app_data_dir() -> Path:
    base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home()
    return root / "SapiensAI" / "AgnesModelTester"


def normalize_data_dir(value: Any) -> Path:
    text = str(value or "").strip()
    return Path(text).expanduser() if text else default_data_dir()


def sessions_file_path(data_dir: Optional[Any] = None) -> Path:
    return normalize_data_dir(data_dir) / "sessions.json"


def asset_path(filename: str) -> str:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_path / "assets" / filename)


APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #f5f7fb;
    color: #172033;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 13px;
}
QFrame#sidebar {
    background: #0c1530;
    border: 0;
}
QFrame#sidebar QLabel {
    background: transparent;
    color: #dbeafe;
}
QLabel#agentTitle {
    color: white;
    font-size: 21px;
    font-weight: 700;
}
QLabel#mutedSidebar {
    color: #8ea1c7;
    font-size: 12px;
}
QLabel#onlineBadge {
    color: #86efac;
    background: #143527;
    border: 1px solid #23613f;
    border-radius: 10px;
    padding: 3px 8px;
    font-size: 11px;
}
QLabel#modelPill {
    color: #c7d2fe;
    background: #142349;
    border: 1px solid #243967;
    border-radius: 7px;
    padding: 7px 9px;
    font-size: 11px;
}
QLabel#pageTitle {
    color: #111827;
    font-size: 22px;
    font-weight: 700;
}
QLabel#pageSubtitle {
    color: #64748b;
    font-size: 12px;
}
QGroupBox {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    margin-top: 12px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
    color: #334155;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: #475569;
}
QLineEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox, QDoubleSpinBox {
    background: white;
    color: #1e293b;
    border: 1px solid #d8e0ec;
    border-radius: 7px;
    padding: 6px;
    selection-background-color: #6366f1;
}
QTextBrowser {
    background: #fbfdff;
    padding: 10px;
}
QLineEdit:focus, QTextEdit:focus, QTextBrowser:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #818cf8;
}
QPushButton {
    background: white;
    color: #334155;
    border: 1px solid #d8e0ec;
    border-radius: 7px;
    padding: 7px 13px;
}
QPushButton:hover {
    background: #f1f5f9;
    border-color: #a5b4fc;
}
QPushButton:disabled {
    color: #94a3b8;
    background: #f1f5f9;
}
QPushButton#primaryButton {
    color: white;
    background: #5b5ce2;
    border: 1px solid #5b5ce2;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background: #4f46cf;
}
QPushButton#quickButton {
    color: #4f46e5;
    background: #eef2ff;
    border: 1px solid #dbe4ff;
    padding: 5px 10px;
}
QPushButton#sidebarButton {
    color: #dbeafe;
    background: #142349;
    border: 1px solid #243967;
}
QPushButton#sidebarButton:hover {
    background: #1b2e5c;
}
QCheckBox {
    color: #475569;
    spacing: 6px;
}
QFrame#sidebar QCheckBox {
    color: #b8c6e3;
}
QTabWidget::pane {
    border: 0;
    top: -1px;
}
QTabBar::tab {
    color: #64748b;
    background: #eef2f7;
    border: 1px solid #e2e8f0;
    padding: 10px 16px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}
QTabBar::tab:selected {
    color: #4338ca;
    background: white;
    border-bottom-color: white;
    font-weight: 600;
}
QStatusBar {
    background: white;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
}
QSplitter::handle {
    background: #e8edf5;
}
"""

CODEX_STYLESHEET = """
QMainWindow, QWidget {
    background: #151515;
    color: #e7e7e7;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 13px;
}
QFrame#navRail, QFrame#threadRail {
    background: #101010;
    border-right: 1px solid #292929;
}
QFrame#threadRail {
    background: #121212;
}
QFrame#topBar {
    background: #181818;
    border-bottom: 1px solid #2a2a2a;
}
QFrame#composer, QFrame#settingsPanel, QFrame#contentCard {
    background: #202020;
    border: 1px solid #343434;
    border-radius: 13px;
}
QFrame#settingsCard {
    background: #1b1b1b;
    border: 1px solid #303030;
    border-radius: 11px;
}
QLabel {
    color: #dedede;
    background: transparent;
}
QLabel#brandTitle {
    color: #f4f4f4;
    font-size: 15px;
    font-weight: 700;
}
QLabel#paneTitle {
    color: #f3f3f3;
    font-size: 14px;
    font-weight: 600;
}
QLabel#pageTitle {
    color: #f1f1f1;
    font-size: 15px;
    font-weight: 600;
}
QLabel#pageSubtitle, QLabel#muted, QLabel#mutedSidebar {
    color: #8d8d8d;
    font-size: 12px;
}
QLabel#onlineBadge {
    color: #a7f3d0;
    background: #173329;
    border: 1px solid #295545;
    border-radius: 9px;
    padding: 2px 7px;
    font-size: 11px;
}
QLineEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #1d1d1d;
    color: #e7e7e7;
    border: 1px solid #363636;
    border-radius: 7px;
    padding: 6px;
    selection-background-color: #2d6fbb;
}
QTextBrowser {
    background: #151515;
    border: 0;
    padding: 14px;
}
QLineEdit:focus, QTextEdit:focus, QTextBrowser:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #5b8bc0;
}
QPushButton {
    background: transparent;
    color: #cfcfcf;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 7px 10px;
    text-align: left;
}
QPushButton:hover {
    background: #242424;
}
QPushButton:checked, QPushButton#navButton:checked {
    background: #292929;
    color: #ffffff;
}
QPushButton#primaryButton {
    color: #111111;
    background: #eeeeee;
    border: 1px solid #eeeeee;
    border-radius: 15px;
    font-weight: 700;
    padding: 6px 11px;
    text-align: center;
}
QPushButton#primaryButton:hover {
    background: #ffffff;
}
QPushButton#subtleButton, QPushButton#quickButton, QPushButton#sidebarButton {
    color: #bdbdbd;
    background: #202020;
    border: 1px solid #353535;
    padding: 6px 9px;
}
QPushButton#subtleButton:hover, QPushButton#quickButton:hover, QPushButton#sidebarButton:hover {
    background: #292929;
}
QPushButton#threadButton {
    color: #d5d5d5;
    background: transparent;
    border-radius: 7px;
    padding: 8px 9px;
}
QPushButton#threadButton:checked {
    background: #292929;
    color: white;
}
QPushButton:disabled {
    color: #686868;
}
QCheckBox {
    color: #b7b7b7;
    spacing: 6px;
}
QGroupBox {
    background: #1b1b1b;
    border: 1px solid #313131;
    border-radius: 10px;
    margin-top: 12px;
    padding: 12px 10px 10px 10px;
    color: #d6d6d6;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #bdbdbd;
}
QTabWidget::pane {
    background: #191919;
    border: 1px solid #303030;
    border-radius: 7px;
}
QTabBar::tab {
    color: #9c9c9c;
    background: #191919;
    border: 0;
    padding: 8px 12px;
}
QTabBar::tab:selected {
    color: #f0f0f0;
    background: #262626;
}
QScrollArea {
    border: 0;
    background: #151515;
}
QScrollBar:vertical {
    background: #161616;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #484848;
    border-radius: 5px;
    min-height: 28px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QSplitter::handle {
    background: #292929;
}
QStatusBar {
    background: #111111;
    color: #929292;
    border-top: 1px solid #292929;
}
QMenu {
    background: #202020;
    color: #dddddd;
    border: 1px solid #3a3a3a;
    padding: 4px;
}
QMenu::item {
    border-radius: 4px;
    padding: 6px 24px 6px 10px;
}
QMenu::item:selected {
    background: #343434;
}
"""


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, bytes):
        return ""
    return str(value)


def parse_urls(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def append_urls(existing: str, urls: List[str]) -> str:
    values = parse_urls(existing)
    seen = set(values)
    for url in urls:
        if url and url not in seen:
            values.append(url)
            seen.add(url)
    return "\n".join(values)


def is_null_pointer_endpoint(endpoint: str) -> bool:
    cleaned = endpoint.strip().rstrip("/").lower()
    return cleaned in {"https://0x0.st", "http://0x0.st", "https://0x0.black", "http://0x0.black"}


def is_tmpfiles_endpoint(endpoint: str) -> bool:
    return endpoint.strip().rstrip("/").lower() == TMPFILES_UPLOAD_ENDPOINT


def is_scdn_endpoint(endpoint: str) -> bool:
    return endpoint.strip().rstrip("/").lower() == SCDN_UPLOAD_ENDPOINT


def is_auto_upload_endpoint(endpoint: str) -> bool:
    cleaned = endpoint.strip().lower()
    return cleaned in {"", "auto", "自动"}


def tmpfiles_direct_url(url: str) -> str:
    marker = "tmpfiles.org/"
    if marker not in url or "tmpfiles.org/dl/" in url:
        return url
    return "https://tmpfiles.org/dl/" + url.split(marker, 1)[1].lstrip("/")


def upload_image_file(path: str, endpoint: str = DEFAULT_IMAGE_UPLOAD_ENDPOINT) -> str:
    if is_auto_upload_endpoint(endpoint):
        errors = []
        for candidate in AUTO_IMAGE_UPLOAD_ENDPOINTS:
            try:
                return upload_image_file(path, candidate)
            except Exception as exc:
                errors.append(f"{candidate}: {exc}")
        raise RuntimeError("所有内置图床上传均失败：" + "；".join(errors))

    image_path = Path(path)
    if not image_path.exists() or not image_path.is_file():
        raise ValueError(f"文件不存在：{image_path}")
    if image_path.suffix.lower() not in IMAGE_UPLOAD_EXTENSIONS:
        raise ValueError(f"只支持上传图片文件：{image_path.name}")

    mime_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
    with image_path.open("rb") as handle:
        if is_scdn_endpoint(endpoint):
            response = requests.post(
                endpoint,
                data={"cdn_domain": "img.scdn.io", "outputFormat": "auto"},
                files={"image": (image_path.name, handle, mime_type)},
                timeout=120,
            )
        elif is_tmpfiles_endpoint(endpoint):
            response = requests.post(
                endpoint,
                data={"expire": "21600"},
                files={"file": (image_path.name, handle, mime_type)},
                timeout=120,
            )
        elif is_null_pointer_endpoint(endpoint):
            response = requests.post(
                endpoint,
                files={"file": (image_path.name, handle, mime_type)},
                timeout=120,
            )
        else:
            response = requests.post(
                endpoint,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (image_path.name, handle, mime_type)},
                timeout=120,
            )
    if not response.ok:
        raise RuntimeError(f"图床上传失败：HTTP {response.status_code} {response.text[:200]}")
    if is_scdn_endpoint(endpoint):
        try:
            payload = response.json()
            url = str(payload.get("url") or payload.get("data", {}).get("url") or "")
        except (ValueError, AttributeError):
            url = ""
        url = _clean_http_url(url)
    elif is_tmpfiles_endpoint(endpoint):
        try:
            url = str(response.json().get("data", {}).get("url", ""))
        except (ValueError, AttributeError):
            url = ""
        url = tmpfiles_direct_url(_clean_http_url(url))
    else:
        url = _clean_http_url(response.text)
    if not url:
        raise RuntimeError(f"图床没有返回可用 URL：{response.text[:200]}")
    return url


def upload_image_to_catbox(path: str, endpoint: str = CATBOX_UPLOAD_ENDPOINT) -> str:
    return upload_image_file(path, endpoint)


def upload_images_to_catbox(paths: List[str], endpoint: str = DEFAULT_IMAGE_UPLOAD_ENDPOINT) -> List[str]:
    return [upload_image_file(path, endpoint) for path in paths]


def prepare_video_image(path: str, output_dir: Path) -> str:
    source = Path(path)
    image = QImage(str(source))
    if image.isNull():
        raise ValueError(f"无法读取图片：{source}")

    output_dir.mkdir(parents=True, exist_ok=True)
    converted = image.convertToFormat(QImage.Format_RGB888)
    output_path = output_dir / f"{source.stem}-{uuid.uuid4().hex[:8]}.jpg"
    if not converted.save(str(output_path), "JPEG", 92):
        raise RuntimeError(f"图片转存失败：{output_path}")
    return str(output_path)


def optional_int(value: int, enabled: bool) -> Optional[int]:
    return value if enabled else None


def extract_usage(payload: Dict[str, Any]) -> Dict[str, Any]:
    usage = payload.get("usage")
    return usage if isinstance(usage, dict) else {}


def estimate_text_tokens(text: Any) -> int:
    total = 0.0
    for char in str(text or ""):
        code = ord(char)
        if "\u4e00" <= char <= "\u9fff" or "\u3040" <= char <= "\u30ff" or "\uac00" <= char <= "\ud7af":
            total += 1.0
        elif char.isspace():
            total += 0.25
        elif code < 128:
            total += 0.25
        else:
            total += 0.8
    return max(1, int(total) + 1) if text else 0


def message_content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text") or ""))
                elif item.get("type") == "image_url":
                    image_url = item.get("image_url") or {}
                    parts.append(str(image_url.get("url") or ""))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return str(content or "")


def estimate_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    total = 0
    for message in messages:
        total += 6
        total += estimate_text_tokens(message.get("role", ""))
        total += estimate_text_tokens(message_content_text(message.get("content", "")))
    return total + 8


def format_token_count(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return "0"
    if number >= 1000:
        return f"{number:,}"
    return str(number)


def conversation_to_text(messages: List[Dict[str, Any]]) -> str:
    parts = []
    for index, message in enumerate(messages, 1):
        role = str(message.get("role") or "unknown")
        content = message_content_text(message.get("content", ""))
        if content:
            parts.append(f"[{index}] {role}:\n{content}")
    return "\n\n".join(parts)


def extract_chat_content(payload: Dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return str(message.get("content") or "")


def extract_reasoning_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
        return "".join(parts)
    if isinstance(value, dict):
        return str(value.get("text") or value.get("content") or "")
    return ""


def extract_chat_reasoning(payload: Dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    for key in ("reasoning_content", "reasoning", "thinking", "analysis", "reasoning_details"):
        reasoning = extract_reasoning_text(message.get(key))
        if reasoning:
            return reasoning
    return ""


def extract_delta_reasoning(delta: Dict[str, Any]) -> str:
    for key in ("reasoning_content", "reasoning", "thinking", "analysis", "reasoning_details"):
        reasoning = extract_reasoning_text(delta.get(key))
        if reasoning:
            return reasoning
    return ""


def _clean_http_url(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    match = HTTP_URL_RE.search(value.strip())
    if not match:
        return ""
    return match.group(0).rstrip(".,;)]}")


def _looks_like_video_url(url: str) -> bool:
    lower = url.split("?", 1)[0].split("#", 1)[0].lower()
    return lower.endswith(VIDEO_EXTENSIONS) or "/video" in lower or "video_" in lower


def extract_video_url(payload: Any, in_video_context: bool = False) -> str:
    if isinstance(payload, dict):
        for key in VIDEO_URL_KEYS:
            if key not in payload:
                continue
            key_lower = key.lower()
            found = extract_video_url(
                payload[key],
                in_video_context or "video" in key_lower,
            )
            if found:
                return found

        for key, value in payload.items():
            key_lower = str(key).lower()
            key_video_context = in_video_context or "video" in key_lower or key_lower in VIDEO_CONTAINER_KEYS
            if ("url" in key_lower or "uri" in key_lower or "link" in key_lower) and isinstance(value, str):
                candidate = _clean_http_url(value)
                if candidate and (key_video_context or _looks_like_video_url(candidate)):
                    return candidate
            found = extract_video_url(value, key_video_context)
            if found:
                return found
        return ""

    if isinstance(payload, list):
        for item in payload:
            found = extract_video_url(item, in_video_context)
            if found:
                return found
        return ""

    candidate = _clean_http_url(payload)
    if candidate and (in_video_context or _looks_like_video_url(candidate)):
        return candidate
    return ""


class ComposerTextEdit(QTextEdit):
    def __init__(self, submit: Callable[[], None]):
        super().__init__()
        self.submit = submit

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.submit()
            event.accept()
            return
        super().keyPressEvent(event)


def build_image_payload(model: str, prompt: str, size: str, seed: Optional[int], image_urls: List[str]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": model or IMAGE_MODEL,
        "prompt": prompt.strip(),
        "size": size,
    }
    if seed is not None:
        payload["seed"] = seed
    if image_urls:
        payload["extra_body"] = {"image": image_urls, "response_format": "url"}
    else:
        payload["extra_body"] = {"response_format": "url"}
    return payload


def validate_video_frames(num_frames: int) -> None:
    if num_frames > 441 or (num_frames - 1) % 8:
        raise ValueError("视频帧数必须小于等于 441，并满足 8n + 1，例如 81、121、161、241 或 441。")


def build_video_payload(
    prompt: str,
    workflow: str,
    image_urls: List[str],
    width: int,
    height: int,
    num_frames: int,
    frame_rate: int,
    inference_steps: Optional[int],
    seed: Optional[int],
    negative_prompt: str,
) -> Dict[str, Any]:
    validate_video_frames(num_frames)
    if workflow == "image" and not image_urls:
        raise ValueError("图生视频至少需要一个输入图片 URL。")
    if workflow in {"multi", "keyframes"} and len(image_urls) < 2:
        raise ValueError("多图视频或关键帧动画至少需要两个输入图片 URL。")

    payload: Dict[str, Any] = {
        "model": VIDEO_MODEL,
        "prompt": prompt.strip(),
        "width": width,
        "height": height,
        "num_frames": num_frames,
        "frame_rate": frame_rate,
    }
    if inference_steps is not None:
        payload["num_inference_steps"] = inference_steps
    if seed is not None:
        payload["seed"] = seed
    if negative_prompt.strip():
        payload["negative_prompt"] = negative_prompt.strip()
    if workflow == "image":
        payload["image"] = image_urls[0]
    elif workflow in {"multi", "keyframes"}:
        payload["extra_body"] = {"image": image_urls}
        if workflow == "keyframes":
            payload["extra_body"]["mode"] = "keyframes"
    return payload


class ApiError(RuntimeError):
    pass


class AgnesClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip()

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _read_json(response: requests.Response) -> Dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw_response": response.text}
        if not response.ok:
            raise ApiError(f"HTTP {response.status_code}\n{pretty_json(payload)}")
        if not isinstance(payload, dict):
            raise ApiError(f"服务端返回了非对象 JSON：\n{pretty_json(payload)}")
        return payload

    def chat(
        self,
        payload: Dict[str, Any],
        on_chunk: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=180,
            stream=bool(payload.get("stream")),
        )
        if not payload.get("stream"):
            return self._read_json(response)
        if not response.ok:
            return self._read_json(response)

        chunks: List[str] = []
        reasoning_chunks: List[str] = []
        events: List[Dict[str, Any]] = []
        usage: Dict[str, Any] = {}
        for raw_line in response.iter_lines(decode_unicode=False):
            if not raw_line:
                continue
            line = raw_line.decode("utf-8", errors="replace")
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                events.append({"raw": data})
                continue
            events.append(event)
            event_usage = extract_usage(event)
            if event_usage:
                usage = event_usage
            choices = event.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            reasoning = extract_delta_reasoning(delta)
            if reasoning:
                reasoning_chunks.append(reasoning)
                if on_chunk:
                    on_chunk("reasoning", reasoning)
            content = delta.get("content")
            if content:
                chunks.append(content)
                if on_chunk:
                    on_chunk("content", content)
        return {
            "stream": True,
            "content": "".join(chunks),
            "reasoning": "".join(reasoning_chunks),
            "usage": usage,
            "events": events,
        }

    def generate_image(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/v1/images/generations",
            headers=self.headers,
            json=payload,
            timeout=300,
        )
        return self._read_json(response)

    def create_video(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/v1/videos",
            headers=self.headers,
            json=payload,
            timeout=300,
        )
        return self._read_json(response)

    def get_video(self, task_id: str) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/v1/videos/{task_id}",
            headers=self.headers,
            timeout=60,
        )
        return self._read_json(response)


class WorkerSignals(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    chunk = pyqtSignal(str)
    finished = pyqtSignal()


class Worker(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            if os.environ.get("AGNES_GUI_DEBUG"):
                detail += "\n\n" + traceback.format_exc()
            self.signals.error.emit(detail)
        finally:
            self.signals.finished.emit()


class LegacyTextTab(QWidget):
    def __init__(self, window: "MainWindow"):
        super().__init__()
        self.window = window
        self.messages: List[Dict[str, str]] = []
        self.streaming_text = ""
        self.streaming_reasoning = ""

        self.system_prompt = QTextEdit("You are a helpful AI assistant.")
        self.system_prompt.setFixedHeight(68)
        self.user_prompt = QTextEdit()
        self.user_prompt.setPlaceholderText("输入要发送给 Agnes-2.0-Flash 的内容...")
        self.user_prompt.setMinimumHeight(115)
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0, 2)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(0.7)
        self.top_p = QDoubleSpinBox()
        self.top_p.setRange(0, 1)
        self.top_p.setSingleStep(0.05)
        self.top_p.setValue(1.0)
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(1, 65500)
        self.max_tokens.setValue(1024)
        self.stream = QCheckBox("流式输出")
        self.stream.setChecked(True)
        self.send_button = QPushButton("发送")
        self.clear_button = QPushButton("清空对话")
        self.answer = QTextBrowser()
        self.raw = QTextEdit()
        self.raw.setReadOnly(True)

        form = QFormLayout()
        form.addRow("模型", QLabel(TEXT_MODEL))
        form.addRow("System Prompt", self.system_prompt)
        form.addRow("用户消息", self.user_prompt)
        options = QHBoxLayout()
        options.addWidget(QLabel("temperature"))
        options.addWidget(self.temperature)
        options.addWidget(QLabel("top_p"))
        options.addWidget(self.top_p)
        options.addWidget(QLabel("max_tokens"))
        options.addWidget(self.max_tokens)
        options.addWidget(self.stream)
        options.addStretch()
        form.addRow("参数", options)
        buttons = QHBoxLayout()
        buttons.addWidget(self.send_button)
        buttons.addWidget(self.clear_button)
        buttons.addStretch()
        form.addRow("", buttons)

        outputs = QSplitter(Qt.Horizontal)
        outputs.addWidget(self._boxed("对话输出", self.answer))
        outputs.addWidget(self._boxed("原始响应", self.raw))
        outputs.setSizes([650, 450])

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(outputs, 1)

        self.send_button.clicked.connect(self.send)
        self.clear_button.clicked.connect(self.clear)

    @staticmethod
    def _boxed(title: str, widget: QWidget) -> QGroupBox:
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        layout.addWidget(widget)
        return box

    def clear(self) -> None:
        self.messages.clear()
        self.answer.clear()
        self.raw.clear()

    def send(self) -> None:
        user_text = self.user_prompt.toPlainText().strip()
        if not user_text:
            self.window.warn("请输入用户消息。")
            return
        try:
            client = self.window.client()
        except ValueError as exc:
            self.window.warn(str(exc))
            return

        request_messages: List[Dict[str, str]] = []
        if self.system_prompt.toPlainText().strip():
            request_messages.append({"role": "system", "content": self.system_prompt.toPlainText().strip()})
        request_messages.extend(
            {"role": message["role"], "content": message.get("content", "")}
            for message in self.messages
        )
        request_messages.append({"role": "user", "content": user_text})
        payload = {
            "model": TEXT_MODEL,
            "messages": request_messages,
            "temperature": self.temperature.value(),
            "top_p": self.top_p.value(),
            "max_tokens": self.max_tokens.value(),
            "stream": self.stream.isChecked(),
        }
        self.messages.append({"role": "user", "content": user_text})
        self.answer.append(f"<b>你：</b><br>{self._html(user_text)}<br>")
        self.user_prompt.clear()
        self.streaming_text = ""
        self.send_button.setEnabled(False)

        on_chunk = self._on_stream_chunk if self.stream.isChecked() else None
        self.window.start_job(
            lambda: client.chat(payload, on_chunk),
            self._on_result,
            self._on_error,
            on_chunk_signal=self._append_stream_chunk if on_chunk else None,
            on_finished=lambda: self.send_button.setEnabled(True),
        )

    def _on_stream_chunk(self, text: str) -> None:
        self.window.emit_chunk(text)

    def _append_stream_chunk(self, text: str) -> None:
        if not self.streaming_text:
            self.answer.append("<b>Agnes：</b><br>")
        self.streaming_text += text
        self.answer.moveCursor(self.answer.textCursor().End)
        self.answer.insertPlainText(text)

    def _on_result(self, result: Dict[str, Any]) -> None:
        self.raw.setPlainText(pretty_json(result))
        if result.get("stream"):
            content = result.get("content", "")
            self.answer.append("<br>")
        else:
            content = (
                result.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            self.answer.append(f"<b>Agnes：</b><br>{self._html(content)}<br>")
        self.messages.append({"role": "assistant", "content": content})

    def _on_error(self, message: str) -> None:
        self.raw.setPlainText(message)
        self.answer.append(
            f'<div style="margin:14px 90px 14px 0; padding:10px 12px; border-radius:9px; '
            f'background:#321f1f; color:#f3b6b6;"><b>请求失败</b><br>{self._html(message)}</div>'
        )
        self.window.warn(message)

    @staticmethod
    def _html(text: str) -> str:
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )


class LegacyAgentTextTab(QWidget):
    def __init__(self, window: "MainWindow"):
        super().__init__()
        self.window = window
        self.messages: List[Dict[str, str]] = []
        self.streaming_text = ""

        self.system_prompt = QTextEdit(
            "You are Agnes, a capable AI agent. Be clear, practical, and proactive. "
            "Help the user complete tasks with concise, useful answers."
        )
        self.system_prompt.setFixedHeight(58)
        self.user_prompt = QTextEdit()
        self.user_prompt.setPlaceholderText("给 Agnes 发消息。可以提问、写作、分析或拆解任务...")
        self.user_prompt.setFixedHeight(92)
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0, 2)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(0.7)
        self.top_p = QDoubleSpinBox()
        self.top_p.setRange(0, 1)
        self.top_p.setSingleStep(0.05)
        self.top_p.setValue(1.0)
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(1, 65500)
        self.max_tokens.setValue(1024)
        self.stream = QCheckBox("流式输出")
        self.stream.setChecked(True)
        self.send_button = QPushButton("发送给 Agnes")
        self.send_button.setObjectName("primaryButton")
        self.clear_button = QPushButton("清空对话")
        self.answer = QTextBrowser()
        self.raw = QTextEdit()
        self.raw.setReadOnly(True)
        self._show_welcome()

        title = QLabel("和 Agnes 对话")
        title.setObjectName("pageTitle")
        subtitle = QLabel("使用 Agnes-2.0-Flash 进行问答、推理、写作和任务规划。对话历史会自动保留。")
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        quick_prompts = QHBoxLayout()
        quick_prompts.addWidget(QLabel("快捷开始"))
        self._add_quick_prompt(quick_prompts, "整理思路", "请帮我把下面的想法整理成清晰的执行计划：")
        self._add_quick_prompt(quick_prompts, "写一份方案", "请为下面的目标写一份简洁、可执行的方案：")
        self._add_quick_prompt(quick_prompts, "分析问题", "请分析下面的问题，给出关键原因和建议：")
        quick_prompts.addStretch()

        composer = QGroupBox("新消息")
        composer_layout = QVBoxLayout(composer)
        composer_layout.addWidget(self.user_prompt)
        composer_buttons = QHBoxLayout()
        composer_buttons.addWidget(self.clear_button)
        composer_buttons.addStretch()
        composer_buttons.addWidget(self.send_button)
        composer_layout.addLayout(composer_buttons)

        settings = QGroupBox("Agent 设置")
        form = QFormLayout(settings)
        form.addRow("当前模型", QLabel(TEXT_MODEL))
        form.addRow("System Prompt", self.system_prompt)
        options = QHBoxLayout()
        options.addWidget(QLabel("temperature"))
        options.addWidget(self.temperature)
        options.addWidget(QLabel("top_p"))
        options.addWidget(self.top_p)
        options.addWidget(QLabel("max_tokens"))
        options.addWidget(self.max_tokens)
        options.addWidget(self.stream)
        options.addStretch()
        form.addRow("参数", options)

        outputs = QSplitter(Qt.Horizontal)
        outputs.addWidget(self._boxed("Agnes 对话", self.answer))
        detail_tabs = QTabWidget()
        detail_tabs.addTab(settings, "Agent 设置")
        detail_tabs.addTab(self.raw, "原始响应")
        outputs.addWidget(detail_tabs)
        outputs.setSizes([760, 340])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(quick_prompts)
        layout.addWidget(outputs, 1)
        layout.addWidget(composer)

        self.send_button.clicked.connect(self.send)
        self.clear_button.clicked.connect(self.clear)

    def _show_welcome(self) -> None:
        self.answer.setHtml(
            """
            <div style="padding:18px; color:#334155;">
              <div style="font-size:20px; font-weight:700; color:#1e1b4b;">你好，我是 Agnes。</div>
              <p style="line-height:1.7; color:#64748b;">
                我可以陪你分析问题、整理计划、完成写作，也可以在另外两个工作区生成图像和视频。
                从下面的输入框开始，或者选择一个快捷提示。
              </p>
            </div>
            """
        )

    def _add_quick_prompt(self, layout: QHBoxLayout, label: str, prompt: str) -> None:
        button = QPushButton(label)
        button.setObjectName("quickButton")
        button.clicked.connect(lambda _checked=False, text=prompt: self.user_prompt.setPlainText(text))
        layout.addWidget(button)

    @staticmethod
    def _boxed(title: str, widget: QWidget) -> QGroupBox:
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        layout.addWidget(widget)
        return box

    def clear(self) -> None:
        self.messages.clear()
        self._show_welcome()
        self.raw.clear()

    def send(self) -> None:
        user_text = self.user_prompt.toPlainText().strip()
        if not user_text:
            self.window.warn("请输入用户消息。")
            return
        try:
            client = self.window.client()
        except ValueError as exc:
            self.window.warn(str(exc))
            return

        request_messages: List[Dict[str, str]] = []
        if self.system_prompt.toPlainText().strip():
            request_messages.append({"role": "system", "content": self.system_prompt.toPlainText().strip()})
        request_messages.extend(
            {"role": message["role"], "content": message.get("content", "")}
            for message in self.messages
        )
        request_messages.append({"role": "user", "content": user_text})
        payload = {
            "model": TEXT_MODEL,
            "messages": request_messages,
            "temperature": self.temperature.value(),
            "top_p": self.top_p.value(),
            "max_tokens": self.max_tokens.value(),
            "stream": self.stream.isChecked(),
        }
        self.messages.append({"role": "user", "content": user_text})
        self.answer.append(
            f'<div style="margin:10px 0;"><b style="color:#4f46e5;">你</b>'
            f'<div style="margin-top:4px;">{self._html(user_text)}</div></div>'
        )
        self.user_prompt.clear()
        self.streaming_text = ""
        self.send_button.setEnabled(False)

        on_chunk = self._on_stream_chunk if self.stream.isChecked() else None
        self.window.start_job(
            lambda: client.chat(payload, on_chunk),
            self._on_result,
            self._on_error,
            on_chunk_signal=self._append_stream_chunk if on_chunk else None,
            on_finished=lambda: self.send_button.setEnabled(True),
        )

    def _on_stream_chunk(self, text: str) -> None:
        self.window.emit_chunk(text)

    def _append_stream_chunk(self, text: str) -> None:
        if not self.streaming_text:
            self.answer.append('<div style="margin:10px 0;"><b style="color:#0891b2;">Agnes</b><div style="margin-top:4px;">')
        self.streaming_text += text
        self.answer.moveCursor(self.answer.textCursor().End)
        self.answer.insertPlainText(text)

    def _on_result(self, result: Dict[str, Any]) -> None:
        self.raw.setPlainText(pretty_json(result))
        if result.get("stream"):
            content = result.get("content", "")
            self.answer.append("</div></div>")
        else:
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            self.answer.append(
                f'<div style="margin:10px 0;"><b style="color:#0891b2;">Agnes</b>'
                f'<div style="margin-top:4px;">{self._html(content)}</div></div>'
            )
        self.messages.append({"role": "assistant", "content": content})

    def _on_error(self, message: str) -> None:
        self.raw.setPlainText(message)
        self.window.warn(message)

    @staticmethod
    def _html(text: str) -> str:
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )


class TextTab(QWidget):
    def __init__(self, window: "MainWindow"):
        super().__init__()
        self.window = window
        self.messages: List[Dict[str, Any]] = []
        self.streaming_text = ""
        self.streaming_reasoning = ""
        self.context_summary = ""
        self.summary_message_count = 0
        self.last_usage: Dict[str, Any] = {}
        self.last_context_estimate: Dict[str, Any] = {}
        self.last_compression_notice = ""

        self.answer = QTextBrowser()
        self.answer.setOpenExternalLinks(True)
        self._show_welcome()

        self.thinking_panel = QFrame()
        self.thinking_panel.setObjectName("settingsPanel")
        thinking_layout = QVBoxLayout(self.thinking_panel)
        thinking_layout.setContentsMargins(10, 8, 10, 8)
        thinking_layout.setSpacing(5)
        self.thinking_toggle = QPushButton("▸ Thinking")
        self.thinking_toggle.setObjectName("subtleButton")
        self.thinking_toggle.setCheckable(True)
        self.thinking_view = QTextBrowser()
        self.thinking_view.setMaximumHeight(170)
        self.thinking_view.hide()
        self.thinking_toggle.toggled.connect(self.thinking_view.setVisible)
        thinking_layout.addWidget(self.thinking_toggle)
        thinking_layout.addWidget(self.thinking_view)
        self.thinking_panel.hide()

        self.user_prompt = ComposerTextEdit(self.send)
        self.user_prompt.setPlaceholderText("向 Agnes 描述任务，或直接开始一次对话...  Enter 发送，Shift+Enter 换行")
        self.user_prompt.setFixedHeight(92)
        self.system_prompt = QTextEdit(
            "You are Agnes, a capable AI agent. Be clear, practical, and proactive. "
            "Help the user complete tasks with concise, useful answers."
        )
        self.system_prompt.setFixedHeight(62)
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0, 2)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(0.7)
        self.top_p = QDoubleSpinBox()
        self.top_p.setRange(0, 1)
        self.top_p.setSingleStep(0.05)
        self.top_p.setValue(1.0)
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(1, TEXT_MAX_OUTPUT_TOKENS)
        self.max_tokens.setValue(1024)
        self.stream = QCheckBox("流式输出")
        self.stream.setChecked(True)
        self.thinking_mode = QComboBox()
        self.thinking_mode.addItem("自动", "auto")
        self.thinking_mode.addItem("开启", "on")
        self.thinking_mode.addItem("关闭", "off")
        self.auto_compress = QCheckBox("上下文接近上限时自动压缩")
        self.auto_compress.setChecked(True)
        self.compress_threshold = QSpinBox()
        self.compress_threshold.setRange(50, 99)
        self.compress_threshold.setValue(DEFAULT_CONTEXT_COMPRESS_THRESHOLD)
        self.recent_context_messages = QSpinBox()
        self.recent_context_messages.setRange(4, 80)
        self.recent_context_messages.setValue(DEFAULT_RECENT_CONTEXT_MESSAGES)
        self.raw = QTextEdit()
        self.raw.setReadOnly(True)

        self.send_button = QPushButton("↑")
        self.send_button.setObjectName("primaryButton")
        self.send_button.setFixedSize(34, 34)
        self.clear_button = QPushButton("＋ 新对话")
        self.clear_button.setObjectName("subtleButton")
        self.settings_button = QPushButton("⚙  模型设置")
        self.settings_button.setObjectName("subtleButton")
        self.settings_button.setCheckable(True)
        self.context_button = QPushButton("上下文")
        self.context_button.setObjectName("subtleButton")
        self.context_button.setCheckable(True)
        self.debug_button = QPushButton("查看原始响应")
        self.debug_button.setObjectName("subtleButton")
        self.debug_button.setCheckable(True)

        composer = QFrame()
        composer.setObjectName("composer")
        composer_layout = QVBoxLayout(composer)
        composer_layout.setContentsMargins(12, 10, 12, 10)
        composer_layout.setSpacing(6)
        composer_layout.addWidget(self.user_prompt)
        composer_actions = QHBoxLayout()
        composer_actions.addWidget(self.settings_button)
        composer_actions.addWidget(self.context_button)
        composer_actions.addWidget(self.debug_button)
        composer_actions.addStretch()
        composer_actions.addWidget(QLabel(TEXT_MODEL))
        composer_actions.addWidget(self.send_button)
        composer_layout.addLayout(composer_actions)

        self.settings_panel = QFrame()
        self.settings_panel.setObjectName("settingsPanel")
        settings_layout = QFormLayout(self.settings_panel)
        settings_layout.setContentsMargins(12, 10, 12, 10)
        settings_layout.addRow("System Prompt", self.system_prompt)
        params = QHBoxLayout()
        params.addWidget(QLabel("temperature"))
        params.addWidget(self.temperature)
        params.addWidget(QLabel("top_p"))
        params.addWidget(self.top_p)
        params.addWidget(QLabel("max_tokens"))
        params.addWidget(self.max_tokens)
        params.addWidget(self.stream)
        params.addStretch()
        settings_layout.addRow("生成参数", params)
        thinking_row = QHBoxLayout()
        thinking_row.addWidget(QLabel("Thinking"))
        thinking_row.addWidget(self.thinking_mode)
        thinking_row.addStretch()
        settings_layout.addRow("思考模式", thinking_row)
        compress_row = QHBoxLayout()
        compress_row.addWidget(self.auto_compress)
        compress_row.addWidget(QLabel("阈值"))
        compress_row.addWidget(self.compress_threshold)
        compress_row.addWidget(QLabel("%"))
        compress_row.addWidget(QLabel("保留最近消息"))
        compress_row.addWidget(self.recent_context_messages)
        compress_row.addStretch()
        settings_layout.addRow("上下文", compress_row)
        self.settings_panel.hide()

        self.context_panel = QFrame()
        self.context_panel.setObjectName("settingsPanel")
        context_layout = QVBoxLayout(self.context_panel)
        context_layout.setContentsMargins(10, 10, 10, 10)
        self.context_view = QTextBrowser()
        self.context_view.setMaximumHeight(220)
        context_layout.addWidget(self.context_view)
        self.context_panel.hide()

        self.raw_panel = QFrame()
        self.raw_panel.setObjectName("settingsPanel")
        raw_layout = QVBoxLayout(self.raw_panel)
        raw_layout.setContentsMargins(10, 10, 10, 10)
        raw_layout.addWidget(self.raw)
        self.raw_panel.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.thinking_panel)
        layout.addWidget(self.answer, 1)
        layout.addWidget(self.settings_panel)
        layout.addWidget(self.context_panel)
        layout.addWidget(self.raw_panel)
        layout.addWidget(composer)

        self.send_button.clicked.connect(self.send)
        self.clear_button.clicked.connect(self.window.new_chat)
        self.settings_button.toggled.connect(self.settings_panel.setVisible)
        self.context_button.toggled.connect(self.context_panel.setVisible)
        self.debug_button.toggled.connect(self.raw_panel.setVisible)
        self.user_prompt.textChanged.connect(self._update_context_panel)
        self.max_tokens.valueChanged.connect(lambda _value: self._update_context_panel())
        self.compress_threshold.valueChanged.connect(lambda _value: self._update_context_panel())
        self.recent_context_messages.valueChanged.connect(lambda _value: self._update_context_panel())
        self.auto_compress.toggled.connect(lambda _checked: self._update_context_panel())
        self.thinking_mode.currentIndexChanged.connect(lambda _index: self._update_context_panel())
        self._update_context_panel()

    def _show_welcome(self) -> None:
        self.answer.setHtml(self._welcome_html())

    @staticmethod
    def _welcome_html() -> str:
        return """
            <div style="max-width:760px; margin:44px auto; color:#d7d7d7;">
              <div style="font-size:24px; font-weight:700; color:#f5f5f5;">开始使用 Agnes</div>
              <p style="font-size:14px; line-height:1.8; color:#a8a8a8;">
                Agnes 是一个轻量多模态 Agent。你可以从普通对话开始，也可以切换到图像或视频工作区完成创作任务。
              </p>
              <div style="margin-top:22px; color:#c9c9c9;"><b>可以试试：</b></div>
              <p style="line-height:1.9; color:#969696;">
                · 将一个模糊想法整理成可执行计划<br>
                · 分析一段需求并给出实现步骤<br>
                · 起草文案、邮件或产品说明
              </p>
            </div>
            """

    def load_session_state(self, session: Dict[str, Any]) -> None:
        self.context_summary = str(session.get("context_summary") or "")
        self.summary_message_count = int(session.get("summary_message_count") or 0)
        self.last_usage = session.get("last_usage") if isinstance(session.get("last_usage"), dict) else {}
        self.last_context_estimate = (
            session.get("last_context_estimate") if isinstance(session.get("last_context_estimate"), dict) else {}
        )
        self.last_compression_notice = str(session.get("last_compression_notice") or "")
        self.load_messages(session.setdefault("messages", []))

    def load_messages(self, messages: List[Dict[str, Any]]) -> None:
        self.messages = messages
        self.streaming_text = ""
        self.streaming_reasoning = ""
        self.raw.clear()
        self._render_conversation()
        self._update_context_panel()

    def export_context_state(self) -> Dict[str, Any]:
        return {
            "context_summary": self.context_summary,
            "summary_message_count": self.summary_message_count,
            "last_usage": self.last_usage,
            "last_context_estimate": self.last_context_estimate,
            "last_compression_notice": self.last_compression_notice,
        }

    def _render_conversation(self, error: str = "") -> None:
        if not self.messages and not self.streaming_text and not error:
            self._show_welcome()
            return
        parts = ['<div style="max-width:860px; margin:18px auto; color:#dddddd;">']
        for message in self.messages:
            content = self._html(message.get("content", ""))
            if message.get("role") == "user":
                parts.append(
                    '<div style="margin:14px 0 14px 90px; padding:12px 14px; border-radius:12px; '
                    f'background:#262626; color:#eeeeee;"><b>你</b><br>{content}</div>'
                )
            else:
                parts.append(f'<div style="margin:14px 90px 14px 0;"><b>Agnes</b><br>{content}</div>')
        if self.streaming_text:
            parts.append(
                '<div style="margin:14px 90px 14px 0;"><b>Agnes</b><br>'
                f'{self._html(self.streaming_text)}</div>'
            )
        if error:
            parts.append(
                '<div style="margin:14px 90px 14px 0; padding:10px 12px; border-radius:9px; '
                f'background:#321f1f; color:#f3b6b6;"><b>请求失败</b><br>{self._html(error)}</div>'
            )
        parts.append("</div>")
        self.answer.setHtml("".join(parts))
        self.answer.verticalScrollBar().setValue(self.answer.verticalScrollBar().maximum())
        self._update_thinking_panel()

    def _update_thinking_panel(self) -> None:
        reasoning = self.streaming_reasoning
        if not reasoning:
            for message in reversed(self.messages):
                reasoning = str(message.get("reasoning") or "")
                if reasoning:
                    break
        if not reasoning:
            self.thinking_panel.hide()
            self.thinking_view.clear()
            return
        first_show = not self.thinking_panel.isVisible()
        self.thinking_panel.show()
        self.thinking_view.setPlainText(reasoning)
        if self.streaming_reasoning:
            self.thinking_toggle.setText("▾ Thinking...")
            if first_show:
                self.thinking_toggle.setChecked(True)
        else:
            self.thinking_toggle.setText("▸ 已完成思考")
            self.thinking_toggle.setChecked(False)

    def _build_request_messages(
        self,
        history: List[Dict[str, Any]],
        user_text: str,
        system_prompt: str,
        context_summary: str,
        summary_message_count: int,
    ) -> List[Dict[str, str]]:
        request_messages: List[Dict[str, str]] = []
        if system_prompt.strip():
            request_messages.append({"role": "system", "content": system_prompt.strip()})
        if context_summary.strip():
            request_messages.append(
                {
                    "role": "system",
                    "content": (
                        "以下是本会话早期上下文的压缩摘要。请把它作为长期记忆使用，但优先遵循用户的最新消息。\n\n"
                        + context_summary.strip()
                    ),
                }
            )
        start = max(0, min(summary_message_count, len(history)))
        request_messages.extend(
            {"role": str(message.get("role") or "user"), "content": message_content_text(message.get("content", ""))}
            for message in history[start:]
            if message.get("role") in {"user", "assistant", "system"}
        )
        request_messages.append({"role": "user", "content": user_text})
        return request_messages

    def _should_enable_thinking(self, user_text: str, mode: Optional[str] = None) -> bool:
        mode = str(mode or self.thinking_mode.currentData() or "auto")
        if mode == "on":
            return True
        if mode == "off":
            return False
        keywords = (
            "代码",
            "编程",
            "调试",
            "报错",
            "错误",
            "分析",
            "推理",
            "规划",
            "计划",
            "方案",
            "重构",
            "实现",
            "agent",
            "debug",
            "code",
            "reason",
            "analyze",
            "plan",
            "implement",
            "refactor",
        )
        lowered = user_text.lower()
        return any(keyword in lowered for keyword in keywords)

    def _context_estimate(
        self,
        request_messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        threshold: Optional[int] = None,
    ) -> Dict[str, Any]:
        prompt_tokens = estimate_messages_tokens(request_messages)
        reserved_output = int(max_tokens if max_tokens is not None else self.max_tokens.value())
        total = prompt_tokens + reserved_output
        percent = int(total * 100 / TEXT_CONTEXT_WINDOW)
        return {
            "prompt_tokens_estimate": prompt_tokens,
            "reserved_output_tokens": reserved_output,
            "total_tokens_estimate": total,
            "context_window": TEXT_CONTEXT_WINDOW,
            "percent": percent,
            "threshold": int(threshold if threshold is not None else self.compress_threshold.value()),
        }

    def _current_request_preview(self) -> List[Dict[str, str]]:
        return self._build_request_messages(
            self.messages,
            self.user_prompt.toPlainText().strip(),
            self.system_prompt.toPlainText(),
            self.context_summary,
            self.summary_message_count,
        )

    def _update_context_panel(self) -> None:
        request_messages = self._current_request_preview()
        estimate = self._context_estimate(request_messages)
        prompt_estimate = estimate["prompt_tokens_estimate"]
        total_estimate = estimate["total_tokens_estimate"]
        percent = estimate["percent"]
        self.context_button.setText(
            f"上下文 {format_token_count(total_estimate)} / {format_token_count(TEXT_CONTEXT_WINDOW)}"
        )
        usage_html = "暂无服务端 usage。发送一次消息后会显示实际 token。"
        if self.last_usage:
            usage_html = (
                f"上次实际输入：{format_token_count(self.last_usage.get('prompt_tokens'))} tokens<br>"
                f"上次实际输出：{format_token_count(self.last_usage.get('completion_tokens'))} tokens<br>"
                f"上次总量：{format_token_count(self.last_usage.get('total_tokens'))} tokens"
            )
        summary_preview = self._html(self.context_summary[:1200]) if self.context_summary else "暂无压缩摘要。"
        thinking_label = self.thinking_mode.currentText()
        notice = self._html(self.last_compression_notice) if self.last_compression_notice else "暂无自动压缩记录。"
        recent_start = max(0, min(self.summary_message_count, len(self.messages)))
        html = f"""
        <div style="color:#d7d7d7; line-height:1.65;">
          <b>当前上下文</b><br>
          估算输入：{format_token_count(prompt_estimate)} tokens<br>
          预留输出：{format_token_count(self.max_tokens.value())} tokens<br>
          估算总量：{format_token_count(total_estimate)} / {format_token_count(TEXT_CONTEXT_WINDOW)} tokens（约 {percent}%）<br>
          自动压缩：{"开启" if self.auto_compress.isChecked() else "关闭"}，阈值 {self.compress_threshold.value()}%<br>
          Thinking：{self._html(thinking_label)}<br>
          最近发送上下文：{len(self.messages) - recent_start} 条消息，已摘要覆盖：{self.summary_message_count} 条消息
          <hr>
          <b>服务端 usage</b><br>{usage_html}
          <hr>
          <b>压缩状态</b><br>{notice}
          <hr>
          <b>长期摘要预览</b><br>
          <pre style="white-space:pre-wrap; color:#bdbdbd;">{summary_preview}</pre>
        </div>
        """
        self.context_view.setHtml(html)

    def _build_chat_payload(self, request_messages: List[Dict[str, str]], user_text: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": TEXT_MODEL,
            "messages": request_messages,
            "temperature": settings["temperature"],
            "top_p": settings["top_p"],
            "max_tokens": settings["max_tokens"],
            "stream": settings["stream"],
        }
        if self._should_enable_thinking(user_text, settings["thinking_mode"]):
            payload["chat_template_kwargs"] = {"enable_thinking": True}
        return payload

    def _compress_context_if_needed(
        self,
        client: AgnesClient,
        history: List[Dict[str, Any]],
        user_text: str,
        system_prompt: str,
        context_summary: str,
        summary_message_count: int,
        settings: Dict[str, Any],
    ) -> Dict[str, Any]:
        request_messages = self._build_request_messages(history, user_text, system_prompt, context_summary, summary_message_count)
        estimate = self._context_estimate(request_messages, settings["max_tokens"], settings["compress_threshold"])
        threshold = settings["compress_threshold"]
        if not settings["auto_compress"] or estimate["percent"] < threshold:
            return {
                "request_messages": request_messages,
                "context_summary": context_summary,
                "summary_message_count": summary_message_count,
                "compressed": False,
                "compression_usage": {},
                "context_estimate": estimate,
            }

        recent_count = max(4, settings["recent_context_messages"])
        target_count = max(summary_message_count, len(history) - recent_count)
        if target_count <= summary_message_count:
            return {
                "request_messages": request_messages,
                "context_summary": context_summary,
                "summary_message_count": summary_message_count,
                "compressed": False,
                "compression_usage": {},
                "context_estimate": estimate,
            }

        messages_to_summarize = history[summary_message_count:target_count]
        compression_messages = [
            {
                "role": "system",
                "content": (
                    "You are a context compression assistant for an AI IDE chat. "
                    "Create a compact Chinese summary that preserves user goals, decisions, constraints, file paths, "
                    "URLs, API details, errors, pending tasks, and important preferences. Do not include private API keys. "
                    "Do not mention irrelevant small talk. Return only the updated summary."
                ),
            },
            {
                "role": "user",
                "content": (
                    "已有长期摘要：\n"
                    f"{context_summary or '（无）'}\n\n"
                    "请把下面这些较早对话并入长期摘要：\n"
                    f"{conversation_to_text(messages_to_summarize)}"
                ),
            },
        ]
        compression_payload = {
            "model": TEXT_MODEL,
            "messages": compression_messages,
            "temperature": 0.2,
            "max_tokens": 4096,
            "stream": False,
        }
        compression_result = client.chat(compression_payload, None)
        new_summary = extract_chat_content(compression_result).strip()
        if not new_summary:
            raise RuntimeError("自动压缩上下文失败：模型没有返回摘要。")
        request_messages = self._build_request_messages(history, user_text, system_prompt, new_summary, target_count)
        estimate = self._context_estimate(request_messages, settings["max_tokens"], settings["compress_threshold"])
        if estimate["total_tokens_estimate"] >= TEXT_CONTEXT_WINDOW:
            raise RuntimeError("当前输入过大，压缩历史后仍可能超过 256K 上下文。请缩短本次输入后重试。")
        return {
            "request_messages": request_messages,
            "context_summary": new_summary,
            "summary_message_count": target_count,
            "compressed": True,
            "compression_usage": extract_usage(compression_result),
            "context_estimate": estimate,
        }

    def _run_chat_job(
        self,
        client: AgnesClient,
        history: List[Dict[str, Any]],
        user_text: str,
        system_prompt: str,
        context_summary: str,
        summary_message_count: int,
        settings: Dict[str, Any],
        on_chunk: Optional[Callable[[str, str], None]],
    ) -> Dict[str, Any]:
        context_state = self._compress_context_if_needed(
            client,
            history,
            user_text,
            system_prompt,
            context_summary,
            summary_message_count,
            settings,
        )
        payload = self._build_chat_payload(context_state["request_messages"], user_text, settings)
        chat_result = client.chat(payload, on_chunk)
        return {
            "chat_result": chat_result,
            **context_state,
        }

    def clear(self) -> None:
        self.context_summary = ""
        self.summary_message_count = 0
        self.last_usage = {}
        self.last_context_estimate = {}
        self.last_compression_notice = ""
        self.load_messages([])
        self.window.statusBar().showMessage("已创建新对话")

    def send(self) -> None:
        if not self.send_button.isEnabled():
            return
        user_text = self.user_prompt.toPlainText().strip()
        if not user_text:
            self.window.warn("请输入用户消息。")
            return
        try:
            client = self.window.client()
        except ValueError as exc:
            self.window.warn(str(exc))
            return
        history = [dict(message) for message in self.messages]
        settings = {
            "temperature": self.temperature.value(),
            "top_p": self.top_p.value(),
            "max_tokens": self.max_tokens.value(),
            "stream": self.stream.isChecked(),
            "thinking_mode": str(self.thinking_mode.currentData() or "auto"),
            "auto_compress": self.auto_compress.isChecked(),
            "compress_threshold": self.compress_threshold.value(),
            "recent_context_messages": self.recent_context_messages.value(),
        }
        system_prompt = self.system_prompt.toPlainText()
        context_summary = self.context_summary
        summary_message_count = self.summary_message_count
        preview_messages = self._build_request_messages(history, user_text, system_prompt, context_summary, summary_message_count)
        preview_estimate = self._context_estimate(preview_messages, settings["max_tokens"], settings["compress_threshold"])
        if preview_estimate["total_tokens_estimate"] >= TEXT_CONTEXT_WINDOW and not settings["auto_compress"]:
            self.window.warn("当前上下文可能超过 256K，请开启自动压缩或缩短历史。")
            return
        if settings["auto_compress"] and preview_estimate["percent"] >= settings["compress_threshold"]:
            self.window.statusBar().showMessage("上下文接近上限，正在自动压缩后继续发送...")
        self.messages.append({"role": "user", "content": user_text})
        self.window.on_conversation_changed(user_text)
        self._render_conversation()
        self.user_prompt.clear()
        self.user_prompt.setEnabled(False)
        self.streaming_text = ""
        self.streaming_reasoning = ""
        self.send_button.setEnabled(False)
        on_chunk = self._on_stream_chunk if settings["stream"] else None
        self.window.start_job(
            lambda: self._run_chat_job(
                client,
                history,
                user_text,
                system_prompt,
                context_summary,
                summary_message_count,
                settings,
                on_chunk,
            ),
            self._on_result,
            self._on_error,
            on_chunk_signal=self._append_stream_chunk if on_chunk else None,
            on_finished=self._send_finished,
        )

    def _on_stream_chunk(self, kind: str, text: str) -> None:
        self.window.emit_chunk(kind, text)

    def _append_stream_chunk(self, kind: str, text: str) -> None:
        if kind == "reasoning":
            self.streaming_reasoning += text
        else:
            self.streaming_text += text
        self._render_conversation()

    def _on_result(self, result: Dict[str, Any]) -> None:
        chat_result = result.get("chat_result") if isinstance(result.get("chat_result"), dict) else result
        if result.get("compressed"):
            self.context_summary = str(result.get("context_summary") or "")
            self.summary_message_count = int(result.get("summary_message_count") or self.summary_message_count)
            self.last_compression_notice = (
                f"已自动压缩早期上下文，摘要覆盖前 {self.summary_message_count} 条消息。"
            )
            self.window.statusBar().showMessage(self.last_compression_notice, 6000)
        else:
            self.context_summary = str(result.get("context_summary") or self.context_summary)
            self.summary_message_count = int(result.get("summary_message_count") or self.summary_message_count)
        self.last_context_estimate = result.get("context_estimate") if isinstance(result.get("context_estimate"), dict) else {}
        usage = extract_usage(chat_result)
        self.last_usage = usage
        self.raw.setPlainText(pretty_json(result))
        if chat_result.get("stream"):
            content = chat_result.get("content", "")
            reasoning = chat_result.get("reasoning", "")
        else:
            content = extract_chat_content(chat_result)
            reasoning = extract_chat_reasoning(chat_result)
        self.streaming_text = ""
        self.streaming_reasoning = ""
        assistant_message: Dict[str, Any] = {"role": "assistant", "content": content, "reasoning": reasoning}
        if usage:
            assistant_message["usage"] = usage
        self.messages.append(assistant_message)
        self.window.on_conversation_changed()
        self._render_conversation()
        self._update_context_panel()

    def _send_finished(self) -> None:
        self.send_button.setEnabled(True)
        self.user_prompt.setEnabled(True)
        self.user_prompt.setFocus()
        self._update_context_panel()

    def _on_error(self, message: str) -> None:
        self.raw.setPlainText(message)
        self.streaming_text = ""
        self.streaming_reasoning = ""
        self._render_conversation(error=message)
        self._update_context_panel()
        self.window.warn(message)

    @staticmethod
    def _html(text: str) -> str:
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )


class SettingsTab(QWidget):
    def __init__(self, window: "MainWindow"):
        super().__init__()
        self.window = window

        title = QLabel("设置")
        title.setObjectName("pageTitle")
        subtitle = QLabel("管理 Agnes Agent 的连接配置。设置仅保存在当前 Windows 用户环境中。")
        subtitle.setObjectName("pageSubtitle")
        back = QPushButton("←  返回对话")
        back.setObjectName("subtleButton")
        back.clicked.connect(lambda: self.window.switch_page(0))

        connection = QFrame()
        connection.setObjectName("settingsCard")
        form = QFormLayout(connection)
        form.setContentsMargins(18, 16, 18, 16)
        form.setSpacing(12)
        form.addRow(self._heading("Agnes API"))
        form.addRow("API Base URL", self.window.base_url)
        form.addRow("API Key", self.window.api_key)
        options = QHBoxLayout()
        options.addWidget(self.window.save_key)
        options.addWidget(self.window.toggle_key)
        options.addStretch()
        form.addRow("", options)

        note = QLabel("API Key 默认只保留在内存中。勾选“在本机保存 API Key”后，关闭窗口时才会写入本机配置。")
        note.setObjectName("muted")
        note.setWordWrap(True)
        form.addRow("", note)

        form.addRow(self._heading("数据保存"))
        data_dir_row = QHBoxLayout()
        data_dir_row.addWidget(self.window.data_dir, 1)
        browse_data_dir = QPushButton("选择目录")
        browse_data_dir.setObjectName("subtleButton")
        browse_data_dir.clicked.connect(self.choose_data_dir)
        data_dir_row.addWidget(browse_data_dir)
        form.addRow("历史数据目录", data_dir_row)
        data_note = QLabel("对话、图像和视频工作室状态会保存到该目录下的 sessions.json。默认目录为程序同级 agnes_data。")
        data_note.setObjectName("muted")
        data_note.setWordWrap(True)
        form.addRow("", data_note)
        form.addRow("图片上传接口", self.window.image_upload_endpoint)
        upload_note = QLabel("用于“上传本地图片并回填 URL”。默认 auto：优先 img.scdn.io，失败后尝试备用图床；也可填写自定义上传接口。")
        upload_note.setObjectName("muted")
        upload_note.setWordWrap(True)
        form.addRow("", upload_note)

        actions = QHBoxLayout()
        self.save_button = QPushButton("保存设置")
        self.save_button.setObjectName("primaryButton")
        docs = QPushButton("↗  打开官方文档")
        docs.setObjectName("subtleButton")
        docs.clicked.connect(lambda: webbrowser.open("https://agnes-ai.com/doc/常用接入文档"))
        self.save_button.clicked.connect(self.save)
        actions.addWidget(self.save_button)
        actions.addWidget(docs)
        actions.addStretch()
        form.addRow("", actions)

        help_card = QFrame()
        help_card.setObjectName("settingsCard")
        help_layout = QVBoxLayout(help_card)
        help_layout.setContentsMargins(18, 16, 18, 16)
        help_layout.addWidget(self._heading("使用说明"))
        help = QLabel(
            "对话工作区：Enter 发送，Shift+Enter 换行。\n"
            "图像与视频工作区：输入图片需要使用公开可访问的 URL。\n"
            "视频任务：创建后默认每 5 秒自动查询一次状态。"
        )
        help.setObjectName("pageSubtitle")
        help.setWordWrap(True)
        help_layout.addWidget(help)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(14)
        layout.addWidget(back, 0, Qt.AlignLeft)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(connection)
        layout.addWidget(help_card)
        layout.addStretch()

    @staticmethod
    def _heading(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("paneTitle")
        return label

    def choose_data_dir(self) -> None:
        current = str(self.window.data_dir_path())
        chosen = QFileDialog.getExistingDirectory(self, "选择历史数据目录", current)
        if chosen:
            self.window.data_dir.setText(chosen)

    def save(self) -> None:
        self.window.save_sessions()
        self.window.save_settings()
        self.window.statusBar().showMessage("连接设置已保存", 4000)


class ImageTab(QWidget):
    def __init__(self, window: "MainWindow"):
        super().__init__()
        self.window = window
        self.current_url = ""
        self.current_bytes = b""
        self.busy = False
        self.preview_loading = False

        self.prompt = QTextEdit()
        self.prompt.setPlaceholderText("描述要生成或编辑的图像。编辑时请写清楚要改变和保持不变的内容。")
        self.prompt.setMinimumHeight(100)
        self.model = QComboBox()
        for label, value in IMAGE_MODEL_OPTIONS:
            self.model.addItem(label, value)
        self.size = QComboBox()
        self.size.addItems(["1024x1024", "1024x768", "768x1024"])
        self.seed_enabled = QCheckBox("指定 Seed")
        self.seed = QSpinBox()
        self.seed.setRange(0, 2147483647)
        self.input_urls = QTextEdit()
        self.input_urls.setPlaceholderText("可选，每行一个图片 URL 或 Data URI Base64。填写后自动启用 img2img，多行可用于合成。")
        self.input_urls.setFixedHeight(88)
        self.generate_button = QPushButton("生成图像")
        self.generate_button.setObjectName("primaryButton")
        self.open_button = QPushButton("浏览器打开结果")
        self.save_button = QPushButton("保存预览图")
        self.open_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.result_url = QLineEdit()
        self.result_url.setReadOnly(True)
        self.raw = QTextEdit()
        self.raw.setReadOnly(True)
        self.preview = QLabel("生成结果将在这里预览")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(QSize(420, 320))
        self.preview.setStyleSheet("QLabel { background: #101010; color: #9c9c9c; border: 1px solid #303030; border-radius: 8px; }")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.preview)

        form = QFormLayout()
        form.addRow("模型", self.model)
        form.addRow("Prompt", self.prompt)
        form.addRow("尺寸", self.size)
        seed_line = QHBoxLayout()
        seed_line.addWidget(self.seed_enabled)
        seed_line.addWidget(self.seed)
        seed_line.addStretch()
        form.addRow("随机种子", seed_line)
        form.addRow("输入图片 URL", self.input_urls)
        buttons = QHBoxLayout()
        buttons.addWidget(self.generate_button)
        buttons.addWidget(self.open_button)
        buttons.addWidget(self.save_button)
        buttons.addStretch()
        form.addRow("", buttons)
        form.addRow("结果 URL", self.result_url)

        outputs = QSplitter(Qt.Horizontal)
        outputs.addWidget(scroll)
        outputs.addWidget(self._boxed("原始响应", self.raw))
        outputs.setSizes([650, 450])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        title = QLabel("Agnes 图像工作室")
        title.setObjectName("pageTitle")
        subtitle = QLabel("生成新图像，或通过公开图片 URL 进行编辑与多图合成。")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(form)
        layout.addWidget(outputs, 1)

        self.generate_button.clicked.connect(self.generate)
        self.open_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.current_url)))
        self.save_button.clicked.connect(self.save_preview)
        self.model.currentIndexChanged.connect(self._model_changed)

    @staticmethod
    def _boxed(title: str, widget: QWidget) -> QGroupBox:
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        layout.addWidget(widget)
        return box

    def export_state(self) -> Dict[str, Any]:
        return {
            "model": self.current_model(),
            "prompt": self.prompt.toPlainText(),
            "size": self.size.currentText(),
            "seed_enabled": self.seed_enabled.isChecked(),
            "seed": self.seed.value(),
            "input_urls": self.input_urls.toPlainText(),
            "current_url": self.current_url,
            "raw": self.raw.toPlainText(),
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        model = str(state.get("model", IMAGE_MODEL))
        index = self.model.findData(model)
        self.model.setCurrentIndex(index if index >= 0 else 0)
        self.prompt.setPlainText(str(state.get("prompt", "")))
        self.size.setCurrentText(str(state.get("size", "1024x1024")))
        self.seed_enabled.setChecked(bool(state.get("seed_enabled", False)))
        self.seed.setValue(int(state.get("seed", 0)))
        self.input_urls.setPlainText(str(state.get("input_urls", "")))
        self.current_url = str(state.get("current_url", ""))
        stored_bytes = state.get("current_bytes", b"")
        self.current_bytes = stored_bytes if isinstance(stored_bytes, bytes) else b""
        self.result_url.setText(self.current_url)
        self.raw.setPlainText(str(state.get("raw", "")))
        self.open_button.setEnabled(bool(self.current_url))
        self.save_button.setEnabled(bool(self.current_bytes))
        self.preview.clear()
        if self.current_bytes:
            self._show_preview(self.current_bytes)
        else:
            self.preview.setText("生成结果将在这里预览")

    def current_model(self) -> str:
        return str(self.model.currentData() or IMAGE_MODEL)

    def _model_changed(self) -> None:
        if getattr(self.window, "stack", None) is not None and self.window.stack.currentIndex() == 1:
            self.window.model_label.setText(self.current_model())

    def generate(self) -> None:
        if not self.prompt.toPlainText().strip():
            self.window.warn("请输入图像 Prompt。")
            return
        try:
            client = self.window.client()
        except ValueError as exc:
            self.window.warn(str(exc))
            return
        payload = build_image_payload(
            self.current_model(),
            self.prompt.toPlainText(),
            self.size.currentText(),
            optional_int(self.seed.value(), self.seed_enabled.isChecked()),
            parse_urls(self.input_urls.toPlainText()),
        )
        self.current_url = ""
        self.current_bytes = b""
        self.result_url.clear()
        self.open_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.generate_button.setEnabled(False)
        self.busy = True
        self.preview.setText("正在生成图像...")
        self.window.start_job(
            lambda: client.generate_image(payload),
            self._on_result,
            self._on_error,
            on_finished=self._generation_finished,
        )

    def _generation_finished(self) -> None:
        self.busy = False
        self.generate_button.setEnabled(True)

    def _on_result(self, result: Dict[str, Any]) -> None:
        self.raw.setPlainText(pretty_json(result))
        data = result.get("data") or []
        self.current_url = data[0].get("url", "") if data else ""
        self.result_url.setText(self.current_url)
        self.open_button.setEnabled(bool(self.current_url))
        if not self.current_url:
            self.preview.setText("响应中没有找到 data[0].url")
            return
        self.preview.setText("正在下载预览...")
        self.preview_loading = True
        self.window.start_job(
            lambda: requests.get(self.current_url, timeout=60).content,
            self._show_preview,
            self._on_error,
            on_finished=lambda: setattr(self, "preview_loading", False),
        )

    def _show_preview(self, data: bytes) -> None:
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            self.preview.setText("预览下载完成，但内容不是可识别的图片。")
            return
        self.current_bytes = data
        self.preview.setPixmap(pixmap.scaled(900, 700, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.save_button.setEnabled(True)

    def _on_error(self, message: str) -> None:
        self.raw.setPlainText(message)
        self.preview.setText("请求失败")
        self.window.warn(message)

    def save_preview(self) -> None:
        if not self.current_bytes:
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存生成图片", "agnes-image.png", "Images (*.png *.jpg *.webp);;All Files (*)")
        if path:
            Path(path).write_bytes(self.current_bytes)


class VideoTab(QWidget):
    TERMINAL_STATUSES = {"completed", "failed"}

    def __init__(self, window: "MainWindow"):
        super().__init__()
        self.window = window
        self.polling = False
        self.uploading_images = False
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(5000)
        self.poll_timer.timeout.connect(self.retrieve)

        self.prompt = QTextEdit()
        self.prompt.setPlaceholderText("描述视频主体、动作、场景、镜头运动、光照和风格。")
        self.prompt.setMinimumHeight(90)
        self.workflow = QComboBox()
        self.workflow.addItem("文生视频", "text")
        self.workflow.addItem("图生视频", "image")
        self.workflow.addItem("多图引导视频", "multi")
        self.workflow.addItem("关键帧动画", "keyframes")
        self.input_urls = QTextEdit()
        self.input_urls.setPlaceholderText("可粘贴公开图片 URL，也可点击下方按钮上传本地图片后自动回填。每行一个 URL。")
        self.input_urls.setFixedHeight(74)
        self.upload_image_button = QPushButton("上传本地图片并回填 URL")
        self.upload_image_button.setObjectName("subtleButton")
        self.upload_status = QLabel("本地图片会上传到第三方公开图床，获得公网 URL 后再提交给 Agnes。")
        self.upload_status.setObjectName("muted")
        self.upload_status.setWordWrap(True)
        self.normalize_upload = QCheckBox("失败时尝试：重新编码为 JPEG")
        self.normalize_upload.setChecked(False)
        self.negative_prompt = QLineEdit()
        self.negative_prompt.setPlaceholderText("可选：描述要避免的内容")
        self.width = self._spin(64, 4096, 1152)
        self.height = self._spin(64, 4096, 768)
        self.frames = self._spin(1, 441, 121)
        self.fps = self._spin(1, 60, 24)
        self.steps_enabled = QCheckBox("指定推理步数")
        self.steps = self._spin(1, 500, 30)
        self.seed_enabled = QCheckBox("指定 Seed")
        self.seed = self._spin(0, 2147483647, 0)
        self.auto_poll = QCheckBox("自动轮询（每 5 秒）")
        self.auto_poll.setChecked(True)
        self.submit_button = QPushButton("创建视频任务")
        self.submit_button.setObjectName("primaryButton")
        self.retrieve_button = QPushButton("查询任务")
        self.open_button = QPushButton("浏览器打开视频")
        self.open_button.setEnabled(False)
        self.task_id = QLineEdit()
        self.task_id.setPlaceholderText("创建任务后自动填写，也可粘贴已有 task_id")
        self.status = QLabel("尚未提交任务")
        self.video_url = QLineEdit()
        self.video_url.setReadOnly(True)
        self.raw = QTextEdit()
        self.raw.setReadOnly(True)

        form = QFormLayout()
        form.addRow("模型", QLabel(VIDEO_MODEL))
        form.addRow("工作流", self.workflow)
        form.addRow("Prompt", self.prompt)
        form.addRow("输入图片 URL", self.input_urls)
        upload_row = QHBoxLayout()
        upload_row.addWidget(self.upload_image_button)
        upload_row.addWidget(self.normalize_upload)
        upload_row.addWidget(self.upload_status, 1)
        form.addRow("本地图片", upload_row)
        form.addRow("Negative Prompt", self.negative_prompt)
        dimensions = QHBoxLayout()
        dimensions.addWidget(QLabel("宽"))
        dimensions.addWidget(self.width)
        dimensions.addWidget(QLabel("高"))
        dimensions.addWidget(self.height)
        dimensions.addWidget(QLabel("帧数"))
        dimensions.addWidget(self.frames)
        dimensions.addWidget(QLabel("FPS"))
        dimensions.addWidget(self.fps)
        dimensions.addStretch()
        form.addRow("视频参数", dimensions)
        advanced = QHBoxLayout()
        advanced.addWidget(self.steps_enabled)
        advanced.addWidget(self.steps)
        advanced.addWidget(self.seed_enabled)
        advanced.addWidget(self.seed)
        advanced.addStretch()
        form.addRow("高级参数", advanced)
        buttons = QHBoxLayout()
        buttons.addWidget(self.submit_button)
        buttons.addWidget(self.retrieve_button)
        buttons.addWidget(self.open_button)
        buttons.addWidget(self.auto_poll)
        buttons.addStretch()
        form.addRow("", buttons)
        form.addRow("Task ID", self.task_id)
        form.addRow("任务状态", self.status)
        form.addRow("视频 URL", self.video_url)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        title = QLabel("Agnes 视频工作室")
        title.setObjectName("pageTitle")
        subtitle = QLabel("创建音画同步视频任务，并在生成期间自动追踪任务状态。")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(form)
        layout.addWidget(self._boxed("原始响应", self.raw), 1)

        self.submit_button.clicked.connect(self.submit)
        self.retrieve_button.clicked.connect(self.retrieve)
        self.open_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.video_url.text())))
        self.upload_image_button.clicked.connect(self.upload_local_images)

    @staticmethod
    def _spin(minimum: int, maximum: int, value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        return spin

    @staticmethod
    def _boxed(title: str, widget: QWidget) -> QGroupBox:
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        layout.addWidget(widget)
        return box

    def upload_local_images(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择要上传的图片",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;All Files (*)",
        )
        if not paths:
            return
        if self.normalize_upload.isChecked():
            try:
                upload_paths = [
                    prepare_video_image(path, self.window.data_dir_path() / "uploads")
                    for path in paths
                ]
            except (OSError, RuntimeError, ValueError) as exc:
                self.window.warn(str(exc))
                return
            status_text = f"已重新编码为 JPEG，正在上传 {len(upload_paths)} 张图片..."
        else:
            upload_paths = paths
            status_text = f"正在上传 {len(upload_paths)} 张原图..."
        self.uploading_images = True
        self.upload_image_button.setEnabled(False)
        self.upload_status.setText(status_text)
        endpoint = self.window.image_upload_endpoint.text().strip() or DEFAULT_IMAGE_UPLOAD_ENDPOINT
        self.window.start_job(
            lambda: upload_images_to_catbox(upload_paths, endpoint),
            self._on_upload_result,
            self._on_upload_error,
            on_finished=self._upload_finished,
        )

    def _upload_finished(self) -> None:
        self.uploading_images = False
        self.upload_image_button.setEnabled(True)

    def _on_upload_result(self, urls: List[str]) -> None:
        self.input_urls.setPlainText(append_urls(self.input_urls.toPlainText(), urls))
        total_urls = len(parse_urls(self.input_urls.toPlainText()))
        if self.workflow.currentData() in {"text", "image"}:
            self.workflow.setCurrentIndex(self.workflow.findData("image" if total_urls == 1 else "multi"))
        self.upload_status.setText(f"已上传并回填 {len(urls)} 个 URL。")
        self.window.save_sessions()

    def _on_upload_error(self, message: str) -> None:
        self.upload_status.setText("上传失败。")
        self.window.warn(message)

    def export_state(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt.toPlainText(),
            "workflow": self.workflow.currentData(),
            "input_urls": self.input_urls.toPlainText(),
            "negative_prompt": self.negative_prompt.text(),
            "width": self.width.value(),
            "height": self.height.value(),
            "frames": self.frames.value(),
            "fps": self.fps.value(),
            "steps_enabled": self.steps_enabled.isChecked(),
            "steps": self.steps.value(),
            "seed_enabled": self.seed_enabled.isChecked(),
            "seed": self.seed.value(),
            "normalize_upload": self.normalize_upload.isChecked(),
            "auto_poll": self.auto_poll.isChecked(),
            "task_id": self.task_id.text(),
            "status": self.status.text(),
            "video_url": self.video_url.text(),
            "raw": self.raw.toPlainText(),
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.poll_timer.stop()
        self.prompt.setPlainText(str(state.get("prompt", "")))
        workflow = str(state.get("workflow", "text"))
        workflow_index = self.workflow.findData(workflow)
        self.workflow.setCurrentIndex(max(0, workflow_index))
        self.input_urls.setPlainText(str(state.get("input_urls", "")))
        self.negative_prompt.setText(str(state.get("negative_prompt", "")))
        self.width.setValue(int(state.get("width", 1152)))
        self.height.setValue(int(state.get("height", 768)))
        self.frames.setValue(int(state.get("frames", 121)))
        self.fps.setValue(int(state.get("fps", 24)))
        self.steps_enabled.setChecked(bool(state.get("steps_enabled", False)))
        self.steps.setValue(int(state.get("steps", 30)))
        self.seed_enabled.setChecked(bool(state.get("seed_enabled", False)))
        self.seed.setValue(int(state.get("seed", 0)))
        self.normalize_upload.setChecked(bool(state.get("normalize_upload", False)))
        self.auto_poll.setChecked(bool(state.get("auto_poll", True)))
        self.task_id.setText(str(state.get("task_id", "")))
        self.status.setText(str(state.get("status", "尚未提交任务")))
        self.video_url.setText(str(state.get("video_url", "")))
        self.raw.setPlainText(str(state.get("raw", "")))
        self.open_button.setEnabled(bool(self.video_url.text()))
        status = self.status.text().split(" ·", 1)[0]
        if self.auto_poll.isChecked() and self.task_id.text().strip() and status not in self.TERMINAL_STATUSES:
            self.poll_timer.start()

    def submit(self) -> None:
        if not self.prompt.toPlainText().strip():
            self.window.warn("请输入视频 Prompt。")
            return
        try:
            client = self.window.client()
            payload = build_video_payload(
                self.prompt.toPlainText(),
                self.workflow.currentData(),
                parse_urls(self.input_urls.toPlainText()),
                self.width.value(),
                self.height.value(),
                self.frames.value(),
                self.fps.value(),
                optional_int(self.steps.value(), self.steps_enabled.isChecked()),
                optional_int(self.seed.value(), self.seed_enabled.isChecked()),
                self.negative_prompt.text(),
            )
        except ValueError as exc:
            self.window.warn(str(exc))
            return
        self.submit_button.setEnabled(False)
        self.video_url.clear()
        self.open_button.setEnabled(False)
        self.status.setText("queued")
        self.window.start_job(
            lambda: client.create_video(payload),
            self._on_result,
            self._on_error,
            on_finished=lambda: self.submit_button.setEnabled(True),
        )

    def retrieve(self) -> None:
        if self.polling:
            return
        task_id = self.task_id.text().strip()
        if not task_id:
            self.window.warn("请先填写 Task ID。")
            return
        try:
            client = self.window.client()
        except ValueError as exc:
            self.window.warn(str(exc))
            return
        self.polling = True
        self.retrieve_button.setEnabled(False)
        self.window.start_job(
            lambda: client.get_video(task_id),
            self._on_result,
            self._on_error,
            on_finished=self._poll_finished,
        )

    def _poll_finished(self) -> None:
        self.polling = False
        self.retrieve_button.setEnabled(True)

    def _on_result(self, result: Dict[str, Any]) -> None:
        self.raw.setPlainText(pretty_json(result))
        task_id = str(result.get("id", self.task_id.text()))
        if task_id:
            self.task_id.setText(task_id)
        status = str(result.get("status", "unknown"))
        progress = result.get("progress")
        suffix = f" · {progress}%" if progress is not None else ""
        self.status.setText(f"{status}{suffix}")
        video_url = extract_video_url(result)
        if video_url:
            self.video_url.setText(video_url)
        self.open_button.setEnabled(bool(self.video_url.text()))
        if status in self.TERMINAL_STATUSES:
            self.poll_timer.stop()
        elif self.auto_poll.isChecked() and task_id:
            self.poll_timer.start()

    def _on_error(self, message: str) -> None:
        self.raw.setPlainText(message)
        self.poll_timer.stop()
        self.window.warn(message)


class LegacyMainWindow(QMainWindow):
    relay_chunk = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool.globalInstance()
        self.settings = QSettings("SapiensAI", "AgnesModelTester")
        self.workers: List[Worker] = []

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(asset_path("agnes-agent.ico")))
        self.resize(1360, 900)
        self.setMinimumSize(1080, 720)

        self.base_url = QLineEdit(self.settings.value("base_url", DEFAULT_BASE_URL))
        self.api_key = QLineEdit(self.settings.value("api_key", ""))
        self.api_key.setEchoMode(QLineEdit.Password)
        self.save_key = QCheckBox("在本机保存 API Key")
        self.save_key.setChecked(bool(self.settings.value("save_key", False, type=bool)))
        self.toggle_key = QCheckBox("显示 Key")
        self.toggle_key.toggled.connect(lambda shown: self.api_key.setEchoMode(QLineEdit.Normal if shown else QLineEdit.Password))
        self.docs_button = QPushButton("打开官方文档")
        self.docs_button.setObjectName("sidebarButton")
        self.docs_button.clicked.connect(lambda: webbrowser.open("https://agnes-ai.com/doc/常用接入文档"))

        self.tabs = QTabWidget()
        self.text_tab = TextTab(self)
        self.image_tab = ImageTab(self)
        self.video_tab = VideoTab(self)
        self.tabs.addTab(self.text_tab, "对话 Agent")
        self.tabs.addTab(self.image_tab, "图像工作室")
        self.tabs.addTab(self.video_tab, "视频工作室")

        note = QLabel("说明：图像和视频接口按官方文档接收公开 URL；本工具不会上传本地媒体。视频生成完成后可用系统浏览器打开结果。")
        note.setWordWrap(True)
        note.setObjectName("pageSubtitle")

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())

        workspace = QWidget()
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(22, 16, 22, 10)
        workspace_layout.addWidget(self._build_header())
        workspace_layout.addWidget(self.tabs, 1)
        workspace_layout.addWidget(note)
        layout.addWidget(workspace, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage("就绪")

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(246)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 20, 18, 16)
        layout.setSpacing(10)

        logo = QLabel()
        pixmap = QPixmap(asset_path("agnes-agent.png"))
        logo.setPixmap(pixmap.scaled(58, 58, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel("Agnes Agent")
        title.setObjectName("agentTitle")
        subtitle = QLabel("多模态 AI 工作台")
        subtitle.setObjectName("mutedSidebar")
        badge = QLabel("●  Ready")
        badge.setObjectName("onlineBadge")
        badge.setFixedWidth(70)
        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(badge)
        layout.addSpacing(10)

        capability = QLabel("MODEL CAPABILITIES")
        capability.setObjectName("mutedSidebar")
        layout.addWidget(capability)
        for label in ("对话与推理  ·  Agnes 2.0", "图像编辑  ·  Image 2.0", "同步视频  ·  Video V2.0"):
            item = QLabel(label)
            item.setObjectName("modelPill")
            layout.addWidget(item)

        layout.addSpacing(10)
        connection = QLabel("CONNECTION")
        connection.setObjectName("mutedSidebar")
        layout.addWidget(connection)
        layout.addWidget(QLabel("API Base URL"))
        layout.addWidget(self.base_url)
        layout.addWidget(QLabel("API Key"))
        layout.addWidget(self.api_key)
        layout.addWidget(self.save_key)
        layout.addWidget(self.toggle_key)
        layout.addWidget(self.docs_button)
        layout.addStretch()

        footer = QLabel("Agnes free models shell\nBuilt for focused creation")
        footer.setObjectName("mutedSidebar")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        return sidebar

    def _build_header(self) -> QWidget:
        header = QFrame()
        row = QHBoxLayout(header)
        row.setContentsMargins(0, 0, 0, 2)
        words = QVBoxLayout()
        title = QLabel("Agnes 多模态 Agent")
        title.setObjectName("pageTitle")
        subtitle = QLabel("一个轻量的外层壳：从对话开始，也可以直接进入图像和视频创作。")
        subtitle.setObjectName("pageSubtitle")
        words.addWidget(title)
        words.addWidget(subtitle)
        row.addLayout(words)
        row.addStretch()
        return header

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.settings.setValue("base_url", self.base_url.text().strip() or DEFAULT_BASE_URL)
        self.settings.setValue("save_key", self.save_key.isChecked())
        self.settings.setValue("api_key", self.api_key.text().strip() if self.save_key.isChecked() else "")
        super().closeEvent(event)

    def client(self) -> AgnesClient:
        api_key = self.api_key.text().strip()
        if not api_key:
            raise ValueError("请先填写 Agnes API Key。")
        base_url = self.base_url.text().strip()
        if not base_url:
            raise ValueError("请填写 Base URL。")
        return AgnesClient(base_url, api_key)

    def start_job(
        self,
        fn: Callable[[], Any],
        on_result: Callable[[Any], None],
        on_error: Callable[[str], None],
        on_chunk_signal: Optional[Callable[..., None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        worker = Worker(fn)
        failed = {"value": False}

        def handle_error(message: str) -> None:
            failed["value"] = True
            on_error(message)

        worker.signals.result.connect(on_result)
        worker.signals.error.connect(handle_error)
        if on_chunk_signal:
            self.relay_chunk.connect(on_chunk_signal)
        self.workers.append(worker)
        self.statusBar().showMessage("请求处理中...")

        def finished() -> None:
            if on_chunk_signal:
                try:
                    self.relay_chunk.disconnect(on_chunk_signal)
                except TypeError:
                    pass
            if worker in self.workers:
                self.workers.remove(worker)
            if on_finished:
                on_finished()
            if not failed["value"]:
                self.statusBar().showMessage("就绪")

        worker.signals.finished.connect(finished)
        self.thread_pool.start(worker)

    def emit_chunk(self, text: str) -> None:
        self.relay_chunk.emit(text)

    def warn(self, message: str) -> None:
        self.statusBar().showMessage(message, 8000)


class MainWindow(QMainWindow):
    relay_chunk = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool.globalInstance()
        self.settings = QSettings("SapiensAI", "AgnesModelTester")
        self.workers: List[Worker] = []
        self.nav_buttons: List[QPushButton] = []
        self.sessions: List[Dict[str, Any]] = []
        self.active_session_id = ""

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(asset_path("agnes-agent.ico")))
        self.resize(1360, 900)
        self.setMinimumSize(1080, 700)

        self.base_url = QLineEdit(self.settings.value("base_url", DEFAULT_BASE_URL))
        self.api_key = QLineEdit(self.settings.value("api_key", ""))
        self.api_key.setEchoMode(QLineEdit.Password)
        self.save_key = QCheckBox("在本机保存 API Key")
        self.save_key.setChecked(bool(self.settings.value("save_key", False, type=bool)))
        self.toggle_key = QCheckBox("显示 Key")
        self.toggle_key.toggled.connect(
            lambda shown: self.api_key.setEchoMode(QLineEdit.Normal if shown else QLineEdit.Password)
        )
        saved_data_dir = self.settings.value("data_dir", "")
        self.data_dir = QLineEdit(str(normalize_data_dir(saved_data_dir)))
        self.data_dir.setPlaceholderText(str(default_data_dir()))
        saved_upload_endpoint = str(self.settings.value("image_upload_endpoint", "") or "").strip()
        if saved_upload_endpoint in {CATBOX_UPLOAD_ENDPOINT, NULL_POINTER_UPLOAD_ENDPOINT, TMPFILES_UPLOAD_ENDPOINT}:
            saved_upload_endpoint = ""
        self.image_upload_endpoint = QLineEdit(saved_upload_endpoint or DEFAULT_IMAGE_UPLOAD_ENDPOINT)

        self.stack = QStackedWidget()
        self.text_tab = TextTab(self)
        self.image_tab = ImageTab(self)
        self.video_tab = VideoTab(self)
        self.settings_tab = SettingsTab(self)
        self.stack.addWidget(self.text_tab)
        self.stack.addWidget(self.image_tab)
        self.stack.addWidget(self.video_tab)
        self.stack.addWidget(self.settings_tab)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_nav_rail())

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._build_top_bar())
        page_wrap = QWidget()
        page_layout = QVBoxLayout(page_wrap)
        page_layout.setContentsMargins(22, 16, 22, 16)
        page_layout.addWidget(self.stack)
        content_layout.addWidget(page_wrap, 1)
        layout.addWidget(content, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage("就绪")
        self.load_sessions()
        if self.sessions:
            self.active_session_id = self.active_session_id or self.sessions[0]["id"]
            session = self._active_session() or self.sessions[0]
            self.active_session_id = session["id"]
            self._load_session_workspace(session)
            self._refresh_session_list()
            self.switch_page(0)
        else:
            self.create_session()

    def _build_nav_rail(self) -> QWidget:
        rail = QFrame()
        rail.setObjectName("navRail")
        rail.setFixedWidth(276)
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(5)

        brand = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap(asset_path("agnes-agent.png")).scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel("Agnes")
        title.setObjectName("brandTitle")
        brand.addWidget(logo)
        brand.addWidget(title)
        brand.addStretch()
        layout.addLayout(brand)
        layout.addSpacing(12)

        new_chat = QPushButton("＋  新对话")
        new_chat.setObjectName("subtleButton")
        new_chat.clicked.connect(self.new_chat)
        layout.addWidget(new_chat)
        layout.addSpacing(7)

        self._add_nav_button(layout, "◈  对话 Agent", 0)
        self._add_nav_button(layout, "▧  图像工作室", 1)
        self._add_nav_button(layout, "▷  视频工作室", 2)
        layout.addSpacing(12)
        section = QLabel("工具")
        section.setObjectName("muted")
        layout.addWidget(section)

        docs = QPushButton("↗  官方文档")
        docs.clicked.connect(lambda: webbrowser.open("https://agnes-ai.com/doc/常用接入文档"))
        layout.addWidget(docs)
        layout.addSpacing(15)

        self.rail_title = QLabel("对话")
        self.rail_title.setObjectName("muted")
        layout.addWidget(self.rail_title)
        self.thread_list_widget = QWidget()
        self.thread_list_layout = QVBoxLayout(self.thread_list_widget)
        self.thread_list_layout.setContentsMargins(0, 0, 0, 0)
        self.thread_list_layout.setSpacing(3)
        layout.addWidget(self.thread_list_widget)
        layout.addStretch()

        self.settings_nav_button = QPushButton("⚙  设置")
        self.settings_nav_button.setObjectName("navButton")
        self.settings_nav_button.setCheckable(True)
        self.settings_nav_button.clicked.connect(lambda: self.switch_page(3))
        layout.addWidget(self.settings_nav_button)
        return rail

    def _add_nav_button(self, layout: QVBoxLayout, label: str, index: int) -> None:
        button = QPushButton(label)
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.clicked.connect(lambda _checked=False, page=index: self.switch_page(page))
        self.nav_buttons.append(button)
        layout.addWidget(button)

    def _build_thread_rail(self) -> QWidget:
        rail = QFrame()
        rail.setObjectName("threadRail")
        rail.setFixedWidth(244)
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(12, 15, 12, 12)
        layout.setSpacing(7)

        self.rail_title = QLabel("对话")
        self.rail_title.setObjectName("paneTitle")
        layout.addWidget(self.rail_title)
        search = QLineEdit()
        search.setPlaceholderText("搜索")
        layout.addWidget(search)
        layout.addSpacing(5)
        recent = QLabel("最近")
        recent.setObjectName("muted")
        layout.addWidget(recent)

        self.thread_button = QPushButton("生成 Agnes 模型测试 GUI")
        self.thread_button.setObjectName("threadButton")
        self.thread_button.setCheckable(True)
        self.thread_button.setChecked(True)
        layout.addWidget(self.thread_button)
        layout.addStretch()

        self.connection_panel = QFrame()
        self.connection_panel.setObjectName("settingsPanel")
        panel_layout = QVBoxLayout(self.connection_panel)
        panel_layout.setContentsMargins(9, 9, 9, 9)
        panel_layout.addWidget(QLabel("API Base URL"))
        panel_layout.addWidget(self.base_url)
        panel_layout.addWidget(QLabel("API Key"))
        panel_layout.addWidget(self.api_key)
        panel_layout.addWidget(self.save_key)
        panel_layout.addWidget(self.toggle_key)
        self.connection_panel.hide()
        layout.addWidget(self.connection_panel)
        return rail

    def _build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setFixedHeight(50)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)
        self.top_title = QLabel("生成 Agnes 模型测试 GUI")
        self.top_title.setObjectName("pageTitle")
        self.model_label = QLabel(TEXT_MODEL)
        self.model_label.setObjectName("muted")
        badge = QLabel("●  Ready")
        badge.setObjectName("onlineBadge")
        layout.addWidget(self.top_title)
        layout.addStretch()
        layout.addWidget(self.model_label)
        layout.addWidget(badge)
        return bar

    def switch_page(self, index: int) -> None:
        labels = ("生成 Agnes 模型测试 GUI", "图像工作室", "视频工作室", "设置")
        image_model = self.image_tab.current_model() if hasattr(self, "image_tab") else IMAGE_MODEL
        models = (TEXT_MODEL, image_model, VIDEO_MODEL, "Agnes Agent")
        rail_titles = ("对话", "图像任务", "视频任务", "设置")
        self.stack.setCurrentIndex(index)
        session = self._active_session()
        self.top_title.setText(session["title"] if index == 0 and session else labels[index])
        self.model_label.setText(models[index])
        self.rail_title.setText(rail_titles[index])
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)
        self.settings_nav_button.setChecked(index == 3)

    def new_chat(self) -> None:
        self.create_session()

    def create_session(self) -> None:
        if self._workspace_busy():
            self.warn("请等待当前任务完成后再创建新对话。")
            return
        self._capture_active_workspace()
        session = {
            "id": uuid.uuid4().hex,
            "title": "新对话",
            "messages": [],
            "context_summary": "",
            "summary_message_count": 0,
            "last_usage": {},
            "last_context_estimate": {},
            "last_compression_notice": "",
            "image_state": {},
            "video_state": {},
        }
        self.sessions.insert(0, session)
        self.active_session_id = session["id"]
        self._load_session_workspace(session)
        self.switch_page(0)
        self._refresh_session_list()
        self.save_sessions()
        self.statusBar().showMessage("已创建新对话", 3000)

    def on_conversation_changed(self, first_user_text: str = "") -> None:
        session = self._active_session()
        if not session:
            return
        if first_user_text and session["title"] == "新对话":
            normalized = " ".join(first_user_text.split())
            session["title"] = normalized[:22] + ("..." if len(normalized) > 22 else "")
            self.top_title.setText(session["title"])
        self._refresh_session_list()
        self.save_sessions()

    def open_session(self, session_id: str) -> None:
        if session_id == self.active_session_id:
            self.switch_page(0)
            return
        if self._workspace_busy():
            self.warn("请等待当前任务完成后再切换对话。")
            return
        session = self._find_session(session_id)
        if not session:
            return
        self._capture_active_workspace()
        self.active_session_id = session_id
        self._load_session_workspace(session)
        self.switch_page(0)
        self.top_title.setText(session["title"])
        self._refresh_session_list()
        self.save_sessions()

    def delete_session(self, session_id: str) -> None:
        if self._workspace_busy():
            self.warn("请等待当前任务完成后再删除对话。")
            return
        self._capture_active_workspace()
        self.sessions = [session for session in self.sessions if session["id"] != session_id]
        if self.active_session_id == session_id:
            if self.sessions:
                self.open_session(self.sessions[0]["id"])
            else:
                self.create_session()
                return
        self._refresh_session_list()
        self.save_sessions()

    def _refresh_session_list(self) -> None:
        while self.thread_list_layout.count():
            item = self.thread_list_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
        for session in self.sessions:
            thread = QPushButton(session["title"])
            thread.setObjectName("threadButton")
            thread.setCheckable(True)
            thread.setChecked(session["id"] == self.active_session_id)
            thread.clicked.connect(lambda _checked=False, sid=session["id"]: self.open_session(sid))
            thread.setContextMenuPolicy(Qt.CustomContextMenu)
            thread.customContextMenuRequested.connect(
                lambda pos, sid=session["id"], button=thread: self._show_session_menu(sid, button, pos)
            )
            self.thread_list_layout.addWidget(thread)

    def _show_session_menu(self, session_id: str, button: QPushButton, pos) -> None:
        menu = QMenu(self)
        delete = menu.addAction("删除对话")
        selected = menu.exec_(button.mapToGlobal(pos))
        if selected == delete:
            self.delete_session(session_id)

    def _capture_active_workspace(self) -> None:
        session = self._active_session()
        if not session:
            return
        session["messages"] = self.text_tab.messages
        session.update(self.text_tab.export_context_state())
        session["image_state"] = self.image_tab.export_state()
        session["video_state"] = self.video_tab.export_state()

    def _load_session_workspace(self, session: Dict[str, Any]) -> None:
        self.text_tab.load_session_state(session)
        self.image_tab.load_state(session.setdefault("image_state", {}))
        self.video_tab.load_state(session.setdefault("video_state", {}))

    def _workspace_busy(self) -> bool:
        return (
            not self.text_tab.send_button.isEnabled()
            or self.image_tab.busy
            or self.image_tab.preview_loading
            or not self.video_tab.submit_button.isEnabled()
            or self.video_tab.polling
            or self.video_tab.uploading_images
        )

    def _find_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return next((session for session in self.sessions if session["id"] == session_id), None)

    def _active_session(self) -> Optional[Dict[str, Any]]:
        return self._find_session(self.active_session_id)

    def data_dir_path(self) -> Path:
        return normalize_data_dir(self.data_dir.text())

    def sessions_path(self) -> Path:
        return sessions_file_path(self.data_dir_path())

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._capture_active_workspace()
        self.save_sessions()
        self.save_settings()
        super().closeEvent(event)

    def load_sessions(self) -> None:
        path = self.sessions_path()
        legacy_path = legacy_app_data_dir() / "sessions.json"
        if not path.exists() and legacy_path.exists():
            path = legacy_path
        if not path.exists():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.warn(f"读取历史对话失败：{exc}")
            return
        sessions = payload.get("sessions", [])
        if not isinstance(sessions, list):
            return
        normalized = []
        for session in sessions:
            if not isinstance(session, dict):
                continue
            session_id = str(session.get("id") or uuid.uuid4().hex)
            normalized.append(
                {
                    "id": session_id,
                    "title": str(session.get("title") or "新对话"),
                    "messages": session.get("messages") if isinstance(session.get("messages"), list) else [],
                    "context_summary": str(session.get("context_summary") or ""),
                    "summary_message_count": int(session.get("summary_message_count") or 0),
                    "last_usage": session.get("last_usage") if isinstance(session.get("last_usage"), dict) else {},
                    "last_context_estimate": (
                        session.get("last_context_estimate")
                        if isinstance(session.get("last_context_estimate"), dict)
                        else {}
                    ),
                    "last_compression_notice": str(session.get("last_compression_notice") or ""),
                    "image_state": session.get("image_state") if isinstance(session.get("image_state"), dict) else {},
                    "video_state": session.get("video_state") if isinstance(session.get("video_state"), dict) else {},
                }
            )
        self.sessions = normalized
        self.active_session_id = str(payload.get("active_session_id") or "")

    def save_sessions(self) -> None:
        self._capture_active_workspace()
        path = self.sessions_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                pretty_json(
                    json_safe(
                        {
                            "version": 1,
                            "active_session_id": self.active_session_id,
                            "sessions": self.sessions,
                        }
                    )
                ),
                encoding="utf-8",
            )
        except OSError as exc:
            self.warn(f"保存历史对话失败：{exc}")

    def save_settings(self) -> None:
        self.settings.setValue("base_url", self.base_url.text().strip() or DEFAULT_BASE_URL)
        self.settings.setValue("save_key", self.save_key.isChecked())
        self.settings.setValue("api_key", self.api_key.text().strip() if self.save_key.isChecked() else "")
        self.settings.setValue("data_dir", str(self.data_dir_path()))
        self.settings.setValue("image_upload_endpoint", self.image_upload_endpoint.text().strip() or DEFAULT_IMAGE_UPLOAD_ENDPOINT)
        self.settings.sync()

    def client(self) -> AgnesClient:
        api_key = self.api_key.text().strip()
        if not api_key:
            self.switch_page(3)
            raise ValueError("请先在设置页填写 Agnes API Key。")
        base_url = self.base_url.text().strip()
        if not base_url:
            self.switch_page(3)
            raise ValueError("请填写 Base URL。")
        return AgnesClient(base_url, api_key)

    def start_job(
        self,
        fn: Callable[[], Any],
        on_result: Callable[[Any], None],
        on_error: Callable[[str], None],
        on_chunk_signal: Optional[Callable[..., None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        worker = Worker(fn)
        failed = {"value": False}

        def handle_error(message: str) -> None:
            failed["value"] = True
            on_error(message)

        worker.signals.result.connect(on_result)
        worker.signals.error.connect(handle_error)
        if on_chunk_signal:
            self.relay_chunk.connect(on_chunk_signal)
        self.workers.append(worker)
        self.statusBar().showMessage("请求处理中...")

        def finished() -> None:
            if on_chunk_signal:
                try:
                    self.relay_chunk.disconnect(on_chunk_signal)
                except TypeError:
                    pass
            if worker in self.workers:
                self.workers.remove(worker)
            if on_finished:
                on_finished()
            if not failed["value"]:
                self.statusBar().showMessage("就绪")

        worker.signals.finished.connect(finished)
        self.thread_pool.start(worker)

    def emit_chunk(self, kind: str, text: str) -> None:
        self.relay_chunk.emit(kind, text)

    def warn(self, message: str) -> None:
        self.statusBar().showMessage(message, 8000)


def run_self_test() -> None:
    image = build_image_payload(IMAGE_MODEL, "edit", "1024x768", 7, ["https://example.com/a.png"])
    assert image["model"] == IMAGE_MODEL_21
    assert image["extra_body"]["image"] == ["https://example.com/a.png"]
    assert image["extra_body"]["response_format"] == "url"
    video = build_video_payload("move", "keyframes", ["a", "b"], 1152, 768, 121, 24, None, 8, "")
    assert video["extra_body"]["mode"] == "keyframes"
    assert video["seed"] == 8
    image_video = build_video_payload("move", "image", ["https://example.com/a.jpg"], 1152, 768, 121, 24, None, None, "")
    assert image_video["image"] == "https://example.com/a.jpg"
    assert "extra_body" not in image_video
    assert extract_usage({"usage": {"prompt_tokens": 2}})["prompt_tokens"] == 2
    assert estimate_text_tokens("你好") >= 2
    assert estimate_messages_tokens([{"role": "user", "content": "hello"}]) > 0
    assert "user" in conversation_to_text([{"role": "user", "content": "hello"}])
    assert AUTO_IMAGE_UPLOAD_ENDPOINTS[0] == SCDN_UPLOAD_ENDPOINT
    assert is_scdn_endpoint("https://img.scdn.io/api/v1.php")
    assert is_null_pointer_endpoint("https://0x0.st/")
    assert is_tmpfiles_endpoint("https://tmpfiles.org/api/v1/upload")
    assert is_auto_upload_endpoint("auto")
    assert tmpfiles_direct_url("https://tmpfiles.org/123/a.jpg") == "https://tmpfiles.org/dl/123/a.jpg"
    assert append_urls("https://a.test/1.png\n", ["https://a.test/1.png", "https://a.test/2.png"]) == "https://a.test/1.png\nhttps://a.test/2.png"
    json.dumps(json_safe({"image_state": {"current_bytes": b"preview"}}), ensure_ascii=False)
    assert sessions_file_path(default_data_dir()).name == "sessions.json"
    assert extract_video_url({"status": "completed", "video_url": "https://example.com/result.mp4"}) == "https://example.com/result.mp4"
    assert extract_video_url({"data": [{"url": "https://example.com/nested/result.mp4"}]}) == "https://example.com/nested/result.mp4"
    assert extract_video_url({"output": {"video": {"url": "https://storage.googleapis.com/bucket/object?token=1"}}}) == "https://storage.googleapis.com/bucket/object?token=1"
    try:
        validate_video_frames(120)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid num_frames should fail")

    class FakeStreamResponse:
        ok = True

        @staticmethod
        def iter_lines(decode_unicode: bool = False):
            assert decode_unicode is False
            yield b'data: {"choices":[],"usage":{"total_tokens":3}}'
            yield 'data: {"choices":[{"delta":{"reasoning_content":"先判断，"}}]}'.encode("utf-8")
            yield 'data: {"choices":[{"delta":{"content":"你好，世界"}}]}'.encode("utf-8")
            yield b"data: [DONE]"

    original_post = requests.post
    streamed_chunks = []
    try:
        requests.post = lambda *args, **kwargs: FakeStreamResponse()  # type: ignore[assignment]
        streamed = AgnesClient(DEFAULT_BASE_URL, "test-key").chat(
            {"model": TEXT_MODEL, "messages": [], "stream": True},
            lambda kind, text: streamed_chunks.append((kind, text)),
        )
    finally:
        requests.post = original_post
    assert streamed["content"] == "你好，世界"
    assert streamed["reasoning"] == "先判断，"
    assert streamed["usage"]["total_tokens"] == 3
    assert streamed_chunks == [("reasoning", "先判断，"), ("content", "你好，世界")]
    assert extract_chat_content({"choices": []}) == ""
    assert extract_chat_content({"choices": [{"message": {"content": "ok"}}]}) == "ok"
    assert extract_chat_reasoning({"choices": [{"message": {"reasoning_content": "step"}}]}) == "step"
    print("Self-test passed.")


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SapiensAI.AgnesAgent")
    except Exception:
        pass


def main() -> int:
    if "--self-test" in sys.argv:
        run_self_test()
        return 0
    set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(QIcon(asset_path("agnes-agent.ico")))
    app.setStyle("Fusion")
    app.setStyleSheet(CODEX_STYLESHEET)
    window = MainWindow()
    window.show()
    if "--smoke-test" in sys.argv:
        QTimer.singleShot(600, app.quit)
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
