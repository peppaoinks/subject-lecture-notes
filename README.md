# Subject Lecture Notes

这个 skill 用来把 PPT、教材和笔记整理成中文课程讲义。先确定读者程度、讲解深度和版式，再按完整章节补充到同一份源文件和 PDF 中，方便后续继续写或修改。

讲义会沿用你提供的资料中的字母和公式约定，补足理解所需的解释、推导、例题及练习。写数学、编程或人文课程时，按学科选择合适的讲解方式。

[交互示例](examples/体验示例.html) · [案例资料](examples/案例资料.md) · [资料回执](examples/资料回执.md) · [验证记录](examples/验证记录.md)

想先看效果，可以下载仓库，用浏览器打开 `examples/体验示例.html`。里面可以搜索内容、换颜色、调字号和行距，也能展开答案、复制代码、导出反馈。页面在本地运行，无需启动网络服务；GitHub 的文件页只显示源码。

![阅读示例：衬线正文、LaTeX 公式、习题与答案](examples/阅读预览.jpg)

数学内容使用独立的公式排版。比如截图中的练习，给定 $P(B)=0.5$ 和 $P(A\cap B)=0.2$，求 $P(A\mid B)$。先确认分母为正，再代入：

$$
P(A\mid B)=\frac{P(A\cap B)}{P(B)}=\frac{0.2}{0.5}=0.4.
$$

## 开始使用

将整个目录放进 Codex 的技能目录，目录名保留为 `subject-lecture-notes`。默认路径是 `~/.codex/skills/subject-lecture-notes/`；如果设置了 `CODEX_HOME`，则放在它的 `skills/` 子目录。更新已有安装时，先检查自己改过的文件。

安装后，可以这样开始：

```text
使用 $subject-lecture-notes，根据我提供的PPT编写课程讲义。
面向大一学生，保留PPT里的字母和公式约定，只用我提供的资料。
先给我一段能看出讲解深度与排版的样稿，再按完整章节累计交付。
```

后续写作直接沿用已有约定：

```text
继续下一章，沿用已确定的资料、符号、深度和版式。
```

```text
只补第二节推导，保留例题、符号和其他段落，给我修改前后对照。
```

## 能做什么

| 功能 | 怎么用 | 对应文件或工具 |
|---|---|---|
| 保存偏好 | 读者、深度和版式确定后，下一章继续沿用；临时默认值会注明 | 启动约定模板与写作流程 |
| 核对资料 | 列出实际读到的范围、原页出处和疑问，保留符号表 | 资料回执模板与资料规则 |
| 先写样稿 | 选资料中一个有代表性的知识点，看看深度和版式是否合适，再按反馈调整 | 样稿流程与三组自编案例 |
| 调整排版 | 修改颜色、字体、字号、行距、缩进和页边距 | LaTeX 模板与排版偏好 |
| 润色文字 | 保留专业语气，删去空泛和重复的表达；有 humanizer 时调用，也有内置规则 | 专业润色规则 |
| 局部修改 | 修改前保存快照，修改后查看差异，需要回退时先生成恢复预览 | `project_tools.py` |
| 继续工作 | 记录每章写到哪一步，重新打开项目后接着处理 | 同上，项目内 `.lecture/state.json` |
| 复用实验结果 | 比较输入、输出文件和环境标识，判断已有结果是否仍可使用 | 同上，文件 SHA-256 摘要 |
| 查找内容 | 用 PDF 的术语和题答链接，或在 HTML 阅读版中搜索、留下反馈 | LaTeX 模板与 `build_reader.py` |

资料读取、公式的视觉核对、正文写作和内容检查由 agent 完成。配套脚本负责保存状态、比较文件和生成阅读版，不会自动理解 PPT 或评价讲解质量。章节状态应在实际检查完成后更新。

## 项目辅助工具

配套脚本仅使用 Python 3.9+ 标准库。下面的命令在仓库根目录运行，将 `我的讲义` 换成自己的项目路径。

```bash
python3 scripts/project_tools.py init --project 我的讲义
python3 scripts/project_tools.py progress --project 我的讲义
```

初始化会补齐缺少的约定和排版偏好文件，已有文件保持原样。你可以直接编辑这些 Markdown 文件，agent 后续会读取其中的设定。

修改前创建快照：

```bash
python3 scripts/project_tools.py checkpoint --project 我的讲义 --files 源文件/学科讲义.tex 讲义编写约定.md --note '补充推导前'
```

命令返回的 `id` 是快照编号。用这个编号查看差异，或生成恢复预览：

```bash
python3 scripts/project_tools.py diff --project 我的讲义 --snapshot 快照编号
python3 scripts/project_tools.py restore-preview --project 我的讲义 --snapshot 快照编号
```

