# 深入理解 AI Agent：设计原理与工程实践

本仓库是《深入理解 AI Agent：设计原理与工程实践》一书的开源主仓库，包含**全书正文**与**配套示例代码**。全书正文、配图与配套实验代码全部开源，欢迎把实验亲手跑一遍、提 issue 和 PR。

## 📖 电子书

全书正文与编译好的 PDF 位于 [`book/`](book/) 目录：

- **正文源码**：`book/introduction.md`（引言）、`book/chapter1.md` ~ `book/chapter10.md`（第一至第十章）、`book/afterword.md`（后记）
- **编译版 PDF**：[`book/book.pdf`](book/book.pdf)
- **自行编译**：安装 pandoc、xelatex、ElegantBook 文档类与相关字体后，运行

  ```bash
  cd book && bash build_pdf.sh
  ```

  图表由 `book/gen_*_figs.py` 生成、存于 `book/images/`，排版细节见 `book/preamble.tex` 与 `book/*.lua`。

本书的核心框架是 **Agent = 模型 + 上下文 + 工具**，下面的配套代码即围绕这一框架、按章节（周次）组织的可独立运行示例。

## 💻 配套代码

所有项目按周次组织，涵盖了从基础概念到高级技术的完整学习路径。每个项目都是可独立运行的完整示例。

## 🚀 Week 1 - Agent 基础

### 1. learning-from-experience - 强化学习 vs LLM 对比
`week1/learning-from-experience/`

对比传统强化学习（Q-learning）与基于 LLM 的上下文学习，复现 Shunyu Yao 的 "The Second Half" 博文中的关键洞察。通过寻宝游戏展示 LLM 如何以 250-400 倍的样本效率超越传统 RL。

**核心概念**：强化学习、上下文学习、样本效率、先验知识

### 2. web-search-agent - Kimi K2 模型即 Agent
`week1/web-search-agent/`

实现具备基础深度搜索能力的 Agent，能够进行多轮搜索和信息整合。

**核心概念**：网络搜索、模型原生 Agent

### 3. search-codegen - GPT-5 原生工具集成
`week1/search-codegen/`

构建能够基础深度搜索能力和代码沙盒能力的 Agent，综合利用网络搜索、代码执行等工具实现复杂分析。

**核心概念**：网络搜索、代码生成、模型原生 Agent

### 4. context - 上下文消融研究 
`week1/context/`

通过系统性的消融实验展示 Agent 上下文各个组件的重要性。支持多种 LLM 提供商（SiliconFlow Qwen、字节 Doubao、月之暗面 Kimi），配置不同的上下文模式观察 Agent 行为变化。

**核心概念**：上下文管理、工具调用、ReAct 循环、消融研究

## 🎯 Week 2 - 上下文工程与优化

### 1. local_llm_serving - 本地 LLM 部署与工具调用
`week2/local_llm_serving/`

跨平台的本地 LLM 部署方案，自动选择最佳后端（vLLM 或 Ollama）。展示即使 0.6B 的小模型也能通过良好的系统设计实现出色的工具调用能力。支持流式响应，实时显示思考过程。

**核心概念**：模型部署、Chat Template、流式处理、工具调用

### 2. attention_visualization - 注意力机制可视化
`week2/attention_visualization/`

可视化 LLM 的完整输入输出 token 序列和注意力权重分布，深入理解模型如何处理上下文、进行推理和调用工具。

**核心概念**：注意力机制、token 分析、推理过程可视化

### 3. kv-cache - KV Cache 友好的上下文设计
`week2/kv-cache/`

探索不同上下文管理模式对 KV Cache 的影响，演示常见的错误模式如何破坏缓存效率。通过实验展示正确的上下文设计如何显著降低延迟和成本。

**核心概念**：KV Cache、上下文优化、性能调优

### 4. context-compression - 上下文压缩策略
`week2/context-compression/`

实现并对比多种上下文压缩策略，包括摘要、关键信息提取、语义压缩等。在保持 Agent 能力的同时减少 token 使用量。

**核心概念**：上下文压缩、token 优化、信息密度

### 5. prompt-engineering - 提示工程消融研究
`week2/prompt-engineering/`

扩展 Tau-Bench 框架，通过系统性的消融实验量化不同提示工程因素对 Agent 性能的影响。展示语气风格、指令组织、工具描述等因素如何影响任务完成率。

