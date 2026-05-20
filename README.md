# zero-api-html-image

用 HTML/CSS 模板和浏览器截图生成图片的 Codex skill。不调用生图 API，适合把结构化内容稳定地渲染成中文视觉图。

## 适合场景

- 总结文档内容，生成可读性强的图文卡片
- 生成可视化数据复盘报告、经营分析图、对比图
- 制作小红书封面、文字卡片、知识地图、咨询报告页
- 在 Codex、Hermes、OpenClaw、云端部署环境中复用同一套模板

## 优势

- 不依赖生图 API，内容更可控，文字不容易变形
- HTML/CSS 模板可维护、可复用、可审查
- 浏览器截图链路通用，适合本地和云端环境
- 模板、数据、渲染脚本都在包内，方便迁移

## 使用

下载 `zero-api-html-image.tar.gz` 后解压到 skill 目录，进入目录运行：

```bash
python3 quick_validate.py
python3 scripts/doctor.py
```

生成图片时遵循 `SKILL.md` 的交互规则：先确认标题，再确认署名；选择模板时只展示总览图；新模板或大改模板先出候选图确认。

## 当前发布形式

这个仓库当前提供可安装压缩包：`zero-api-html-image.tar.gz`。压缩包内包含完整 skill 源码、模板、演示数据、脚本和文档。
