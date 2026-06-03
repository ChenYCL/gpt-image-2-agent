# gpt-image-2-agent

这是一个 OpenClaw 技能集合仓库，包含各种实用的 agent skills，帮助扩展 OpenClaw 的能力。

## 📚 技能列表

### [gpt-image-2-agent](./gpt-image-2-agent/)

Generate or edit images with OpenAI's gpt-image-2 model. Supports text-to-image, image-to-image editing, reference composition, and mask-based inpainting. Saves images locally and returns their file paths for integration with other agents/tools.

## 🚀 如何使用

### 方法 1：直接使用源代码

1. Clone 这个仓库：
   ```bash
   git clone https://github.com/ChenYCL/gpt-image-2-agent.git
   cd gpt-image-2-agent
   ```

2. 使用具体的 skill：
   ```bash
   cd gpt-image-2-agent
   # 按照 SKILL.md 说明使用
   ```

### 方法 2：安装到 LobeHub

将 skill 复制到 LobeHub 的 skills 目录：

```bash
cp -r gpt-image-2-agent ~/.lobeagent/workspace/skills/
```

## 📝 Skill 概述

**gpt-image-2-agent** 是一个强大的图像生成和编辑 skill，基于 OpenAI 的 `gpt-image-2` 模型。

### 主要功能

- **文本到图像（Text-to-Image）** - 从文本描述生成图像
- **图像编辑（Image Editing）** - 编辑和转换现有图像
- **引用合成（Reference Composition）** - 从多个引用图像合成新图像
- **区域修复（Inpainting）** - 使用遮罩修复图像的特定区域
- **本地保存** - 所有结果保存为本地文件，方便与其他 agents 集成

## 💡 使用场景

- 创建营销物料和海报
- 设计 UI/UX 原型
- 生成产品展示图
- 编辑和转换照片
- 创意内容生成

## 📄 许可证

MIT License

## 🤝 贡献

欢迎贡献新的 skills 或改进现有的 skills！提交 Pull Request 或 Issue 来帮助我们改进。

---

**注意：** 这些 skills 是为 LobeHub AI 助手设计的。