**核心概念**：提示工程、消融研究、性能基准测试

### 6. system-hint - 系统提示优化
`week2/system-hint/`

研究系统提示（System Hint）对 Agent 行为的影响，探索如何通过优化系统提示提升性能。

**核心概念**：系统提示、行为引导、提示优化

### 7. user-memory-evaluation - 用户记忆评估框架
`week2/user-memory-evaluation/`

系统化评估用户记忆系统的准确性、相关性和有效性，包含多种测试场景和评估指标。

**核心概念**：评估框架、测试用例、性能度量

### 8. user-memory - 用户记忆系统
`week2/user-memory/`

构建长期用户记忆系统，让 Agent 能够记住用户偏好和历史交互，提供个性化服务。

**核心概念**：长期记忆、个性化、用户建模

### 9. log-sanitization - 日志脱敏处理
`week2/log-sanitization/`

实现智能的日志脱敏系统，在保留调试信息的同时保护敏感数据。

**核心概念**：隐私保护、日志处理、数据安全

## 📚 Week 3 - 知识库与学习机制

### 1. dense-embedding - 稠密嵌入向量检索服务
`week3/dense-embedding/`

构建向量相似性搜索服务，对比研究 ANNOY（基于树）和 HNSW（基于图）两种近似最近邻索引算法。展示不同索引策略在性能、内存占用和更新能力上的权衡。

**核心概念**：稠密嵌入、向量检索、ANN 算法、语义搜索

### 2. sparse-embedding - 稀疏检索引擎
`week3/sparse-embedding/`

从零实现基于 BM25 算法的稀疏向量搜索引擎，通过丰富的日志和可视化接口展示搜索引擎的内部工作机制，理解词频权重计算和倒排索引原理。

**核心概念**：稀疏嵌入、BM25、TF-IDF、精确匹配

### 3. retrieval-pipeline - 混合检索流水线
`week3/retrieval-pipeline/`

构建完整的检索流水线，结合稠密检索、稀疏检索和神经重排序。通过精心设计的测试用例，系统性展示混合检索在不同场景下的优势互补效果。

**核心概念**：混合检索、神经重排序、跨编码器、检索融合

### 4. multimodal-agent - 多模态信息提取
`week3/multimodal-agent/`

对比三种多模态处理策略：原生多模态处理、提取为文本、工具化分析。通过统一框架下的消融研究，揭示不同技术路径在保真度、成本和灵活性上的权衡。

**核心概念**：多模态、视觉理解、OCR、端到端处理

### 5. structured-index - 结构化索引
`week3/structured-index/`

实现并对比 RAPTOR（递归抽象树）和 GraphRAG（知识图谱）两种先进索引策略。通过索引技术手册演示如何构建反映知识内在层次和关联的结构化索引。

**核心概念**：RAPTOR、GraphRAG、层次摘要、知识图谱

### 6. agentic-rag - 智能体 RAG
`week3/agentic-rag/`

对比传统 Non-Agentic RAG 与 Agentic RAG 的性能差异。展示 Agent 如何通过 ReAct 模式主导迭代式信息检索，在处理复杂司法问答时显著提升答案质量。

**核心概念**：Agentic RAG、ReAct 循环、迭代检索、主动探索

### 7. agentic-rag-for-user-memory - 利用 Agentic RAG 构建用户记忆
`week3/agentic-rag-for-user-memory/`

将 Agentic RAG 框架应用于管理用户对话历史，通过多轮迭代搜索能力处理跨会话的记忆检索，实现基础回忆和多会话检索能力。

**核心概念**：用户记忆、对话历史索引、跨会话检索

### 8. contextual-retrieval - 上下文感知检索
`week3/contextual-retrieval/`

实现 Anthropic 提出的上下文感知检索技术，通过为文本块生成包含核心上下文的前缀摘要，解决传统分块方法的上下文丢失问题，将检索失败率降低 49-67%。

**核心概念**：上下文增强、前缀生成、语义锚定、检索优化

### 9. contextual-retrieval-for-user-memory - 上下文感知的用户记忆系统
`week3/contextual-retrieval-for-user-memory/`

将上下文感知检索技术应用于用户记忆构建，结合 Advanced JSON Cards 与上下文感知 RAG，形成双层记忆结构，实现更高层次的主动服务能力。

