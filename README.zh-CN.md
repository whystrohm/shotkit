<h1 align="center">Shotkit</h1>

<p align="center"><strong>先把整支视频规划好，再去生成第一帧。</strong><br>
Claude Code 的 AI 分镜技能包。一句需求，或者一个装着你自己素材的文件夹，<br>
变成一块看板：每个镜头都已规划、写好提示词、并经过检查。</p>

<p align="center"><a href="README.md">English</a> · <strong>简体中文</strong></p>

![Shotkit Canvas 演示从脚本创建分镜、标注画面、调整镜头顺序，并对比 WhyStrohm 影片的横版和信息流版。](docs/images/workspace-demo.gif)

三个已完成的案例，点击图片打开在线看板。

| Media Tsunami · 16:9 | 屋顶工程公司 · 16:9 | 软件发布 · 9:16 |
|---|---|---|
| [![Media Tsunami 看板](docs/images/example-whystrohm-media-tsunami.jpg)](https://whystrohm.com/shotkit/examples/whystrohm-media-tsunami/board.html) | [![Kestrel Roofing 看板](docs/images/example-kestrel-roofing.jpg)](https://whystrohm.com/shotkit/examples/kestrel-roofing/board.html) | [![Brightdock 看板](docs/images/example-brightdock.jpg)](examples/brightdock) |

六个 Claude 技能加一组小工具，由 [WhyStrohm](https://whystrohm.com) 开发。
Apache 2.0 开源，免费。仓库里不带任何密钥。

## 为什么需要它

图像和视频生成模型一次只出一个片段。一支 30 秒的视频是八个必须互相对得上的镜头：
同一个人、同一个场景、同一种光线、同一个品牌，文字还要放得进画面。
一个一个地写提示词，第五个镜头就和第二个对不上，品牌色会跑偏，
而且直到剪辑时才有人认真看每一帧。

Shotkit 做的是生成之前的那一步：

- **规划每个镜头**：时长、景别、运动和画面文字，按叙事框架排好。
- **锁定不能变的东西**：整支视频共用的人物、场景、光线和调色，以及品牌的颜色和字体。
- **为每个镜头写提示词**：支持十个图像和视频生成模型，各用各的格式。
- **检查每一帧**：对照镜头和品牌，指出要改什么，只重做那一个镜头。
- **优先用你自己的素材**：指向一个照片和视频的文件夹，它逐个查看、放到合适的镜头上，只把缺的部分留给生成模型。
- **全部放在一块看板上**：在浏览器里打开，每段内容都能一键复制给任何模型。

Shotkit 插件负责规划镜头、检查画面并生成粗剪。Canvas 支持在本机审阅、调整镜头与准备交接文件。

## 试用 Canvas

在预览发行版的 **Assets** 中下载 `shotkit-canvas-*.zip` 和对应的校验文件。
GitHub 的 **Source code** 压缩包包含插件与 CLI。 [GitHub Releases](https://github.com/whystrohm/shotkit/releases)

在下载目录校验并解压。macOS 需要 Python 3.10 或更高版本。

```sh
shasum -a 256 -c shotkit-canvas-v3.7.0-rc.2.zip.sha256
unzip shotkit-canvas-v3.7.0-rc.2.zip
cd shotkit-canvas
./start.sh --isolated --open --port 0
```

在主页打开 **WhyStrohm · How it works**，可以播放影片、比较横版与信息流版，
也可以在画面上添加批注。**The flight of Apollo 11** 展示长片的章节导航。

如需连接 Claude，运行 `./start.sh --open`，进入 **Settings and keys → Claude**，
粘贴 API 密钥并选择 **Save and check**。密钥保存在 macOS 钥匙串中。
[Claude Console](https://platform.claude.com/settings/keys)

Codex 可以通过 MCP 连接本机工作区。 [Codex 设置](README.md#use-canvas-from-codex)

## 安装

在 Claude Code 里：

```
/plugin install shotkit --marketplace whystrohm/shotkit
```

然后输入需求：

```
/shotkit:shotkit 为我们的新应用做一支 30 秒的发布视频，9:16
```

需要 Claude Code 2.1.275 或更高版本。旧版本请先运行
`/plugin marketplace add whystrohm/shotkit`，再运行 `/plugin install shotkit@shotkit`。

也可以用安装脚本，这样可以用更短的 `/shotkit` 命令：

```bash
git clone https://github.com/whystrohm/shotkit.git
cd shotkit && ./install.sh
```

### 在 Canvas 中打开项目

安装支持工作区 API 1 的 Shotkit Canvas 后，可通过 CLI 打开项目。
从仓库运行时使用 `tools/sk`。运行 `./install.sh` 后，使用以下路径。

```bash
~/.claude/shotkit-tools/sk workspace "/path/to/project" \
  --runtime "/path/to/shotkit-canvas" --open
```

项目目录和它的 `output/` 目录指向同一次工作记录。设置
`SHOTKIT_CANVAS_HOME` 后可省略 `--runtime`。`--rules-only`
可在无需连接 AI 的情况下审阅。`--port 0` 会选择可用的本地端口。
`--isolated` 跳过对其他项目和已保存密钥的查找。
插件自带的便携看板仍可通过 `sk board output/ --open` 打开。

Python 3.10 或更高版本可打开主页、分镜和已经完成的示例影片。
如需预览可编辑剪辑，请在 Canvas 目录运行
`npm install` 和 `npm run build`，然后重启 Canvas。

## 从你已有的素材开始

```
/shotkit:shotkit 用 ~/Desktop/shoot 里的照片和视频做一支 30 秒的视频，9:16
```

Claude 会查看每一张照片和每一段视频，把它们放到合适的镜头上，并标出缺少的部分。
生成模型只负责补缺；两个接不上的镜头之间，可以生成一段过渡片段。
你的原始文件不会被移动或修改。详见 [docs/own-media.md](docs/own-media.md)（英文）。

## 生成画面和视频片段

用你自己的 fal.ai 密钥，`sk generate` 可以生成静帧和视频片段并归档。
密钥只放在你的环境变量或被 git 忽略的 `.env` 文件里。
不加 `--yes` 不会发送任何请求。详见 [docs/generate-with-fal.md](docs/generate-with-fal.md)（英文）。

## 看板

一次运行对应一个页面：输出文件夹里的单个 HTML 文件，可以离线打开，不上传任何内容。

- **一眼看到所有镜头**：缩略图总览和时间线，镜头、屏幕文字、旁白各占一条轨道。
- **提示词带复制按钮**：每个生成模型一个标签页，按 `C` 复制当前这条。
- **每一帧的评审结论**：哪里可以、哪里不行、怎么改。之前几轮的结果也都留着。
- **实时模式**：`sk board output/ --serve` 会随文件变化自动刷新。把画面拖到镜头上即可保存；
  拖动镜头上的文字可以调整位置，文字不会超出安全区。
- **安全区**：一个开关，显示竖屏视频里会被应用界面挡住的区域。
- **给客户看的页面**：`preview.html` 是同一份计划的简洁版本，看板上的 **PDF** 按钮可直接打印。
- **导出**：`sk export output/` 生成带文字的轮播图片、一份 PowerPoint 和一个粗剪视频。见 [`docs/export.md`](docs/export.md)。

## 六个技能

| 技能 | 作用 |
|---|---|
| `shotkit` | 入口。一句需求，从计划做到看板 |
| `storyboard-architect` | 规划每个镜头，写出 `shots.json` |
| `visual-prompt-forge` | 为每个镜头、每个生成模型写提示词 |
| `visual-asset-critic` | 对照镜头和品牌检查每一帧 |
| `storyboard-html-preview` | 生成看板和客户预览页 |
| `brand-lock-extractor` | 从网站、PDF 或截图读出品牌的颜色、字体和语气 |

## 数据去哪了

便携看板和检查在电脑本地运行。Canvas 的服务仅监听本机。
使用 Claude Code 规划和评审时，Claude 会收到读取的需求、品牌资料和素材。
连接 Claude Console 后，Canvas 聊天会发送请求和相关项目内容。
使用 fal.ai 生成素材需要使用自己的密钥并确认请求。 [安全与数据](SECURITY.md)

## 人工确认

评审结论是模型给出的。有人确认之后，把这件事也记下来：

```bash
~/.claude/shotkit-tools/sk approve output/ --by "姓名"                 # 确认计划
~/.claude/shotkit-tools/sk approve output/ --by "姓名" --what frames   # 确认已通过的画面
```

每次确认都是 `output/approvals/` 里的一个新文件，用哈希记录确认的是哪一版。
之后内容有变，看板和 `sk validate` 会提示这次确认已失效。名字是手动输入的，
所以这是一条记录，不是签名。

## 输出

便携看板可以导出镜头表、幻灯片和粗剪。Canvas 可以审阅和调整剪辑，
并将带时间信息的镜头表和字幕交给剪辑师。 [导出](docs/export.md)

## 文档

完整文档为英文：[README](README.md) · [快速上手](https://whystrohm.com/shotkit/docs/quickstart) · [更新日志](CHANGELOG.md)

## 许可

Apache 2.0。见 [LICENSE](LICENSE)。

## 开发者

Shotkit 由 WhyStrohm 的 Yuri Strohm 创建和维护。OpenAI Codex 和 Anthropic
Claude 协助实现与审查。Canvas 的设计也经过 Astra 审查。
