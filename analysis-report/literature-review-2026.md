# 知乎社交网络分析：文献综述更新（2015–2026）

> 本文是对 2015 年课程项目《Social Network Analysis of Zhihu》的文献综述更新。原报告的 Related Work 仅引用了两篇知乎专栏文章；十年间，围绕知乎及同类社会化问答（CQA, Community Question Answering）社区的研究已发展出多条成熟脉络。本综述系统梳理 2015 年以来的相关文献，对照原项目的方法与数据，给出差距分析与后续研究建议。
>
> 撰写日期：2026 年 7 月，含一轮针对中文文献与 LLM 时代研究的定向补查。文献检索与核验方法见文末"方法与局限"一节。

## 目录

1. [原项目回顾](#1-原项目回顾)
2. [知乎本体研究（2015–2026）](#2-知乎本体研究2015--2026)
3. [CQA 研究的整体版图与平台偏向](#3-cqa-研究的整体版图与平台偏向)
4. [方法演进：从 2015 年工具箱到异质图神经网络与 LLM](#4-方法演进从-2015-年工具箱到异质图神经网络与-llm)
5. [公开数据集：ZhihuRec 与本项目数据集的对比](#5-公开数据集zhihurec-与本项目数据集的对比)
6. [差距分析与创新点建议](#6-差距分析与创新点建议)
7. [方法与局限](#7-方法与局限)
8. [参考文献](#8-参考文献)

---

## 1. 原项目回顾

原项目（2015 年底）以广度优先策略从种子用户爬取知乎数据，构建了包含约 2.6 万用户、460 万关注边的数据集（SQLite，含 User / Following / Question / UserQuestion / UserTopic 五张表），完成了以下分析：

- 用户特征（关注数、粉丝数、回答数、赞同数、感谢数）的幂律分布拟合；
- 赞同数与粉丝数的相关性；
- 关注网络的图密度、closeness / betweenness 分布；
- 基于 PageRank 与 HITS 的影响力排序（Net10k / Net50k 子网）；
- 强连通分量分析（发现高赞用户高度互连的"大陆—孤岛"结构）;
- 基于支配集（dominant set）的热门话题提取。

报告中列为"未来工作"但未完成的方向：**用户聚类、用户-话题-问题异质网络分析、基于回答文本的话题抽取**。这三项恰好对应过去十年 CQA 研究的主战场（见第 4 节）。

## 2. 知乎本体研究（2015–2026）

### 2.1 专家发现、意见领袖与网络结构

与原项目时间几乎重合，**ZhihuRank**（Liu, Ye, Li, Luo, Rao，中山大学；ICWL 2015，Springer LNCS 9412）[1] 已提出话题敏感的概率专家发现模型，将链接分析与用户-问题的 LDA 主题相似度联合建模，并在真实爬取的知乎数据集上报告优于各基线权威度排序算法。其核心论点——**同时考虑链接结构与主题相似度优于仅用链接分析**——直接指出了原项目所用 PageRank/HITS 纯链接路线的局限。

中文图书情报学界在 2018 年前后也用社会网络分析方法对知乎做了同类研究：

- 施艳萍、袁曦临、宋歌《社会化问答平台意见领袖的知识共享行为特征探析》（**《图书情报知识》** 2018(6): 103–112）[17] 以知乎"人工智能"话题下的活跃回答者为样本，用数理统计与社会网络分析从社交行为、信息行为、知识交互三个维度刻画意见领袖特征。
- 王忠义、张鹤铭、黄京、李春雅《基于社会网络分析的网络问答社区知识传播研究》（**《数据分析与知识发现》** 2018, 2(11): 80–94）[18] 基于约 42 万知乎用户的爬取数据（2017 年 2 月），结合社会网络分析与熵权法量化意见领袖的知识能力与传播影响力，并基于 Cowan 模型构建知识传播动力学仿真，发现该网络整体知识传播速率在下降。
- 《社会化问答社区用户行为统计特性及其动力学分析：以知乎网为例》（**《数据分析与知识发现》** 2018, 2(4): 48–58）[19] 用爬取的知乎公开数据发现：用户活动的事件间隔与等待时间服从幂指数分别为 0.68 与 1.51 的幂律分布（阵发性、非泊松）；**关注网络度分布及回答/赞同/评论数均服从指数截断幂律分布**——这与原项目的 log-log 目测幂律结论形成有趣对照：更严格的拟合显示知乎的分布带指数截断（见 6.6 节）。

### 2.2 知识付费与平台商业化

知乎 Live（2016 年 5 月上线）催生了一批以知乎为实证场景的商业化研究：

- Cong, Zhao & Zhang（**Marketing Science** 44(3), 2025, pp. 655–670）[2] 用双重差分（DiD）研究"知识可以定价"对创作者免费贡献行为的影响，发现知乎 Live 上线后**参与者的免费回答贡献被重新激活，而未参与者的贡献持续下滑**——付费内容并未挤出参与者的免费贡献。
- Zeng, Zhuang, Guo & Fan（**Electronic Markets** 32(4), 2022, pp. 2507–2523）[3] 基于 12,419 条知乎面板数据、以信号理论研究付费问答，发现**草根知识供给者的权威信号对用户付费行为无显著影响**——这对"2015 年式影响力指标（粉丝数、PageRank）能否转化为商业价值"给出了平台特异的否定性证据。
- Tu & Xin（**WHICEB 2020**，AIS eLibrary）[4] 结合 Gephi 社会网络分析与 LSTM 情感分析研究知乎 Live 的用户互动与评论，实证发现**核心话题周围的用户互动网络呈小世界结构**，并认为增强社交性是激励付费知识分享的有效平台策略。

### 2.3 用户行为：知识贡献、留存与流失迁移

**持续使用与贡献意愿**：

- 宋慧玲、帅传敏、李文静（**《信息资源管理学报》** 2019, 9(4): 68–81）[20] 以 488 份知乎用户问卷、PLS-SEM 分析持续使用意愿，发现自我效能感、满意度、感知开放性和感知有用性直接显著正向影响持续使用意愿，期望确认、感知交互性和社区归属感为间接影响。
- 杨刚、闫璐、房懿卿、赵娜（**《图书情报工作》** 2020, 64(11): 46–56）[5] 以结构方程模型研究答案质量反馈对答题者持续答题意愿的影响。
- Li, Du, Feng & Chen（**SAGE Open** 14(4), 2024）[6] 用 5,000 个知乎用户样本、fsQCA 组态分析研究知识贡献行为，其研究动机指出在线问答社区中**知识输入行为的用户占比小且强度在下降**。
- 涂艳、崔智斌、蒋楚钰《基于用户细分的社会化问答社区知识贡献激励机制研究》（**《北京理工大学学报（社会科学版）》** 2022, 24(3): 154–167）[21] 用系统动力学模型研究分层激励，指出社会化问答社区参与已演化为 **"90-9-1" 金字塔结构**（90% 长尾用户、9% 腰部、1% 头部），并论证平台对高赞头部内容的频繁推荐产生**信息茧房**、尾部用户因缺乏声誉回报而贡献意愿下降——把推荐机制设计与"内容质量下滑"感知直接关联。

**流失与迁移**（2021 年后中文研究的活跃主题）：

- 《数字图书馆论坛》2024 年第 7 期刊载的社会化问答社区用户**非持续使用行为**研究 [22] 以知乎为代表案例，用半结构化访谈与扎根理论、基于刺激-有机体-反应（SOR）模型构建影响因素模型，发现环境刺激、社交刺激、情境刺激导致认知压力与情感倦怠，用户在多重负累下选择逃离平台。
- Zhou & Mi（**Universal Access in the Information Society**, 2023 online / 2024）[23] 用推拉锚定（push-pull-mooring）框架研究社会化问答平台间的用户转移：推力（对现平台的不满与倦怠）与拉力（替代平台的内容质量与用户体验）均正向影响转移意愿并导致实际转移，转移成本起负向调节——**将"感知内容质量差异"与用户迁移直接建立了因果链**。

**平台产品决策的因果证据**：Cao, Zhu, Li & Qiu《Consequences of Information Feed Integration on User Engagement and Contribution: A Natural Experiment in an Online Knowledge-Sharing Community》（**Information Systems Research**）[24] 利用知乎 2019 年 6 月将"想法"（社交短内容）并入回答信息流的自然实验，发现信息流整合**因果性地降低了两类内容的参与度与贡献量**，机制包括专业形象稀释（在意"专家"形象的优秀回答者减少发布非正式内容）与认知负荷（严肃知识与休闲内容并置增加心智切换）——为"知乎变味"叙事提供了罕见的因果证据（注：本条经浙江大学管理学院对该论文的中文报道间接核验，未直接核对期刊原文）。

### 2.4 小结

知乎本体研究 2015 年后持续产出且方法多样（概率图模型、DiD、自然实验、信号理论计量、SEM、fsQCA、SNA+LSTM、系统动力学、扎根理论）。中文图书情报学期刊（《图书情报工作》《图书情报知识》《数据分析与知识发现》《信息资源管理学报》《数字图书馆论坛》等）构成一条与英文文献平行且更贴近平台演化议题的研究脉络。但**以关注网络结构为核心对象的大规模图分析类研究在 2018 年后明显减少**——研究重心转向行为计量与用户心理，网络科学视角的知乎研究反而出现空窗。

## 3. CQA 研究的整体版图与平台偏向

### 3.1 系统综述刻画的主题版图

Roy, Saumya, Singh, Banerjee & Gutub（**CAAI Transactions on Intelligence Technology** 8(1): 95–117, 2023）[7] 系统综述了 133 篇将机器学习/深度学习应用于 CQA 的文献，按**问题、答案、用户**三个分析单元组织。主导主题为：问题质量、答案质量、**专家识别**（后者正是 2015 年 PageRank/HITS 影响力排序的现代继任者）。两个对本项目重要的结论：

1. **平台偏向**：被研究最多的平台是 Yahoo! Answers、Stack Exchange 与 Stack Overflow，**而非知乎**；
2. **单平台局限**：绝大多数研究只覆盖单一平台，跨平台比较稀缺。

这构成明确的"知乎缺口"与跨平台比较缺口。（注意：该综述检索截止约 2021/2022 年，其"传统 ML 研究数量仍多于 DL"的计数在 LLM 时代后很可能已逆转。）

### 3.2 Stack Overflow：平台研究版图的模板

Meldrum, Licorish & Savarimuthu（**EASE 2020**；arXiv:2010.12282）[8] 对 265 篇 Stack Overflow 论文（2009–2017）做了系统映射，研究聚为四个体量相近的主题：内容（问题/答案/标签，23.0%）、编程/开发（21.9%）、社区动态与过程（20.8%）、社区成员（20.0%）。社区结构/用户行为类研究合计约 40.8%——说明与原项目同类的问题在 CQA 研究中仍占重要份额。**目前尚无知乎版的等价系统映射研究**，这也是一个可做的贡献。

### 3.3 专家发现：从链接分析到排序学习

- Yuan, Zhang, Tang, Hall & Bautista Cabotà（**Artificial Intelligence Review** 53, 2020；arXiv:1804.07958）[9] 的专家发现综述将主流方案归为矩阵分解（MF）、梯度提升树（GBT）、深度学习（DL）、排序（Ranking）四类，经典 PageRank/HITS 图排序已不再是领先类别；其论证 CQA 的新特征（海量、稀疏、众包）违反了传统方法的基本假设。在众包基准（ByteCup/头条问答数据）上，其实证发现 **MF 类模型优于包括深度学习在内的其余三类**——这是 2018–2019 年、前 BERT 时代的历史性结论，不代表当前 SOTA，但说明"深度模型未必自动占优"。
- 当前前沿的代表是 **TUEF**（Amendola, Passarella & Perego；ECIR 2024，期刊版 ACM TOIS，arXiv:2407.04018）[10]：按话题构建用户交互**多层图**融合内容与社交关系，用 learning-to-rank（LambdaMART/LightGBM）而非纯图中心性排序候选专家，在六个 Stack Exchange 社区上报告最低 +42.42% P@1、+29.81% MRR 的提升（作者自报）。论文同时指出**有效融合 CQA 平台上的多样信息源（内容 + 社交）至今仍具挑战**——这一开放问题与原项目未完成的用户-话题-问题异质网络分析直接相关。

### 3.4 话题体系治理（Quora 的镜像问题）

Mathew, Maity, Goyal & Mukherjee（**ACM CoDS-COMAD 2020**；arXiv:1909.04367）[11] 研究 Quora 用户自定义话题体系（folksonomy）中的"竞争性命名"合并预测：在约 540 万问题语料上，用异常检测 + 监督分类预测应当合并的话题对（F-score 0.711），且预测比社区人工裁决平均快数年。知乎的话题体系同样是社区维护的图结构，原项目 UserTopic/Question-topic 数据可支撑类似的话题图治理研究，目前未见知乎版等价工作。

## 4. 方法演进：从 2015 年工具箱到异质图神经网络与 LLM

原项目的工具箱（networkx + PageRank/HITS + 幂律拟合 + 支配集）代表了 2015 年的标准做法。此后方法演进大致三代：

### 4.1 第一代更替：网络表示学习（2014–2018）

Cai, Zheng & Chang 的综述（**IEEE TKDE** 30(9), 2018；arXiv:1709.07604）[12] 确立了图嵌入（graph embedding）作为图分析的标准框架：将节点/边/全图映射到低维向量空间，再把影响力排序、链接预测、社区发现统一为向量空间中的下游任务。DeepWalk/node2vec 一代随机游走方法即属此列。对本项目的含义：**用户聚类、关注链接预测、影响力排序都可以在同一嵌入空间中完成**，不再需要为每个任务单独设计图算法。

### 4.2 第二代更替：（异质）图神经网络（2017 至今）

- Bing, Yuan, Zhu, Meng, Ma & Qiao 的异质图神经网络（HGNN）综述（**Artificial Intelligence Review** 56: 8003–8042, 2023）[13] 指出：真实网络（如知乎的用户-问题-话题图）天然具有多类型节点与边，同质图方法（在单一关注图上跑 PageRank/HITS 的范式）会丢弃这种结构与语义信息；其实证比较显示 HGNN 的特征学习能力优于 DeepWalk/node2vec/metapath2vec 一代浅层嵌入。
- 需要的限定：Lv et al.（**KDD 2021**，HGB 基准）[14] 显示调优良好的简单 GAT/RGCN 常可匹敌复杂 HGNN 架构——HGNN 架构复杂化的边际收益存疑，但"深度图方法优于浅层嵌入、异质建模优于同质建模"的总体结论不受动摇。
- CQA 场景的直接应用：Wu, Fu, Xu, Yin, Zhou & Liu（**Information Sciences** 621: 708–728, 2023）[15] 提出 HCDBG，用异质图神经网络联合嵌入节点文本内容与网络拓扑，再以改进 k-means 做实体聚类完成**异质重叠社区发现**——其问题设定（用户/问题/答案多类型实体、重叠社区）正是原项目"用户聚类 + 异质网络"两项未完成计划的现代版本，且一步到位地融合了原项目分开处理的结构与文本。

### 4.3 第三代：LLM 时代（2023 至今）

定向补查确认，LLM 从两个方向重塑了 CQA 研究——**LLM 作为研究对象**（对社区的冲击）与 **LLM 作为研究工具**（替代旧的文本/图方法）：

**LLM 对问答社区的冲击（实证）**：

- del Rio-Chanona, Laurentsyeva & Wachs《Large language models reduce public knowledge sharing on online Q&A platforms》（**PNAS Nexus** 3(9): pgae400, 2024）[25] 是该方向的标志性研究：ChatGPT 发布（2022 年 11 月）后 6 个月内，Stack Overflow 发帖活动相对反事实平台下降 **25%**（作者视为下界）；下降在 Python/JavaScript 等 LLM 最擅长的主题上更大；发帖质量（同行投票）无显著变化、各经验层级用户的贡献都在下降——即 LLM 替代的不只是低质/新手内容。**方法上对本项目尤其重要**：其 DiD 设计用俄语 Stack Overflow 与中文平台 SegmentFault（ChatGPT 受限地区）及数学论坛作为对照组——中文问答平台在该文献中是"对照组"而非研究对象，**国产 LLM 对中文问答社区（知乎）的冲击至今没有等价的实证研究**。
- Burtch, Lee & Chen《The consequences of generative AI for online knowledge communities》（**Scientific Reports** 14: 10413, 2024）[26] 用 2021 年 10 月–2023 年 3 月数据对比 Stack Overflow 与 Reddit 开发者社区：Stack Overflow 的访问量与提问量显著下降且集中于 ChatGPT 擅长的主题，而 **Reddit 社区无下降**——作者归因于"社交纽带"（social fabric）对 LLM 冲击的缓冲作用；且下降集中于**新用户/社交嵌入度低的用户**。这两点都指向社区的网络结构是调节 AI 冲击的关键变量——正是网络分析可以贡献的地方。
- Helic & Santos（**Journal of Systems and Software**, 2026, DOI 10.1016/j.jss.2026.112988；arXiv:2509.05879）[27] 的后续研究发现 ChatGPT 加速了 Stack Overflow 本已存在的贡献衰退，但同时**因果性地提高了**问题长度、答案长度、代码示例长度与问题难度——解释为 LLM 与人类社区之间的"任务分拣"：简单问题流向 ChatGPT，困难问题留给人类。社区不是单纯死亡，而是在转型。
- 治理侧：Wang & Zheng（SSRN 工作论文，DOI 10.2139/ssrn.4750326）[28] 研究 ChatGPT 发布后 4 个月内 18 个 Stack Exchange 社区禁止 AI 生成答案的 DiD 效应：禁令使提问需求上升约 13%，但回答效率下降约 3.3%（注：该研究为工作论文且部分细节未能直接核验，引用需谨慎）。

**AI 生成内容已进入知乎**：Cui, Zhang, Wang & Cai 的 **SAID** 基准（arXiv:2310.08240, 2023）[29] 用**真实发布在知乎和 Quora 上的 AI 生成回答**（而非实验室模拟文本）构建检测基准——直接证明 2023 年知乎上已存在 AI 生成回答的实际扩散；熟悉 LLM 的人类标注者在知乎子集上的辨别准确率约 96.5%，且提出基于用户级多回答信息的检测范式优于单文本检测。与之呼应，Kabir et al.（**CHI 2024**, DOI 10.1145/3613904.3642596）[30] 分析 ChatGPT 对 517 个 Stack Overflow 问题的回答：52% 含错误信息、77% 冗长，但用户研究中参与者仍有 35% 的情形偏好 ChatGPT 答案、39% 的情形没有察觉其中的错误信息。

**LLM 作为研究工具**：

- **TopicGPT**（Pham, Hoyle, Sun, Resnik & Iyyer；NAACL 2024）[31] 用提示式 LLM 框架做主题发现，与人类标注主题的对齐度（harmonic purity 0.74）显著优于 LDA（0.64）与 BERTopic（0.58），并产出自然语言标签的可解释主题——原项目"基于文本的话题抽取"计划在 2015 年只能用 LDA，如今 LLM 路线已系统性占优。
- Ren, Tang, Yin, Chawla & Huang（**KDD 2024**, arXiv:2405.08011）[32] 的 LLM×图学习综述给出四类集成范式（GNNs as Prefix / LLMs as Prefix / LLMs-Graphs Integration / LLMs-Only），为把 LLM 应用于知乎这类用户交互图提供了方法分类地图。

### 4.4 对照总结

| 任务 | 2015 年工具箱（原项目） | 当前主流 |
|---|---|---|
| 影响力/专家排序 | PageRank、HITS（纯链接） | 内容+结构联合建模；多层图 + learning-to-rank（TUEF）|
| 用户聚类/社区发现 | 未完成（仅 SCC） | （异质）GNN 嵌入 + 聚类（HCDBG）|
| 异质网络 | 未完成 | HGNN / metapath 方法为标准框架；LLM×图（KDD 2024 综述）|
| 话题提取 | 支配集 + 频次统计 | LDA → 神经主题模型 → LLM（TopicGPT，NAACL 2024）|
| 度分布刻画 | log-log 目测幂律 | 需统计检验；中文文献已报告知乎为指数截断幂律 [19] |
| 社区冲击测量 | —（不存在此问题） | 围绕 ChatGPT 发布的 DiD / 自然实验设计 [25][26][27] |

## 5. 公开数据集：ZhihuRec 与本项目数据集的对比

**ZhihuRec**（清华大学 THUIR 与知乎联合发布，2021；Hao et al., arXiv:2106.06467）[16] 是目前规模最大的公开知乎数据集：约 1 亿条用户-回答交互（10 天窗口），涉及 79.8 万用户、16.5 万问题、55.4 万回答、24 万作者、7 万话题，含丰富的用户侧聚合特征（注册时间、性别、登录频率、粉丝数、获赞数、设备、地域、关注话题等），以 100M/20M/1M 三种规格、约 3.6GB CSV 发布，仅限研究使用。

**关键对比**（对本项目数据集的定位至关重要）：

| 维度 | ZhihuRec (2021) | 本项目数据集 (2015) |
|---|---|---|
| 规模 | ~1 亿交互、79.8 万用户 | 2.6 万用户、460 万关注边 |
| 时间窗 | 10 天（快照极浅） | 单时点快照，但处于平台早期 |
| **用户-用户关注图** | **不含关注边列表**（仅有粉丝数等聚合特征） | **显式 460 万边关注图**（核心资产） |
| 文本 | 脱敏，无原始文本（仅 64 维 word2vec 向量） | 有话题标签原文；无回答正文 |
| 定位 | 推荐/搜索研究 | 社会网络结构分析 |
| 时点 | 商业化成熟期 | **知乎 Live（2016.5）上线之前** |

结论：**本项目 2015 年数据集的年龄不是负债而是独特资产**，理由有四：

1. ZhihuRec 不含用户-用户关注边，本数据集的显式关注图与之**互补而非被取代**；
2. 快照时点在知乎 Live 及整个知识付费浪潮之前，是研究"商业化前的知乎"的**基线快照**——Marketing Science 的 DiD 研究 [2] 正是围绕这一事件设计的，而公开数据中此类"事前"网络结构数据极为稀缺；
3. ZhihuRec 无原始文本、话题以 ID 形式给出，本数据集的话题标签原文可支撑话题层面的语义分析；
4. （补查后新增）快照同样早于生成式 AI 时代——SAID 基准 [29] 证明 2023 年知乎上已有 AI 生成回答的实际扩散，del Rio-Chanona et al. [25] 论证 LLM 正在侵蚀人类生成的公共知识内容。2015 年的快照是**保证纯人类生成**的语料与网络，作为"前 AI 时代基线"的价值随时间上升而非下降。

代价是必须正视的：2.6 万用户的 BFS 爬取带有强种子偏差（原报告已自承），任何正式发表都需要做偏差处理或将结论限定于种子邻域。

## 6. 差距分析与创新点建议

综合以上文献，按"新颖性 × 可行性"给出六个方向，均基于现有数据集（必要处注明需补充数据）：

### 6.1 异质网络专家发现：完成原计划，且填补"知乎缺口"（推荐，最高优先级）

原项目的用户-话题-问题数据天然构成异质信息网络。TUEF [10] 证明"按话题分层的多层图 + 排序"是当前 SOTA，但其评测全部在 Stack Exchange；Roy et al. [7] 确认绝大多数研究单平台且知乎缺席。**在 2015 知乎快照上构建用户-话题-问题异质图，比较 metapath 嵌入 / HGNN / 简单 GAT（含 HGB [14] 的"简单基线要调优"教训）与 PageRank/HITS 的专家发现效果**，既完成原计划，又是文献中可辨识的空白。赞同数/感谢数可作为专家性的弱标签。

### 6.2 同数据方法学基准：2015 工具箱 vs. 三代新方法

在完全相同的数据上系统比较 PageRank/HITS → node2vec 一代 → GNN 一代在影响力排序、链接预测、用户聚类三个任务上的表现。文献中方法比较通常跨数据集进行，同一真实 CQA 关注图上的受控三代对比少见，且工程量适中（数据已在手）。

### 6.3 影响力回溯研究：十年后的高影响力用户去哪了（需补爬少量数据）

2015 年 Net10k/Net50k 的 PageRank/HITS 头部用户名单是现成的"历史预测"。**重访这批用户的现状**（留存/注销/停更、粉丝增长、是否转型知识付费），检验 2015 年结构性影响力指标对十年后结果的预测力。补查结果显著强化了这一方向的理论框架：Burtch et al. [26] 发现 AI 冲击下**社交嵌入度低的用户先流失**、社交纽带是社区韧性的缓冲——2015 年关注图中每个用户的结构嵌入度（度、核数、社区归属）是现成的解释变量；结合 Zhou & Mi [23] 的推拉迁移框架、Electronic Markets [3] "权威信号不影响付费"与涂艳等 [21] 的 90-9-1 分层，可以讲一个完整的"早期结构位置 → 商业化与 AI 双重冲击下的长期命运"的故事。仅需对约 2 千个头部账号做轻量现状采集；文献中利用 2015 级早期中文平台快照做纵向研究的工作未见先例。

### 6.4 双重基线研究：商业化前 + 生成式 AI 前的"事前"网络快照

围绕知乎 Live 的研究 [2][3][4] 与围绕信息流整合的自然实验 [24] 都关心平台决策对贡献行为的影响，但都缺少**事件前的网络结构数据**；LLM 冲击研究 [25][26][27] 则需要"前 AI 时代"的活动基线，且中文平台在这条文献线里至今只当过对照组、没当过研究对象。本数据集恰好同时处于两个"事前"：知乎 Live 之前、生成式 AI 之前。可支撑的研究包括：商业化前知乎的结构特征刻画、与 ZhihuRec（事件后多年）的跨时点聚合对比（度分布、话题分布层面），以及为"国产 LLM 对知乎的冲击"这一空白研究提供历史基线。王忠义等 [18]（2017 年 42 万用户）与《数据分析与知识发现》2018 活动动力学研究 [19] 提供了可衔接的 2017–2018 年中间时点参照。

### 6.5 话题图治理：Quora 话题合并研究的知乎版

以 Mathew et al. [11] 为模板，用 Question-topic 与 UserTopic 数据构建话题共现图，研究知乎话题体系中的冗余/竞争命名与层级结构（原爬虫的 topic 漏爬问题需先评估影响）。补查后这一方向的工具升级明确：TopicGPT [31] 证明 LLM 主题发现已系统性优于 LDA/BERTopic，对 2015 年话题标签做 LLM 语义聚类与层级重构是低成本、高新颖性的增量。

### 6.6 严格化既有结论：幂律的统计检验

原报告的幂律结论基于 log-log 目测，当前网络科学标准要求 Clauset–Shalizi–Newman 式的最大似然拟合 + 对数正态等备择分布的似然比检验（`powerlaw` 库即可）。补查发现这不只是形式要求：《数据分析与知识发现》2018 年研究 [19] 报告知乎的度分布与行为计数服从**指数截断幂律**而非纯幂律——用严格检验重新拟合 2015 年数据，验证或反驳"知乎早期即存在指数截断"本身就是一个有对话对象的实证问题。

**优先级建议**：6.1 + 6.6 组合是一篇完整论文的骨架（新方法 + 严格化的数据刻画）；6.3 是数据独特性最强、故事性最好的方向，若能补爬则潜在影响最大；6.4 的"双重基线"论证是向审稿人解释数据集价值的核心话术。

## 7. 方法与局限

本综述由深度研究工作流完成，共两轮：

- **第一轮**（主综述）：问题分解为 5 个检索角度，抓取 20 个来源、提取 84 条候选声明，对 25 条核心声明做三票对抗式核验（24 条确认、1 条驳回）。
- **第二轮**（定向补查）：针对第一轮的两个已确认缺口（中文 CNKI 文献、LLM 时代研究）再次分解检索。因运行中多次触及会话用量限制，核验完成 8 条（全部确认），其余约 17 条候选声明的书目信息经从原始来源页的抓取记录交叉整理后纳入，未走完整三票流程。

置信度分级如下：

1. **三票对抗核验确认**：[1][4][5][6][7][8][9][10][13]（部分）以及补查中的 [19]（两条核心结论）、[20][22][23]（推拉与流失机制核心结论）；
2. **原始来源页直接提取、未走三票**：[2][3][12][14][15][16][17][18][21][25][26][27][29][30][31][32]——其中 [25][26] 的书目信息（作者、卷期、DOI）在抓取记录中有原文引文佐证，可信度高；
3. **间接来源或工作论文，引用需谨慎**：[24]（经浙江大学管理学院中文报道核验，未直接核对 ISR 原文）、[28]（SSRN 工作论文，细节未能直接核验）；[19] 的作者名单未能确认（期刊页对抓取返回 403），引用时以题名+期刊+DOI 为准。

仍存在的局限：

1. **CNKI 全貌仍未覆盖**：补查经由百度学术、万方镜像、期刊官网等间接渠道确认了《图书情报知识》《数据分析与知识发现》《信息资源管理学报》《数字图书馆论坛》《北京理工大学学报（社科版）》等期刊的知乎研究脉络，但这仍是可间接检索到的子集；正式论文投稿前建议用 CNKI 做一次系统检索（特别是 2021 年后知乎商业化与内容质量主题）。
2. **知乎×LLM 冲击的实证研究未发现**——多方检索均未找到以知乎为对象的 ChatGPT/国产大模型冲击研究，这既是局限也是第 6.4 节论证的核心机会。
3. 多家出版商（Springer、SAGE、Wiley、Elsevier、magtech 系中文期刊平台）对自动抓取返回 403，部分验证依赖检索索引摘要与机构库镜像交叉印证。

## 8. 参考文献

[1] Liu, Ye, Li, Luo, Rao. *ZhihuRank: A Topic-Sensitive Expert Finding Algorithm in Community Question Answering Websites.* ICWL 2015, Springer LNCS 9412. DOI: 10.1007/978-3-319-25515-6_15. https://link.springer.com/chapter/10.1007/978-3-319-25515-6_15

[2] Cong, Zhao, Zhang. *Understanding Users' Content Contribution Behavior When Knowledge Can Be Priced.* Marketing Science 44(3): 655–670, 2025. DOI: 10.1287/mksc.2022.0205. https://pubsonline.informs.org/doi/10.1287/mksc.2022.0205

[3] Zeng, Zhuang, Guo, Fan. (paid Q&A on Zhihu, signaling theory). Electronic Markets 32(4): 2507–2523, 2022. DOI: 10.1007/s12525-022-00588-2. https://link.springer.com/article/10.1007/s12525-022-00588-2

[4] Tu, Xin. *Social Network Analysis for Online Knowledge Exchange Platform: Evidence from Zhihu.* WHICEB 2020, AIS eLibrary. https://aisel.aisnet.org/whiceb2020/3/

[5] 杨刚, 闫璐, 房懿卿, 赵娜. 答案质量反馈对社会化问答社区用户持续答题意愿的影响研究——以"知乎"平台为例. 图书情报工作, 2020, 64(11): 46–56. DOI: 10.13266/j.issn.0252-3116.2020.11.006. https://www.lis.ac.cn/EN/10.13266/j.issn.0252-3116.2020.11.006

[6] Li, Du, Feng, Chen. *Research on Factors Influencing Knowledge Contribution in Online Q&A Communities: Based on an Empirical Study of QCA on Zhihu.* SAGE Open 14(4), 2024. DOI: 10.1177/21582440241305158

[7] Roy, Saumya, Singh, Banerjee, Gutub. *Analysis of community question-answering issues via machine learning and deep learning: State-of-the-art review.* CAAI Transactions on Intelligence Technology 8(1): 95–117, 2023. DOI: 10.1049/cit2.12081

[8] Meldrum, Licorish, Savarimuthu. *Exploring Research Interest in Stack Overflow — A Systematic Mapping Study and Quality Evaluation.* EASE 2020. arXiv:2010.12282

[9] Yuan, Zhang, Tang, Hall, Bautista Cabotà. *Expert finding in community question answering: a review.* Artificial Intelligence Review 53, 2020. DOI: 10.1007/s10462-018-09680-6. arXiv:1804.07958

[10] Amendola, Passarella, Perego. *Topic-oriented User-Interaction model for Expert Finding (TUEF).* ECIR 2024；期刊版 ACM Transactions on Information Systems, DOI: 10.1145/3793531. arXiv:2407.04018. 代码：https://github.com/maddalena-amendola/TUEF

[11] Mathew, Maity, Goyal, Mukherjee. (Quora topic-merge prediction). ACM CoDS-COMAD 2020. arXiv:1909.04367

[12] Cai, Zheng, Chang. *A Comprehensive Survey of Graph Embedding: Problems, Techniques, and Applications.* IEEE TKDE 30(9), 2018. arXiv:1709.07604

[13] Bing, Yuan, Zhu, Meng, Ma, Qiao. *Heterogeneous graph neural networks analysis: a survey of techniques, evaluations and applications.* Artificial Intelligence Review 56: 8003–8042, 2023. DOI: 10.1007/s10462-022-10375-2

[14] Lv et al. *Are we really making much progress? Revisiting, benchmarking and refining heterogeneous graph neural networks.* KDD 2021. https://dl.acm.org/doi/10.1145/3447548.3467350

[15] Wu, Fu, Xu, Yin, Zhou, Liu. *HCDBG: heterogeneous community detection in CQA based on graph neural networks.* Information Sciences 621: 708–728, 2023. https://www.sciencedirect.com/science/article/abs/pii/S0020025522012506

[16] Hao et al. *A Large-Scale Rich Context Query and Recommendation Dataset in Online Knowledge-Sharing.* arXiv:2106.06467, 2021. 数据：https://github.com/THUIR/ZhihuRec-Dataset

[17] 施艳萍, 袁曦临, 宋歌. 社会化问答平台意见领袖的知识共享行为特征探析. 图书情报知识, 2018(6): 103–112. DOI: 10.13366/j.dik.2018.06.103. https://dik.whu.edu.cn/jwk3/tsqbzs/CN/abstract/abstract4069.shtml

[18] 王忠义, 张鹤铭, 黄京, 李春雅. 基于社会网络分析的网络问答社区知识传播研究. 数据分析与知识发现, 2018, 2(11): 80–94. DOI: 10.11925/infotech.2096-3467.2018.0293

[19] （作者待核实）. 社会化问答社区用户行为统计特性及其动力学分析：以知乎网为例. 数据分析与知识发现, 2018, 2(4): 48–58. DOI: 10.11925/infotech.2096-3467.2017.0904

[20] 宋慧玲, 帅传敏, 李文静. （知识问答社区用户持续使用意愿实证研究）. 信息资源管理学报, 2019, 9(4): 68–81. DOI: 10.13365/j.jirm.2019.04.068

[21] 涂艳, 崔智斌, 蒋楚钰. 基于用户细分的社会化问答社区知识贡献激励机制研究. 北京理工大学学报（社会科学版）, 2022, 24(3): 154–167. DOI: 10.15918/j.jbitss1009-3370.2022.2741

[22] （社会化问答社区用户非持续使用行为的影响因素研究）. 数字图书馆论坛, 2024(7). https://journals.istic.ac.cn/dlf/ch/reader/view_abstract.aspx?file_no=202407004

[23] Zhou, T., Mi, Q. *Examining user switching between social Q&A platforms: a push–pull–mooring perspective.* Universal Access in the Information Society, 2024 (online 2023). DOI: 10.1007/s10209-023-01001-1

[24] Cao, Zhu, Li, Qiu. *Consequences of Information Feed Integration on User Engagement and Contribution: A Natural Experiment in an Online Knowledge-Sharing Community.* Information Systems Research（经浙江大学管理学院报道间接核验）.

[25] del Rio-Chanona, Laurentsyeva, Wachs. *Large language models reduce public knowledge sharing on online Q&A platforms.* PNAS Nexus 3(9): pgae400, 2024. DOI: 10.1093/pnasnexus/pgae400（预印本 arXiv:2307.07367）

[26] Burtch, Lee, Chen. *The consequences of generative AI for online knowledge communities.* Scientific Reports 14: 10413, 2024. DOI: 10.1038/s41598-024-61221-0

[27] Helic, Santos. (ChatGPT's causal effect on Stack Overflow content characteristics). Journal of Systems and Software, 2026. DOI: 10.1016/j.jss.2026.112988. arXiv:2509.05879

[28] Wang, Zheng. *Can Banning AI-generated Content Save User-generated Q&A Platforms?* SSRN 工作论文. DOI: 10.2139/ssrn.4750326

[29] Cui, Zhang, Wang, Cai. *Who Said That? Benchmarking Social Media AI Detection (SAID).* arXiv:2310.08240, 2023

[30] Kabir et al. (ChatGPT answers to Stack Overflow questions: correctness and user perception). CHI 2024. DOI: 10.1145/3613904.3642596

[31] Pham, Hoyle, Sun, Resnik, Iyyer. *TopicGPT: A Prompt-based Topic Modeling Framework.* NAACL 2024（arXiv 预印本 2023-11）

[32] Ren, Tang, Yin, Chawla, Huang. *A Survey of Large Language Models for Graphs.* KDD 2024. DOI: 10.1145/3637528.3671460. arXiv:2405.08011