**核心概念**：双层记忆、结构化事实、上下文检索、主动服务

### 10. structured-knowledge-extraction - 结构化知识提取
`week3/structured-knowledge-extraction/`

从海量司法判例数据集中提取隐性知识，通过因子分析和重要性建模，构建判决经验模型。展示如何将数据中的隐性模式转化为 Agent 可用的结构化决策逻辑。

**核心概念**：知识发现、因子分析、数据驱动、判决建模

### 11. gaia-experience - 从成功经验中学习
`week3/gaia-experience/`

基于 AWorld 框架和 GAIA 基准测试，实现完整的"学习-应用"闭环。Agent 自动总结成功的任务轨迹为结构化经验，并在新任务中检索应用，实现自我进化。

**核心概念**：经验学习、策略摘要、轨迹总结、自我进化

### 12. browser-use-rpa - 工作流录制与回放
`week3/browser-use-rpa/`

实现浏览器自动化的工作流录制系统，将重复性操作序列自动封装为参数化工具。通过从昂贵的 LLM 推理切换到精确的自动化执行，实现 3-5 倍速度提升。

**核心概念**：工作流录制、RPA、工具生成、外部化学习

## 🛠️ Week 4 - 工具生态与系统集成

### 1. perception-tools - 感知工具 MCP 服务器
`week4/perception-tools/`

构建全面的感知工具集，提供网络搜索、多模态理解、文件系统操作和公共数据源访问能力。大部分功能基于免费开放 API（DuckDuckGo、Open-Meteo、Yahoo Finance、OpenStreetMap 等），无需 API 密钥即可使用。

**核心概念**：MCP 协议、多模态解析、公共数据源、文档理解、地理信息服务

### 2. execution-tools - 执行工具 MCP 服务器
`week4/execution-tools/`

实现具备安全机制的执行工具集，包括文件操作、代码解释器、虚拟终端和外部系统集成。通过 LLM 二次审批机制防止危险操作，自动摘要复杂输出，并对代码进行语法验证。

**核心概念**：MCP 协议、执行安全、LLM 审批、结果摘要、自动验证

### 3. collaboration-tools - 协作工具 MCP 服务器
`week4/collaboration-tools/`

提供全面的协作能力，包括浏览器自动化（browser-use 框架）、人机协同（Human-in-the-Loop）、多渠道通知（Email、Telegram、Slack、Discord）和定时器管理。支持敏感操作的管理员审批和定时任务调度。

**核心概念**：MCP 协议、浏览器自动化、HITL 模式、多渠道通知、定时任务

### 4. agent-with-event-trigger - 事件触发型 Agent 与 MCP 集成
`week4/agent-with-event-trigger/`

基于 FastAPI 构建的现代化事件驱动 Agent，默认集成前三个 MCP 服务器的所有工具。采用原生异步架构实现清晰的 MCP 工具加载，通过 HTTP API 接收多源事件（Web、即时消息、GitHub、定时器等）。提供自动 API 文档（Swagger UI）和后台监控能力。

**核心概念**：FastAPI、原生异步、MCP 集成、事件驱动、自动 API 文档、工具编排

### 5. active-tool-selection - 主动工具选择
`week4/active-tool-selection/`

实现智能工具选择机制，让 Agent 能够根据任务需求主动选择最合适的工具组合，而非被动接受预定义的工具集。

**核心概念**：工具选择、动态工具加载、任务分析

### 6. async-agent - 异步 Agent 架构
`week4/async-agent/`

展示如何构建真正的异步 Agent，支持并发任务处理、非阻塞 I/O 和高效的资源利用。

**核心概念**：异步编程、并发处理、事件循环、非阻塞 I/O

## 💻 Week 5 - Coding Agent：代码生成与编辑

### 1. coding-agent - 生产级 Coding Agent
`week5/coding-agent/`

基于 Claude 构建的生产级 AI 编码助手，实现了第二章中的所有技术，采用纯 Python 实现所有工具，无需命令行依赖。包含 17 个完整实现的工具，涵盖文件操作、搜索、Shell 操作和项目管理。特别实现了纯 Python 的 Grep 工具，完全兼容 ripgrep 的功能。

