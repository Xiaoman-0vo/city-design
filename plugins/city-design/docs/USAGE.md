# 使用说明

## 核心工具

下面的 `<plugin>` 指包含 `.codex-plugin/plugin.json` 的 `plugins/city-design` 目录；安装后的插件缓存中也有同样结构。

```sh
python3 <plugin>/scripts/city_design.py doctor
python3 <plugin>/scripts/city_design.py init-project --output ./my-project
python3 <plugin>/scripts/city_design.py demo --output ./new-example
python3 <plugin>/scripts/city_design.py --project ./my-project check-drawing --manifest drawings/check.json
```

`init-project` 为新目录建立状态和工作约定。单位、比例和坐标默认未确认，不会默认为真实米制。已有项目不自动覆盖；将已有项目整理成包含 `AGENTS.md` 和 `state/PROJECT_STATE.json` 的受控工作目录后，可用 `--project` 指定。

`demo` 无需模型资料、账号或设计软件。它产生合成参数、四栋建筑的 SVG 平面图、制图清单样例与检查记录。再次使用同一输出目录会被拒绝，避免覆盖你的修改。

## 私人配置

正常检查可直接使用 `--project`。可选的连接配置从高到低选择：`--config` → `CITY_DESIGN_CONFIG` → 插件内的 `config/local-binding.json`。项目路径从 `--project` → `CITY_DESIGN_PROJECT` → 配置中的 `project_root` 选择。

复制 `config/local-binding.example.json` 到仓库之外的私人位置，填入实际项目与应用路径，再用 `--config` 选择它。`project_root`、`mcp_python` 的相对路径相对于配置文件。不要提交私人配置；插件目录内的 `local-binding.json` 已被忽略。

Rhino、QGIS、AutoCAD 的连接使用你安装的对应工具。插件未携带这些软件、MCP 服务或许可证。`doctor` 可以检查已配置的路径及可选的 QGIS TCP 端口，但不会打开软件，也不会把 TCP 可通认作 MCP 认证成功。调用前仍需检查实际文档和连接。

## Rhino 8 交换副本

```sh
python3 -m pip install -r <plugin>/requirements-rhino.txt
python3 <plugin>/scripts/city_design.py export-rhino8 source.3dm target_Rhino8.3dm
```

输出包括 `.3dm` 和 `.verification.json`。检查读取到的几何记录、属性、图层、材质、图块、组、视图、单位和容差。数值序列化变化仅在严格核对 BRep 各裁剪面、边线、顶点后才可能接受；所有例外均记录。

中断时保留 `.pending.3dm` 与 `.pending.json`，同一输入可重新核对后继续；来源不同、已有目标被修改或来源不明时停止。不要删除日志后盲目重跑。SDK 不保证未识别的自定义插件数据、Rhino 9 独有内容或渲染环境完整，应在目标 Rhino 桌面版本另行验收。

## 历史原生案例

`assess-run --prefix <id>` 复核指定项目里符合原回执结构的保存记录。`run-synthetic --prefix <new-id> --execute` 是保留的历史适配入口，需要该项目自行提供 `scripts/run_mac_micro_workflow.py`、运行环境和软件连接。这些私人适配器不包含在公开包中。公开试用请运行 `demo`。

## 常见结果

| 结果 | 含义与下一步 |
|---|---|
| `NEEDS_CONFIGURATION` | 核心程序可用；配置项目或直接运行独立示例 |
| `SOURCE_REQUIRED` / `BLOCKED` | 缺少某项图纸依据，补齐对应事实后复核 |
| 目标已存在 | 保护已有文件；先核对版本，或使用新输出位置 |
| 连接工具不可用 | 配置并验证对应软件连接，保留当前文件 |
| Rhino 8 能打开但显示不同 | 检查着色/渲染模式与自定义插件，保留原始高版本文件 |

Windows/Linux 的 Python 核心检查与 macOS 原生软件操作是不同验收范围。请以验证记录为准。
