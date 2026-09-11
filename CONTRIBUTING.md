# Contributing

欢迎以可复现问题和小型示例改进 City Design。

提交问题时提供：系统与 Python/软件版本、命令或操作步骤、预期与实际结果、脱敏后的最小输入。不要在 issue 中上传密钥、私人路径、原始照片 GPS 或未获授权的项目文件。

修改检查器或导出器时，为实际失败增加正例和反例。运行：

```sh
python3 -m unittest discover -s plugins/city-design/tests
python3 tools/check_release.py
```

涉及 3DM 时安装 `plugins/city-design/requirements-rhino.txt` 再运行测试；否则 3DM 测试会明确跳过。原生 Rhino/QGIS/AutoCAD 验证需单独记录软件版本和回读结果，不能用离线测试替代。

新增工作流说明需写明适用场景、依据、已验证范围和未决问题。优先提交自编合成示例，避免把某个场地的尺寸、道路角度或用户审美当成通用规则。

提交的原创贡献按本仓库 MIT 许可证分发。第三方内容应明确来源与许可；不要直接提交标准全文或软件安装包。