**核心特性**：
- 纯 Python 实现，无命令行依赖，特别适合 Mac 用户
- 完整的工具套件：文件读写编辑、纯 Python 正则搜索、目录列表、Shell 会话管理
- 系统提示技术：时间戳、工具调用计数、TODO 列表管理、详细错误信息
- 持久化 Shell 环境、自动 Lint 检测、流式响应支持
- 支持多个 LLM 提供商（Anthropic、OpenAI、OpenRouter）

**核心概念**：代码生成、文件编辑、纯 Python 工具、系统提示、Lint 检测、多提供商支持

## 🎯 Week 6 - Agent 评估基准

### 1. terminal-bench - 终端环境基准测试
`week6/terminal-bench/`

Terminal-Bench 是测试 AI Agent 在真实终端环境中表现的基准测试。从编译代码到训练模型、设置服务器，评估 Agent 如何处理真实的端到端任务。包含约 100 个任务的数据集和执行框架，支持多种 Agent 实现。

**核心概念**：终端自动化、任务评估、Docker 沙箱、基准测试

### 2. SWE-bench - 软件工程基准测试
`week6/SWE-bench/`

SWE-bench 是评估大语言模型解决真实 GitHub 问题能力的基准测试。给定代码库和问题描述，模型需要生成能够解决问题的补丁。包含 SWE-bench、SWE-bench Lite、SWE-bench Verified 和 SWE-bench Multimodal 多个版本。

**核心概念**：代码修复、GitHub 问题、补丁生成、Docker 评估

### 3. GAIA - 通用 AI 助手基准测试
`week6/GAIA/`

GAIA 旨在评估下一代 LLM（具有工具增强、高效提示、搜索访问等能力的 LLM）。包含 450+ 个需要不同程度工具和自主性的非平凡问题，答案明确无歧义。分为 3 个难度级别。

**核心概念**：工具使用、多步推理、自主性评估

### 4. OSWorld - 操作系统级 Agent 基准
`week6/OSWorld/`

评估 Agent 在完整操作系统环境中执行复杂任务的能力，包括文件管理、应用程序操作和系统配置。

**核心概念**：操作系统自动化、多应用协作、系统级任务

### 5. android_world / android-world - Android 环境基准
`week6/android_world/` 和 `week6/android-world/`

评估 Agent 在 Android 移动环境中的表现，包括应用导航、UI 交互和任务完成能力。

**核心概念**：移动自动化、Android UI、应用交互

### 6. tau2-bench - 工具增强推理基准
`week6/tau2-bench/`

专注于评估 Agent 使用工具进行复杂推理的能力，包括计算、搜索和数据处理等场景。

**核心概念**：工具增强推理、多步骤任务、工具组合

### 7. elo-leaderboard - ELO 排行榜系统
`week6/elo-leaderboard/`

实现基于 ELO 评分系统的 Agent 性能排行榜，通过对战比较来评估不同 Agent 的相对能力。

**核心概念**：ELO 评分、相对评估、排行榜系统

## 🧠 Week 7 - 模型后训练：SFT 与 RL

Week 7 包含多个模型后训练项目，涵盖监督微调（SFT）和强化学习（RL）的各种技术和应用场景。

### 1. AdaptThink - 自适应推理深度
`week7/AdaptThink/` 和 `week7/AdaptThink-original/`

让推理模型学会根据问题难度自适应选择推理模式（Thinking vs NoThinking）。通过约束优化和重要性采样，在大幅降低推理成本（45-69%）的同时提升准确率。基于 DeepSeek-R1-Distill-Qwen 模型，使用 DAPO 算法训练。

**核心概念**：自适应推理、推理成本优化、约束优化、重要性采样

### 2. retool - 工具增强数学推理
`week7/retool/`

使用多轮对话和代码沙箱提升大语言模型数学推理能力。通过 SFT 和 RL 两阶段训练，让模型学会使用代码执行环境辅助数学问题求解。基于 Qwen2.5-32B-Instruct，在 AIME 2024 数据集上训练，使用 DAPO 算法和 SandboxFusion 沙箱。

**核心概念**：工具使用、代码执行、数学推理、多轮对话、DAPO 算法

### 3. AWorld / AWorld-train - 具身 Agent 训练
`week7/AWorld/` 和 `week7/AWorld-train/`

基于 AWorld 框架训练具身 Agent，让 Agent 能够在虚拟环境中执行复杂任务并从经验中学习。

**核心概念**：具身智能、环境交互、经验学习