恢复预览保存在单独目录中，当前文件保持原样。确定要回退哪些内容后，agent 先保存最新快照，再把核对过的内容写回。PDF 等二进制文件会报告是否变化，不提供逐行文字对照。

写完或检查完一章后，可以记录当前阶段：

```bash
python3 scripts/project_tools.py progress --project 我的讲义 --chapter ch01 --title 第一章 --stage 草稿 --next 核对例题与符号
```

可选阶段为计划中、草稿、内容已核对、排版已核对、已交付。需要说明检查依据时，使用 `--evidence`。

实验运行后，记录输入、产物和实际环境标识，方便下次检查结果能否复用：

```bash
python3 scripts/project_tools.py cache-record --project 我的讲义 --name experiment01 --files 配套实践/experiment.py 数据/input.csv --outputs 配套实践/result.txt --environment '填入实际解释器和依赖版本'
python3 scripts/project_tools.py cache-check --project 我的讲义 --name experiment01 --environment '填入同一实际环境标识'
```

工具会检查记录中的文件和环境标识是否一致。实验方法是否合理、环境里是否还有未记录的变化，需要另行核对。

## 可选阅读版

```bash
python3 scripts/build_reader.py --input examples/reader-data.json --output 阅读示例.html
```

阅读版使用白底纸张、衬线正文和独立题号，公式由内置 KaTeX 排版。脚本、样式和数学字体全部写进生成的 HTML，打开时无需联网或安装额外依赖。

输入为结构化章节 JSON，可参考示例中的 `chapters`、`sections`、`paragraphs`、`exercises`。正文、题干和答案用 `\(...\)` 标记行内公式、`\[...\]` 标记独立公式；单独的公式块使用 `equation_latex`。JSON 中的反斜杠需要写成两个，例如：

```json
{
  "paragraphs": ["只有 \\(P(B)>0\\) 时，才能使用下面的公式。"],
  "equation_latex": "P(A\\mid B)=\\frac{P(A\\cap B)}{P(B)}"
}
```

普通文本和原有的 `equation` 字段仍可使用，代码按原文显示。不支持的公式会显示原始表达式并标记错误，需核对后修正。KaTeX 支持常见数学命令，不会编译完整 LaTeX 文档或任意宏包；图示和整部 PDF 的转换仍需另行处理。

你在阅读版里调整的排版和填写的反馈会保存在当前浏览器，可以下载为 JSON，也可以复制文本。如果浏览器限制自动复制，页面会选中文本供手动复制；下载受限时仍能导出文本。

把导出的内容交给 agent 后，再同步到正式讲义。阅读页面本身只调整阅读版，不会改写源文件，也不会把反馈发给外部服务。

## 资料怎么处理

开始写作时，agent 会先询问是否有 PPT、教材、大纲或笔记。如果提供资料，讲义会严格沿用其中的字母、大小写、上下标、正负号、单位和公式约定，并向你说明这一点。

遇到疑似错误、资料冲突或看不清的字符，会标出原位置，集中询问需要确认的问题。无法辨认的关键字符需先确认，再写入讲义。是否补充网络资料由你决定，补充内容和原资料分别记录。

humanizer 用于润色解释性文字，保留专业语气、事实、公式、引用、代码、限定条件和必要步骤。它是可选工具，文字质量以实际阅读和内容核对为准，不用文本检测器分数衡量。

## 仓库结构

```text
subject-lecture-notes/
├── SKILL.md
├── README.md
├── agents/openai.yaml
├── assets/       # 启动、资料回执、排版与阅读模板
├── references/   # 按需读取的规则
├── scripts/      # 项目工具与阅读版生成器
├── tests/        # 工具行为核对
└── examples/     # 自编资料、回执、交互示例与验证记录
```

## 设计参考

保存并复用输入的做法参考了 [Cookiecutter](https://cookiecutter.readthedocs.io/en/stable/advanced/replay.html)，资料出处的记录参考了 [Docling](https://docling-project.github.io/docling/concepts/docling_document/)。阅读工具和版本对照分别参考 [Quarto](https://quarto.org/docs/books/book-output.html) 与 [Anthropic skills](https://github.com/anthropics/skills/blob/main/skills/skill-creator/eval-viewer/viewer.html)。这些项目提供设计参考，使用本 skill 无需安装它们。

## 许可与署名

本项目由 peppaoinks 发布，采用 [MIT 许可证](LICENSE)。允许使用、修改和分发，包括商用；分发时需保留版权与许可声明。具体条款见许可证文件。

公式排版使用 [KaTeX](https://katex.org/)，其版权与 MIT 许可保留在 [第三方许可文件](assets/vendor/katex/LICENSE) 中，并随生成的阅读页一起提供。
