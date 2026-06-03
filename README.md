# Agnes Agent

一个非官方的 Agnes API 桌面工具，用来快速测试 Agnes 免费模型：文本、图像、视频都放在一个简易 Agent 外壳里。

English version: [README.en.md](README.en.md)

> 说明：本项目主要由 Codex 的 GPT-5.5 辅助生成和迭代。项目不是 Agnes / Sapiens AI 官方客户端，API 行为以官方服务为准。

## 能做什么

- 对话 Agent：调用 `agnes-2.0-flash`，支持多轮对话、流式输出、Thinking / Reasoning 折叠展示。
- 图像工作室：调用 `agnes-image-2.0-flash`，支持文生图、URL 图生图、多图合成、预览和保存。
- 视频工作室：调用 `agnes-video-v2.0`，支持文生视频、图生视频、多图视频、关键帧动画、任务轮询。

## 下载后怎么用

如果你只是想使用工具：

1. 到 GitHub Release 下载 `AgnesModelTester.exe`。
2. 双击运行。
3. 点击左下角“设置”。
4. 填写 Agnes API Key。
5. 如需下次打开仍保留 Key，勾选“在本机保存 API Key”。
6. 返回对话、图像工作室或视频工作室开始测试。

默认 API Base URL 是：

```text
https://apihub.agnes-ai.com
```

## 视频工作室说明

Agnes Video 的图生视频需要公网可访问的图片 URL。

你可以：

- 直接粘贴图片 URL。
- 点击“上传本地图片并回填 URL”，工具会先上传到图床，再自动把 URL 填入输入框。
- 如果某张图片一直被 Agnes 返回 `Invalid image`，可以尝试换图床或用 Agnes 图像工作室生成的图片 URL。

默认上传接口为 `auto`，会优先使用 `img.scdn.io`。第三方图床是公开服务，请不要上传隐私图片。

## 本地数据

会话和工作区状态默认保存在：

```text
agnes_data\sessions.json
```

你也可以在设置中修改历史数据目录。

开源或提交代码前，建议不要提交：

- `dist/`
- `build/`
- `agnes_data/`
- 本地生成的图片、视频、会话记录

## 从源码运行

```bat
conda activate py313
pip install -r requirements.txt
python agnes_gui.py
```

## 自行打包

双击：

```text
build_onefile.bat
```

脚本会进入 `py313` 环境，运行自检，然后生成：

```text
dist\AgnesModelTester.exe
```

## 官方文档

- [常用接入文档](https://agnes-ai.com/doc/%E5%B8%B8%E7%94%A8%E6%8E%A5%E5%85%A5%E6%96%87%E6%A1%A3)
- [Agnes-2.0-Flash](https://agnes-ai.com/doc/agnes-20-flash)
- [Agnes-Image-2.0-Flash](https://agnes-ai.com/doc/agnes-image-20-flash)
- [Agnes-Video-V2.0](https://agnes-ai.com/doc/agnes-video-v20)
- [img.scdn.io API](https://img.scdn.io/api_docs.php)