### 4. SFTvsRL - SFT 与 RL 对比研究
`week7/SFTvsRL/`

系统性对比监督微调（SFT）和强化学习（RL）在不同任务上的效果，分析两种方法的优劣和适用场景。

**核心概念**：SFT vs RL、训练方法对比、性能分析

### 5. verl - 高效 RL 训练框架
`week7/verl/`

verl 是专门为大语言模型 RLHF 训练设计的高效强化学习框架，支持 PPO、GRPO、DAPO 等多种算法。

**核心概念**：RLHF、PPO、分布式训练、高效优化

### 6. Intuitor - 直觉推理训练
`week7/Intuitor/`

训练模型的直觉推理能力，让模型能够快速做出合理判断而不需要详细的思考链。

**核心概念**：直觉推理、快速决策、思考链优化

### 7. MultilingualReasoning - 多语言推理
`week7/MultilingualReasoning/`

训练模型在多种语言环境下的推理能力，提升跨语言任务的表现。

**核心概念**：多语言、跨语言推理、语言泛化

### 8. SpatialReasoning - 空间推理训练
`week7/SpatialReasoning/`

专注于训练模型的空间推理能力，处理涉及位置、方向、距离等空间关系的问题。

**核心概念**：空间推理、几何理解、位置关系

### 9. SimpleVLA-RL - 视觉-语言-动作 RL
`week7/SimpleVLA-RL/`

结合视觉、语言和动作的强化学习训练，让模型能够理解视觉输入并执行相应动作。

**核心概念**：视觉-语言-动作、多模态 RL、具身智能

### 10. continued-pretraining - 持续预训练
`week7/continued-pretraining/`

在特定领域数据上进行持续预训练，提升模型在目标领域的表现。

**核心概念**：持续预训练、领域适应、知识注入

### 11. MiniMind-pretrain - 小型模型预训练
`week7/MiniMind-pretrain/`

从零开始预训练小型语言模型，理解预训练的完整流程和关键技术。

**核心概念**：预训练、小型模型、训练流程

### 12. prompt-distillation - 提示蒸馏
`week7/prompt-distillation/`

将复杂提示的效果蒸馏到模型参数中，减少推理时的提示长度。

**核心概念**：知识蒸馏、提示优化、参数化知识

### 13. feedback-guided-sampling - 反馈引导采样
`week7/feedback-guided-sampling/`

使用反馈信号引导模型的采样过程，提升生成质量和任务完成率。

**核心概念**：反馈学习、采样优化、质量控制

### 14. learn-from-observation - 观察学习
`week7/learn-from-observation/`

让模型从观察人类或其他 Agent 的行为中学习，无需显式标注。

**核心概念**：观察学习、模仿学习、行为克隆

### 15. sesame - 序列建模与评估
`week7/sesame/`

专注于序列建模任务的训练和评估方法。

**核心概念**：序列建模、评估方法、性能优化

### 16. orpheus - 音乐生成与理解
`week7/orpheus/`

训练模型的音乐生成和理解能力。

**核心概念**：音乐生成、音频理解、创意 AI

### 17. tinker-cookbook - 训练技巧集锦
`week7/tinker-cookbook/`

收集各种模型训练的实用技巧和最佳实践。

**核心概念**：训练技巧、最佳实践、调优方法

## 🎙️ Week 8 - 多模态交互

### 1. live-audio - 实时语音对话
`week8/live-audio/`

实时语音聊天演示，集成语音转文本、AI 对话和文本转语音功能。支持多个 AI 服务提供商（OpenAI、OpenRouter、ARK、Siliconflow），提供低延迟的对话体验。

**核心特性**：
- 实时语音输入与 VAD（Voice Activity Detection）
- 多提供商支持：ASR（OpenAI Whisper、SenseVoice）、LLM（GPT-4o、Gemini、Doubao）、TTS（Fish Audio）
- WebSocket 实时通信、低延迟音频流
- 实时延迟监控和日志记录
- 灵活的提供商选择和配置

**核心概念**：语音识别、实时对话、TTS、WebSocket、多提供商架构

### 2. browser-use - 浏览器自动化 Agent
`week8/browser-use/`

Browser-Use 是一个强大的浏览器自动化框架，让 LLM 能够控制浏览器完成复杂任务。支持表单填写、网页导航、数据提取等场景。提供 Python SDK 和云服务。

