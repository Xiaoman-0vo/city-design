# Unreleased — site analysis maps

- Add a site-analysis-maps skill for native-pixel RGB vegetation grids, building-only VGA and model-ground winter/summer direct-sun duration.
- Add reusable RGB-mask aggregation and transparent grid-plate helpers, configurable crop/opacity, white buildings and a coordinated blue/red palette.
- Record real-case numerical and output checks while keeping survey accuracy, vegetation seasonality and measured access/irradiance outside the validated claims.

# 0.3.0-alpha.2 — 连接安装工具

- 核实并区分 Rhino 官方 MCP、QGIS 社区 MCP、AutoCAD 官方 Windows/Assistant 路线与 Autodesk 文档服务。
- 新增固定提交、SHA-256 校验的 QGIS 两端下载与锁文件安装，保留上游源码和 GPL 许可。
- 新增本机配置生成、令牌文件启动器、仅添加缺失条目的 Codex 注册与备份。
- 新增 MCP 初始化、工具发现、ping、版本一致性检查，保留模型验收边界。

# 0.3.0-alpha.1 — 公开实验版

- 私人路径改为可选配置；未配置项目也能检查核心环境和运行独立示例。
- 新增受控项目初始化、四栋建筑示例、平面 SVG 和可选 Rhino 8 SDK 文件。
- 将兼容导出整理成通用入口，保护原件并核对几何、属性、图层、材质与视图。
- 测试使用临时合成资料，取消对私人项目的依赖。
- 缺少实体统计时报告缺少依据；修正重复控制点与临时目录路径解析。
- 新增 MIT 许可证、示例配置、GitHub marketplace、公开包检查和 CI。
- 保留历史原生执行入口与证据边界；未宣称通用自动建模或跨平台原生验收。

## 2026-09-11 — 地面格局先行与对象放置检查

将“先校核地面格局，再按街段/地块放置建筑及附属构件，最后细化”写入建模工作流。增加局部放置基准、依附构件同步、保存文件的道路冲突/接地/连接复核及地面改版后的重新校核。保留 v06 原生回读、俯视检查、实际占地与同参重跑证据；现场道路和照片准确性仍未全部验收。此版更新代理执行规则，未新增通用自动对齐引擎。

## 2026-09-11 — Photo site workflow precautions

Added original-metadata propagation, independent exposure poses, multi-view acceptance and observed Rhino Mac document/units/view failures. The site reconstruction remains experimental; this update does not promote full-site photo accuracy.

# City Design 实践版本记录

## 0.2.0 — 2026-09-09

- 新增 `assess-run`，把七阶段回执汇总为 6 组跨软件检查：阶段状态、指标、ID/楼层、控制点和原生文件。
- 新增 `check-drawing`，执行首批 7 条规划与电子报批清单规则，保存结构化检查报告。
- 电子报批坐标增加受理部门来源、非合成数据及三个非共线控制点门槛。
- 新增绘图清单 schema、通过/失败/采用性未确认三类样例，以及 7 项插件测试。
- 新增实践案例索引；仍将真实坐标、复杂建筑、原生图形扫描和完整合规检查列为未验证。

## 0.1.0 — 2026-09-09

- 用户命名为 City Design，建立个人插件及设计协作、中国制图标准两个技能。
- 接入已完成的 Mac 合成案例执行器与原生证据，保留原接管包作为当前执行项目。
- 登记 QGIS 专用 profile、Rhino Mac 文档绑定差异、AutoCAD 后台 PDF 驱动异常及主窗口打印的成功路径。
- 建立首批中国制图标准目录、状态区分和条款映射；未声称完整标准自动符合性。
- 维护采用案例与证据驱动更新；真实项目验证留待相应输入与实践。
