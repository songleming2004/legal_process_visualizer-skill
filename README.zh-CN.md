# 法律程序可视化 Skill

[English](README.md) | [简体中文](README.zh-CN.md)

这是一个供 Codex 使用的、可编辑且重视依据可追溯性的法律程序可视化 skill。它可用于研究、建模、创建、修改和检查诉讼、仲裁、行政、监管、上诉、执行、证据、期限及法律关系图。

## 能做什么

- 绘图前先建模主体、触发事件、行为、期限、依据、结果、分支、例外和不确定性。
- 创建保留文本、描述性 ID、可复用样式和 marker 箭头的可编辑 SVG。
- 在图内显示法律依据，并可为需要审计的项目建立“节点—来源”索引。
- 用明确线义区分程序状态变化、条件路径、说明关联和模块边界。
- 在渲染前检查连接线身份、端点贴合、进出方向、穿越无关节点及模块边界碰撞。
- 支持概览级、条文级、实务级和高密度学习长图四种详细程度。

## 安装

克隆仓库：

```bash
git clone https://github.com/songleming2004/legal_process_visualizer-skill.git
```

将 skill 内容复制到 Codex 的 skills 目录。安装后的文件夹名称请保留为 `legal-process-visualizer`：

```bash
mkdir -p ~/.codex/skills/legal-process-visualizer
rsync -a --exclude .git --exclude 'README*' legal_process_visualizer-skill/ ~/.codex/skills/legal-process-visualizer/
```

如果 Codex 没有立即识别，请重启或重新加载 Codex。

## 使用

可以显式调用：

```text
$legal-process-visualizer
仅以这份判决为依据，制作三张可编辑 SVG：跨法域案件时间线、程序与裁判路径图、股权转移及救济关系图。
```

也可以直接要求制作程序流程图、诉讼时间线、决策树、带依据的图表，或者修改现有的可编辑法律 SVG。

## 连接线契约

每条带箭头的连接线都必须声明来源节点、目标节点和两端所连接的边：

```svg
<path id="edge-application-order"
      class="connector"
      d="M320 300 V380"
      data-from="application"
      data-to="service-order"
      data-from-side="bottom"
      data-to-side="top"/>
```

端点必须落在声明的节点边界上；第一段线必须从来源节点向外离开，最后一段线必须从外部朝目标节点进入。这样可以在第一次渲染前发现“箭头指向空白处”或看起来属于相邻标题、相邻节点的问题。

## 校验

渲染前校验单个 SVG 或一个目录：

```bash
python3 scripts/validate_svg.py path/to/diagram.svg
python3 scripts/validate_svg.py path/to/svg-directory
```

以下问题会直接导致校验失败：缺少连接线元数据、端点脱离节点、进出方向错误、穿越无关节点、模块边界穿过节点。自动检查不能替代法律来源核对和连接密集区域的放大目检，两者都要做。

还可以使用 Codex `skill-creator` 自带的校验器检查整个 skill 包：

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py .
```

## 仓库结构

```text
SKILL.md                                  核心工作流和交付要求
assets/editable-legal-flow-template.svg   可编辑 SVG 起始模板
references/connector-integrity.md         连接线契约和检查规则
references/editable-svg-standard.md       SVG 制作与渲染标准
references/legal-*.md                     法律建模和来源处理指引
scripts/validate_svg.py                   结构与连接线校验器
```

## 范围说明

本 skill 用于辅助法律研究整理和可视化表达，不能替代特定法域的法律意见。来源范围有限、期限存在争议、依据无法取得或图中有意省略某条路径时，应在图内或交付说明中明确标注。
