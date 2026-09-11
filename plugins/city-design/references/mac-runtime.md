# 已验证的 Mac 接口与限制

本机快照：QGIS 3.44.14；QGIS MCP 0.14.0，commit 29931a0eea80bf30a40b0b18ca6c60a8191521b6；Rhino WIP 9.0.25350.306；官方 Rhino MCP Platform 0.1.5；AutoCAD 2024，24.3.61.182。恢复任务时重新检测。Rhino 许可状态未验证，本插件不修改许可。

QGIS 由专用 profile 的内部插件与固定版本外部服务组成，本机 127.0.0.1:9876，令牌保存在工作区私有文件。不要复制令牌进插件、图纸或日志。当前外部服务启动器需要 QGIS 内部服务器先运行；doctor 的端口结果仅为 TCP 检测，执行前还须 MCP ping。

Rhino router 使用 --default-version 9。原生模板使用 IronPython 2。Mac 的 Open 可以打开新文档窗口而 MCP 仍绑定旧空文档：核对 FullPath/RuntimeSerialNumber，必要时用 RhinoDoc.OpenDocuments() 选择准确文档，或使用原生 headless 保存/回读。不要只看 get_viewport_image 判定模型为空。持有 router 的进程可能拥有 Rhino 生命周期；文件保存前不要随意终止该进程。

AutoCAD Core Console 已验证几何写入与独立 DWG 回读。本机通过 Core Console 调用 PDF 驱动发生 initMetaCaps / NSBitmapImageRep 异常，不能继续使用该出图路径。主 GUI 的 AutoCAD PDF (High Quality Print).pc3 已成功打印并视觉检查 A3 中文成果。GUI 打印是独立步骤，尚未封装为通用无人值守打印器。

GUI 输入路径含下划线时，本次 AutoCAD 命令行 typeText 出现字符丢失。已用受控短路径别名解决；恢复时先检查实际输入值，不假设脚本路径已完整进入命令行。

现有 Codex 配置已连接 rhino 与 qgis；本插件不再声明重复的 MCP 服务，以免争用实例。安装插件不会把第三方软件、MCP 二进制或它们的许可证打包进去。本机绑定只指向现有接管包，迁移电脑需重新适配与验收。