**核心特性**：
- LLM 驱动的浏览器自动化
- 支持多种 LLM（ChatBrowserUse、OpenAI、Google、本地模型）
- 自定义工具扩展、认证处理
- 沙箱部署支持、云服务集成
- 丰富的示例：表单填写、购物、个人助手等

**核心概念**：浏览器自动化、RPA、视觉理解、工具扩展

### 3. claude-quickstarts - Claude 快速入门
`week8/claude-quickstarts/`

Claude API 的快速入门示例和最佳实践，涵盖各种使用场景。

**核心概念**：Claude API、提示工程、最佳实践

## 🤝 Week 9 - 多 Agent 协作

### 1. use-computer-while-calling - 双 Agent 架构
`week9/use-computer-while-calling/`

实现电话呼叫 Agent 和计算机使用 Agent 的双 Agent 协作架构。两个 Agent 通过 WebSocket 直接通信，无需协调器。电话 Agent 处理语音交互，计算机 Agent 执行浏览器自动化，并行工作完成需要语音和网页操作的复杂任务。

**核心特性**：
- 直接 Agent 间通信（无协调器）
- 标准工具调用进行消息传递
- 并行操作：语音对话 + 浏览器自动化
- 特殊消息前缀标识消息来源
- 简单的 JSON 消息协议

**架构组件**：
- Phone Call Agent（Node.js）：语音 I/O、ASR/TTS、LLM 对话
- Computer Use Agent（Python）：浏览器自动化、browser-use、网页抓取
- WebSocket 通信：Agent 间直接消息传递

**核心概念**：多 Agent 协作、Agent 间通信、并行任务处理、语音+浏览器集成

## 📖 学习建议

### 核心理念：Agent = 模型 + 上下文 + 工具

本书的核心框架是 **Agent = 模型 + 上下文 + 工具**，这三个组件相互协作，共同实现 Agent 的智能行为：

- **模型（Model）**：Agent 的大脑，提供理解、推理和决策能力
- **上下文（Context）**：Agent 的操作系统，包含系统指令、对话历史、推理过程、工具交互记录等
- **工具（Tools）**：Agent 的双手，让 Agent 能够感知环境、执行操作、与外部世界交互

### 学习路径

#### Week 1：基础篇 - 理解 Agent 的本质

**核心目标**：建立对 Agent 系统的完整认知框架

- 理解强化学习中的 Agent 定义（状态、动作、奖励、策略、价值函数）
- 对比传统 RL（MDP）与现代 LLM+RL 范式的根本差异
- 通过实验验证：传统 RL vs LLM Agent 的样本效率差异
- 理解"模型即 Agent"的新范式（Kimi K2、GPT-5）
- 掌握 Agent = 模型 + 上下文 + 工具的核心框架

**关键洞察**：先验知识的重要性超越算法和环境，LLM 通过预训练获得的海量知识是现代 Agent 高样本效率的根本原因。

#### Week 2-3：上下文篇 - Agent 的操作系统

**核心目标**：深入理解上下文在 Agent 系统中的关键作用

**Week 2 - 上下文工程**：
- 系统提示技术：通过元信息增强 Agent 轨迹
- 上下文压缩策略：在保持能力的同时减少 token 使用
- KV Cache 友好的上下文设计：优化推理效率
- 用户记忆系统：跨会话的长期知识积累
- 提示工程消融研究：量化不同因素的影响

**Week 3 - 知识库与学习机制**：
- 稠密/稀疏嵌入与混合检索：构建高效的检索系统
- Agentic RAG：让 Agent 主导迭代式信息检索
- 上下文感知检索：解决传统分块的上下文丢失问题
- 结构化知识提取：从数据中发现隐性模式
- 从成功经验中学习：实现 Agent 的自我进化

**关键洞察**：上下文是 Agent 感知世界、记录历史、指导行为的基础。完整的上下文包括系统指令、对话历史、推理过程、工具交互记录、用户记忆和外部知识。

#### Week 4-5：工具篇 - Agent 的双手

**核心目标**：掌握工具设计与集成，让 Agent 能够执行实际操作

