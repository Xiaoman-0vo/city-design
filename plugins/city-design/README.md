# City Design 0.3.0-alpha.2

照片辅助的城市分析底模工作流、可独立运行的合成示例、制图清单检查与 Rhino 8 交换副本导出。

从 `scripts/city_design.py doctor` 开始。没有私人项目也可以运行 `demo --output <new-directory>`。

- [使用与配置](docs/USAGE.md)
- [验证与边界](docs/VALIDATION.md)
- [设计工作流](skills/design-workflow/SKILL.md)
- [场地分析制图](skills/site-analysis-maps/SKILL.md)：RGB 绿色像元网格、建筑障碍 VGA、冬夏至模型日照与透明图件。
- [地面与放置](references/ground-layout-and-placement.md)
- [交付、兼容与恢复](references/delivery-and-recovery.md)

核心工具使用 Python 标准库；3DM 功能需要可选的 `requirements-rhino.txt`。软件连接需使用者配置，历史私人适配器未包含。保持可编辑原件并核对目标软件中的结果。

静态网格制图辅助程序使用可选的 `requirements-maps.txt`；VGA 和日照计算引擎的要求见对应方法文档。制图工具不替代原生分析计算，也不证明现场测量精度。

MIT 许可证见 [LICENSE](LICENSE)。不分发私人场地照片、模型、凭证或第三方标准全文。

连接安装与平台限制见 [CONNECTIONS.md](docs/CONNECTIONS.md)，支持固定来源准备 QGIS 两端、生成 Rhino 配置、保留已有 MCP 注册并核对连接。
