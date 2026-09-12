# 三软件连接与安装

核验日期：2026-09-12。City Design 提供安装辅助、配置生成与检查；三款设计软件及其许可仍需自行安装。下面分别说明官方组件、社区组件和当前无法承诺的路线。

| 对象 | 来源与身份 | 当前可执行的路线 |
|---|---|---|
| Rhino 8 / 9，Windows / macOS | McNeel 官方 Rhino-MCP-Platform；上游源码 MIT | Rhino 包管理器安装，取得 router 路径，生成并注册 Codex 配置 |
| QGIS，Windows / macOS / Linux | 社区 `nkarasiak/qgis-mcp`，收录在 QGIS 插件库；GPL-2.0 | 下载校验同一提交的插件与服务，安装锁定依赖，配置本机令牌，再做 MCP 检查 |
| AutoCAD / Civil 3D，Windows | Autodesk 官方 MCP，Tech Preview | 官方文档支持 Autodesk Assistant；AutoCAD 为读取/分析，Civil 3D 另有写工具 |
| AutoCAD 2024，macOS | 上述官方 MCP 路线不支持 | 保留已有 AutoLISP / Core Console / GUI 工作流；本版本没有将私人适配器转换为通用 Mac MCP |
| Autodesk Help，跨平台客户端 | Autodesk 官方远程 MCP | 可选注册到 Codex，用来查文档，不能操作本地 DWG |

