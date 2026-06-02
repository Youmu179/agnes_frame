# Agnes Agent

围绕 Agnes 免费模型构建的轻量多模态 Agent 桌面壳：

- `agnes-2.0-flash`：文本、多轮对话、流式输出。
- `agnes-image-2.0-flash`：图像生成、URL 图生图、多图合成、结果预览。
- `agnes-video-v2.0`：文生视频、图生视频、多图视频、关键帧动画、异步轮询。

应用使用统一的 Agnes Agent 图标，覆盖 exe、窗口标题栏与 Windows 任务栏。

界面采用主流 Agent 工作台布局：左侧导航与最近任务、右侧主线程、底部固定输入器。连接配置、模型参数和原始响应默认折叠，需要时再展开。

## 运行

双击 `run_gui.bat`，或在 Anaconda Prompt 中运行：

```bat
conda activate py313
python agnes_gui.py
```

## 打包 onefile

双击 `build_onefile.bat`。脚本会进入 `py313` 环境，执行自检，并使用 PyInstaller 生成：

```text
dist\AgnesModelTester.exe
```

## 使用说明

- API Base URL 默认为 `https://apihub.agnes-ai.com`。
- 点击左下角“设置”进入独立设置页。API Key 默认不会写入本机配置，需要持久化时勾选“在本机保存 API Key”。
- 对话输入框中，按 `Enter` 发送消息，按 `Shift+Enter` 插入换行。
- 左侧对话列表会在当前运行期间保留线程。每个线程分别保存文本消息、图像工作区和视频工作区状态，切换线程时互不干扰。
- 新线程发送首条消息后会自动生成标题。右键点击线程，可从菜单中删除。
- 如果模型返回 Thinking / Reasoning 流，对话页会显示可折叠的 Thinking 区域；模型不返回时不会显示。
- 官方图像和视频接口接收公开可访问的图片 URL，本工具不会上传本地图片。
- 视频任务是异步任务。创建后，工具默认每 5 秒查询一次任务状态。

官方文档：

- [常用接入文档](https://agnes-ai.com/doc/%E5%B8%B8%E7%94%A8%E6%8E%A5%E5%85%A5%E6%96%87%E6%A1%A3)
- [Agnes-2.0-Flash](https://agnes-ai.com/doc/agnes-20-flash)
- [Agnes-Image-2.0-Flash](https://agnes-ai.com/doc/agnes-image-20-flash)
- [Agnes-Video-V2.0](https://agnes-ai.com/doc/agnes-video-v20)
