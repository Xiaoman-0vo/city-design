# City Design · Alpha

面向 **Codex** 的城市设计工作流插件：用现场照片、总平面和已有模型组织可编辑的城市分析底模，并保留对象编号、资料依据和检查记录。

当前版本 **0.3.0-alpha.2**。核心检查与合成示例可以独立运行；连接 Rhino、QGIS、AutoCAD 需要另行配置对应软件和工具。实际场地定位与尺寸仍需单独校核。

## 能做什么

- 按“地面格局 → 建筑定位 → 入口、围栏与绿化 → 细化”组织建模。
- 保留每张照片的独立角度和原始相机信息，区分照片证据与暂定几何。
- 创建不依赖私人资料的四栋建筑示例，输出平面预览、参数和核对记录。
- 检查 7 条已映射的制图清单规则，缺少依据时明确报告。
- 可选：生成 Rhino 8 示例文件，或将受支持的 3DM 几何导出为 Rhino 8 副本并重新读取核对。

模型对象的管理和程序检查已实现；通用场地自动识别、任意建筑自动对齐、全场照片一致性、完整报批合规尚未实现。

## 安装到 Codex

需要支持插件的 Codex 版本。使用你的 Codex CLI：

```sh
codex plugin marketplace add Xiaoman-0vo/city-design --ref main
codex plugin add city-design@city-design-public
```

也可以先下载源码，再将本仓库的本地目录添加为 marketplace。安装后在新对话中说：

> 使用 City Design 检查这个场地项目，先核实已有文件，再按地面格局推进模型。

安装插件后可使用新增的[连接安装工具与完整说明](plugins/city-design/docs/CONNECTIONS.md)：校验并准备 QGIS 两端组件、生成 Rhino/QGIS 配置、保留现有 MCP 条目并验证连通。Rhino 使用 McNeel 官方组件，QGIS 使用社区组件；AutoCAD 官方 MCP 当前限定 Windows/Autodesk Assistant，不能承诺 Mac/Codex 直接控制。三款软件和许可需自行安装。首次运行见[使用说明](plugins/city-design/docs/USAGE.md)。

## 先试独立示例

Python **3.11–3.13**；核心功能只用标准库。以下命令在仓库根目录执行，Windows 可将 `python3` 换为 `python`。

```sh
python3 plugins/city-design/scripts/city_design.py doctor
python3 plugins/city-design/scripts/city_design.py demo --output ./demo-project
python3 plugins/city-design/scripts/city_design.py --project ./demo-project check-drawing --manifest drawings/master_plan_complete.json
python3 -m unittest discover -s plugins/city-design/tests
```

第一次 `doctor` 显示 `NEEDS_CONFIGURATION` 是可操作的配置提示；独立示例可以继续运行。打开 `demo-project/outputs/plan.svg` 看平面图。示例把四栋楼的楼层从 10/10/10/10 调整为 8/12/8/12，示例楼面面积保持 20,000 m²。所有尺寸均为合成数据。

若要生成或转换 3DM，请在自己的虚拟环境内安装可选依赖：

```sh
python3 -m pip install -r plugins/city-design/requirements-rhino.txt
python3 plugins/city-design/scripts/city_design.py demo --output ./demo-rhino --with-rhino
python3 plugins/city-design/scripts/city_design.py export-rhino8 source.3dm output_Rhino8.3dm
```

导出拒绝覆盖原件或未知的已有目标文件。生成检查记录后，再由接收者在 Rhino 8 中核对显示和特殊插件内容。SDK 检查不等于 Rhino 8 桌面程序验收。

## 验证与适用范围

- [验证记录](plugins/city-design/docs/VALIDATION.md)：区分本机执行、自动测试和未验证项目。
- [工作流技能](plugins/city-design/skills/design-workflow/SKILL.md)：代理如何组织操作与判断。
- [交付与恢复](plugins/city-design/references/delivery-and-recovery.md)：版本、保存冲突、用户修改与导出核对。
- [贡献说明](CONTRIBUTING.md)：如何报告可复现问题、提交新能力及保留适用边界。

历史三软件案例的说明与部分摘要保留在插件中；它们依赖的私人资料不随仓库发布，也不代表任意项目通过验收。标准索引是带日期的资料，正式出图前应核实当前版本与当地采用要求。

## 许可证

[MIT](LICENSE)。第三方软件、标准原文、相机照片和用户项目各自保留其授权条件。本仓库仅提供自编程序、工作流、摘要和合成示例，不打包设计软件或第三方标准 PDF。