官方来源：[Rhino 安装到 Codex](https://github.com/mcneel/RhinoAI/blob/rhino-9.x/docs/content/docs/getting-started/codex.md)、[QGIS 插件库](https://plugins.qgis.org/plugins/qgis_mcp_plugin/)、[QGIS MCP 源码](https://github.com/nkarasiak/qgis-mcp)、[AutoCAD/Civil 3D MCP](https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_AutoCADCivil3DMcp_autodesk_autocad_civil_3d_mcp_html)、[Autodesk Help MCP](https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_KnowledgeMcp_autodesk_product_help_mcp_server_html)。机器可读来源及版本见 `references/connections.json`。

## 先检查已有环境

请在新对话中使用：

> 使用 City Design 检查这台电脑的 Rhino、QGIS、AutoCAD 连接。保留已有可用配置，按操作系统选择受支持的路线，补齐缺失连接，并区分安装、工具发现、实际连通和模型验收。

代理先读取现有 MCP 名称与实际软件版本。不要因为窗口关闭就重装插件，也不要用另一个同名服务覆盖已工作的连接。准备命令只写新目录；注册默认只预览，`--apply` 才实际添加缺少的条目。显式要求补齐连接即授权在该范围内执行，不需要重复确认。

以下 `<plugin>` 是本插件目录。核心配置工具使用 Python 3.11+；QGIS 外部服务需要 Python 3.12+ 和 `uv`。

```sh
python3 <plugin>/scripts/connections.py catalog
```

Windows 将示例中的 `python3` 换成 `py -3` 或当前环境的 `python`；每条命令均可单独执行，含空格的路径用双引号包裹。

## QGIS：固定两端版本，再连通

1. 在仓库之外选择新目录执行：

```sh
python3 <plugin>/scripts/connections.py stage-qgis --output ./qgis-connection --install-server
```

工具下载固定提交 `29931a0eea80bf30a40b0b18ca6c60a8191521b6`（源码版本 0.14.0），核对 SHA-256，再解压。`uv sync --frozen --no-dev` 使用上游锁文件安装外部服务，不改系统 Python。完整上游源码与 GPL 许可保留在该目录；内部插件 ZIP 也包含上游许可。现有目录不会覆盖；安装中断后可在已校验源码目录执行相同的 `uv sync --frozen --no-dev`，不要删除已安装的其他版本。

2. 输出的 `qgis-mcp-plugin.zip` 在 QGIS 的“插件 → 管理并安装插件 → 从 ZIP 安装”中安装到**当前要使用的 profile**。该源码快照可能比插件库的稳定版新；不能混装稳定版内部插件和不同版本的外部服务。已有工作的两端无需替换。更新前备份 profile 中原插件目录，按 QGIS 提示重载或重启。

3. 在 QGIS MCP 面板设置访问令牌并启动服务，限制在本机回环地址。将同一令牌保存到仓库外的私人文本文件；在 macOS/Linux 上设为仅自己可读。不要在聊天、GitHub、示例配置或命令参数中粘贴令牌值。

4. 使用源码目录中新安装的 Python 生成配置。macOS/Linux 路径为 `<source>/.venv/bin/python`；Windows 为 `<source>/.venv/Scripts/python.exe`。

```sh
python3 <plugin>/scripts/connections.py prepare --output ./local-connections --qgis-python "<source>/.venv/bin/python" --token-file "<private-token-file>" --port 9876
```

`prepare` 在新目录保存启动器快照，后续插件缓存更新不会导致启动器路径失效。它只记录令牌文件路径；启动服务时才读取值。端口必须与 QGIS 面板一致，启动器固定连接 `127.0.0.1`，不会继承其他终端的远程或多实例设置。

5. 实际验证外部 MCP 与内部插件：

```sh
"<source>/.venv/bin/python" <plugin>/scripts/probe_qgis.py --plan ./local-connections/connections.json
```

检查会初始化 MCP、发现工具、调用 `ping` 和 `diagnose`，核对两端版本，不修改图层。退出码 0 只表示 `CONNECTED_VERSION_MATCHED`。端口打开、MCP 工具可列出、插件实际响应是不同状态；任何缺项返回 2。此命令使用 QGIS 外部环境已安装的 MCP SDK，无需另装到系统 Python。

## Rhino：复用官方 router

在已安装并许可的 Rhino 8 或 9 中运行 `PackageManager`，搜索 `Rhino-MCP-Platform`。安装完成运行 `MCPConnect`，复制它显示的实际 router 路径；不要猜测版本文件夹或芯片架构。

```sh
python3 <plugin>/scripts/connections.py prepare --output ./rhino-connection --rhino-router "<actual-router-path>" --rhino-version 8
```

Rhino 9 使用 `--rhino-version 9`。也可将这些参数添加到上面的 QGIS `prepare` 命令，一次生成两端配置。这里固定的是使用的本机 router 文件路径，实际二进制由 McNeel 包管理器分发，未随本仓库复制。

注册并新建 Codex 对话后先用现有连接的 `list_slots` 检查：空数组表示路由器可响应但没有运行实例。不要将其记为模型已打开。再核对实际文档路径、RuntimeSerialNumber、对象数量及单位；在受控副本上完成一次保存和重新打开，才能验收建模链路。不要为检查而随意终止 router：它可能持有 Rhino 进程生命周期。

## 注册到 Codex 与恢复

```sh
python3 <plugin>/scripts/connections.py register --plan ./local-connections/connections.json
python3 <plugin>/scripts/connections.py register --plan ./local-connections/connections.json --apply
```

CLI 不在 PATH 时指定 `--codex "<actual-codex-executable>"`。工具使用 Codex 自身的 `mcp add`，先备份原 `config.toml`，仅添加不存在的名称，并回读核对。已有同名配置无论是否一致都保留，结果列出 `existing_preserved`，不把“已存在”当成连通。多项注册中断时，已成功条目仍保留；重新预览会只显示剩余条目。

`connections.json`、生成的 TOML、配置备份和令牌均属于本机私人资料，不上传。需要恢复时先查看本次添加的名称及备份，使用 Codex 的 MCP 配置管理移除本次新条目；不要用整份旧配置覆盖之后新增的其他服务。若没有其他变化，可以恢复已核对的备份。QGIS 内部插件回滚与 Codex 配置回滚分别处理。

## AutoCAD：按官方当前支持范围配置

在具备该功能的 Windows AutoCAD/Civil 3D 中打开 Autodesk Assistant 并启用 Tech Preview，运行 `MCPHTTPSTART`，使用其返回的真实地址；`MCPCONFIG` 查看启用工具，`MCPHTTPSTOP` 停止。用 Assistant 读取当前图纸的图层和对象数量，与打开的 DWG 核对。官方示例中的 5001 是示例端口，不要硬编码。

当前产品文档只列 Autodesk Assistant 为支持客户端，未建立该产品路线到 Codex 的受支持配置。因此本工具**不生成一个虚假的 AutoCAD Codex 条目**，也不把 Civil 3D 的写入功能算作 AutoCAD 能力。Mac AutoCAD 2024 不具备此官方路线；继续使用经过项目验收的脚本/GUI，并单独核验保存的 DWG。源码包提供的城市建模技能仍可指导这条工作流，但不等于已附带通用执行器。

如需在 Codex 中查询 Autodesk 官方文档，可单独启用：

```sh
python3 <plugin>/scripts/connections.py prepare --output ./autodesk-docs-connection --autodesk-help
python3 <plugin>/scripts/connections.py register --plan ./autodesk-docs-connection/connections.json --apply
```

这只注册官方文档服务。实际请求时仅发送查阅关键词，不应将私有图纸或项目路径当成查询文本。它不能读取或改动本地 DWG。

## 验收层级

1. **安装**：软件、原生插件和外部可执行文件存在，版本有记录。
2. **注册**：客户端配置正确，原配置保留。
3. **连通**：MCP 初始化、工具发现、原生应用响应与版本核对均成功。
4. **文档身份**：核对当前文件路径、单位、坐标、对象/图层统计。
5. **实际操作**：受控副本上执行小规模操作、保存、独立重开与结果比较。

自动测试覆盖配置保护与可重复安装逻辑；模拟服务只能验收协议工具，不能替代 QGIS/Rhino/AutoCAD 的桌面验收。