**Week 4 - 工具生态与系统集成**：
- 感知工具（MCP）：网络搜索、多模态理解、文件系统、公共数据源
- 执行工具（MCP）：代码解释器、文件操作、系统命令、安全机制
- 协作工具（MCP）：浏览器自动化、人机协同、多渠道通知
- 事件触发型 Agent：通过 HTTP API 接收多源事件
- 主动工具选择与异步 Agent 架构

**Week 5 - Coding Agent**：
- 生产级 Coding Agent 的完整实现
- 纯 Python 工具实现（无命令行依赖）
- 系统提示技术的实际应用
- 多 LLM 提供商支持

**关键洞察**：工具是 Agent 与外部世界交互的桥梁。工具设计应该通用化（如代码解释器优于计算器），给 LLM 更大的发挥空间。工具分为感知工具、执行工具和协作工具三大类。

#### Week 6-7：模型篇 - Agent 的大脑

**核心目标**：理解模型能力与后训练技术

**Week 6 - Agent 评估基准**：
- Terminal-Bench：终端环境任务评估
- SWE-bench：软件工程问题求解
- GAIA：通用 AI 助手能力测试
- OSWorld、Android World：操作系统级任务
- Tau2-Bench：工具增强推理评估

**Week 7 - 模型后训练（SFT 与 RL）**：
- AdaptThink：自适应推理深度，优化推理成本
- ReTool：工具增强数学推理，多轮对话与代码沙箱
- 各种后训练技术：持续预训练、提示蒸馏、反馈引导采样等
- SFT vs RL 对比研究
- verl 高效 RL 训练框架

**关键洞察**：LLM 是 Agent 的决策核心。"模型即 Agent"的新范式通过强化学习将工具调用能力内化为模型的原生能力。后训练、上下文学习和外部化学习是 Agent 学习的三种互补机制。

#### Week 8-9：应用篇 - 综合实践

**核心目标**：将模型、上下文、工具三者结合，构建实际应用

**Week 8 - 多模态交互**：
- 实时语音对话：ASR + LLM + TTS 的完整流程
- 浏览器自动化：LLM 驱动的 RPA
- 多提供商架构：灵活选择 AI 服务

**Week 9 - 多 Agent 协作**：
- 双 Agent 架构：电话呼叫 + 计算机使用
- Agent 间直接通信（无协调器）
- 并行任务处理：语音对话 + 浏览器自动化

**关键洞察**：实际应用需要综合运用模型、上下文、工具三个维度的技术。多 Agent 系统通过分工协作处理复杂任务，每个 Agent 专注于特定领域。

### 实践建议

1. **动手实践**：每个项目都设计为可独立运行，建议亲自运行并修改代码
2. **结合书籍**：配合本仓库 [`book/`](book/) 中的书稿相应章节阅读，理解理论与实践的结合
3. **实验对比**：多个项目包含消融研究和对比实验，通过对比加深理解
4. **渐进学习**：从简单项目开始，逐步深入复杂系统
5. **关注协议**：Week 4 的 MCP 服务器项目展示了标准化工具协议，这是构建可扩展 Agent 的关键

### 难度分级

- **入门级**（Week 1-2）：适合初学者，理解基本概念
- **进阶级**（Week 3-4）：需要一定编程基础，涉及系统集成
- **高级**（Week 5-6）：需要较强编程能力，涉及复杂系统设计
- **专家级**（Week 7）：需要深度学习和分布式训练经验
- **应用级**（Week 8-9）：综合运用前面所学，构建实际应用

## 🔑 API 密钥

建议大家申请几个平台的 API key，方便学习：
- **Kimi**: https://platform.moonshot.cn/
- **Siliconflow**: https://siliconflow.cn/ 上面有各种开源模型，包括 DeepSeek、Qwen 等
- **火山引擎**: https://www.volcengine.com/product/ark 上面有字节的闭源模型（豆包），国内访问延迟比较低
- **OpenRouter**: https://openrouter.ai/ 可以从国内直接访问海外的各种闭源和开源模型，包括 Gemini 2.5 Pro、Claude 4 Sonnet、OpenAI GPT-5 等（官方 API 需要海外 IP 和支付方式，OpenAI 还需要海外身份实名认证，注册比较麻烦）

模型选型可以参考： https://01.me/2025/07/llm-api-setup/

## 🤝 贡献

欢迎通过 Pull Request 贡献代码改进、bug 修复或新的示例项目。

## 📄 许可证

本项目代码仅供学习参考，具体许可证信息请查看各子项目。
