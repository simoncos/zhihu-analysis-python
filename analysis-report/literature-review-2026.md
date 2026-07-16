# 知乎社交网络分析：文献综述更新（2015–2026）

> 本文是对 2015 年课程项目《Social Network Analysis of Zhihu》的文献综述更新。原报告的 Related Work 仅引用了两篇知乎专栏文章；十年间，围绕知乎及同类社会化问答（CQA, Community Question Answering）社区的研究已发展出多条成熟脉络。本综述系统梳理 2015 年以来的相关文献，对照原项目的方法与数据，给出差距分析与后续研究建议。
>
> 撰写日期：2026 年 7 月。文献检索与核验方法见文末"方法与局限"一节。

## 目录

1. [原项目回顾](#1-原项目回顾)
2. [知乎本体研究（2015–2026）](#2-知乎本体研究2015--2026)
3. [CQA 研究的整体版图与平台偏向](#3-cqa-研究的整体版图与平台偏向)
4. [方法演进：从 2015 年工具箱到异质图神经网络](#4-方法演进从-2015-年工具箱到异质图神经网络)
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

### 2.1 专家发现与影响力排序

与原项目时间几乎重合，**ZhihuRank**（Liu, Ye, Li, Luo, Rao，中山大学；ICWL 2015，Springer LNCS 9412）[1] 已提出话题敏感的概率专家发现模型，将链接分析与用户-问题的 LDA 主题相似度联合建模，并在真实爬取的知乎数据集上报告优于各基线权威度排序算法。其核心论点——**同时考虑链接结构与主题相似度优于仅用链接分析**——直接指出了原项目所用 PageRank/HITS 纯链接路线的局限。换言之，早在 2015 年，"内容 + 结构"联合建模就已是知乎专家发现的起点，此后这一范式不断深化（见 4.1、3.3 节）。

### 2.2 知识付费与平台商业化

知乎 Live（2016 年 5 月上线）催生了一批以知乎为实证场景的商业化研究：

- Cong, Zhao & Zhang（**Marketing Science** 44(3), 2025, pp. 655–670）[2] 用双重差分（DiD）研究"知识可以定价"对创作者免费贡献行为的影响，发现知乎 Live 上线后**参与者的免费回答贡献被重新激活，而未参与者的贡献持续下滑**——付费内容并未挤出参与者的免费贡献。
- Zeng, Zhuang, Guo & Fan（**Electronic Markets** 32(4), 2022, pp. 2507–2523）[3] 基于 12,419 条知乎面板数据、以信号理论研究付费问答，发现**草根知识供给者的权威信号对用户付费行为无显著影响**——这对"2015 年式影响力指标（粉丝数、PageRank）能否转化为商业价值"给出了平台特异的否定性证据。
- Tu & Xin（**WHICEB 2020**，AIS eLibrary）[4] 结合 Gephi 社会网络分析与 LSTM 情感分析研究知乎 Live 的用户互动与评论，实证发现**核心话题周围的用户互动网络呈小世界结构**，并认为增强社交性是激励付费知识分享的有效平台策略。

这类研究的共同点：数据规模中等（数千至数万条记录）、方法为计量经济学或"网络 + 神经文本分析"的混合，与 2015 年的大规模图爬取路线明显不同。

### 2.3 用户行为：知识贡献与答题者留存

- 杨刚、闫璐、房懿卿、赵娜《答案质量反馈对社会化问答社区用户持续答题意愿的影响研究——以"知乎"平台为例》（**《图书情报工作》** 2020, 64(11): 46–56）[5] 以结构方程模型研究答案质量反馈对答题者持续答题意愿的影响，覆盖了英文文献较少触及的**答题者留存/流失**主题。该文也印证 CSSCI 图书情报学期刊持续产出知乎专属研究——中文文献中知乎研究的真实体量远大于英文可见部分（本次检索受限，见第 7 节）。
- Li, Du, Feng & Chen（**SAGE Open** 14(4), 2024）[6] 用 Python 爬虫采集 5,000 个知乎用户样本，以模糊集定性比较分析（fsQCA）研究知识贡献行为的组态路径。值得注意的是其研究动机部分指出：在线问答社区中**表现出知识输入行为的用户占比小且强度在下降**——为"知乎贡献活跃度衰退"的叙事提供了佐证，也为回溯性/衰退分析提供了研究缺口。

### 2.4 小结

知乎本体研究 2015 年后持续产出且方法多样（概率图模型、DiD、信号理论计量、SEM、fsQCA、SNA+LSTM），但**以关注网络结构为核心对象的大规模图分析类研究在英文文献中反而少见**——多数研究把知乎当作行为实证场景而非网络科学对象。这本身就是一个可辨识的缺口。

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

## 4. 方法演进：从 2015 年工具箱到异质图神经网络

原项目的工具箱（networkx + PageRank/HITS + 幂律拟合 + 支配集）代表了 2015 年的标准做法。此后方法演进大致三代：

### 4.1 第一代更替：网络表示学习（2014–2018）

Cai, Zheng & Chang 的综述（**IEEE TKDE** 30(9), 2018；arXiv:1709.07604）[12] 确立了图嵌入（graph embedding）作为图分析的标准框架：将节点/边/全图映射到低维向量空间，再把影响力排序、链接预测、社区发现统一为向量空间中的下游任务。DeepWalk/node2vec 一代随机游走方法即属此列。对本项目的含义：**用户聚类、关注链接预测、影响力排序都可以在同一嵌入空间中完成**，不再需要为每个任务单独设计图算法。

### 4.2 第二代更替：（异质）图神经网络（2017 至今）

- Bing, Yuan, Zhu, Meng, Ma & Qiao 的异质图神经网络（HGNN）综述（**Artificial Intelligence Review** 56: 8003–8042, 2023）[13] 指出：真实网络（如知乎的用户-问题-话题图）天然具有多类型节点与边，同质图方法（在单一关注图上跑 PageRank/HITS 的范式）会丢弃这种结构与语义信息；其实证比较显示 HGNN 的特征学习能力优于 DeepWalk/node2vec/metapath2vec 一代浅层嵌入。
- 需要的限定：Lv et al.（**KDD 2021**，HGB 基准）[14] 显示调优良好的简单 GAT/RGCN 常可匹敌复杂 HGNN 架构——HGNN 架构复杂化的边际收益存疑，但"深度图方法优于浅层嵌入、异质建模优于同质建模"的总体结论不受动摇。
- CQA 场景的直接应用：Wu, Fu, Xu, Yin, Zhou & Liu（**Information Sciences** 621: 708–728, 2023）[15] 提出 HCDBG，用异质图神经网络联合嵌入节点文本内容与网络拓扑，再以改进 k-means 做实体聚类完成**异质重叠社区发现**——其问题设定（用户/问题/答案多类型实体、重叠社区）正是原项目"用户聚类 + 异质网络"两项未完成计划的现代版本，且一步到位地融合了原项目分开处理的结构与文本。

### 4.3 第三代：LLM 时代（2023 至今）

LLM 对 CQA 研究的影响（LLM 辅助答案质量评估、话题抽取，以及 ChatGPT 对 Stack Overflow/知乎活跃度的冲击）在本次检索中未获得经过验证的文献支持（见第 7 节），此处不作有据陈述，仅指出这是撰写正式论文前必须补查的方向——尤其是"生成式 AI 冲击下知识社区衰退"已成为热点叙事，可能与本项目的历史快照价值直接相关。

### 4.4 对照总结

| 任务 | 2015 年工具箱（原项目） | 当前主流 |
|---|---|---|
| 影响力/专家排序 | PageRank、HITS（纯链接） | 内容+结构联合建模；多层图 + learning-to-rank（TUEF）|
| 用户聚类/社区发现 | 未完成（仅 SCC） | （异质）GNN 嵌入 + 聚类（HCDBG）|
| 异质网络 | 未完成 | HGNN / metapath 方法为标准框架 |
| 话题提取 | 支配集 + 频次统计 | 主题模型 → 神经文本模型 → LLM |
| 度分布刻画 | log-log 目测幂律 | 需用 Clauset-Shirky-Newman 式统计检验（目测拟合已不被接受）|

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

结论：**本项目 2015 年数据集的年龄不是负债而是独特资产**，理由有三：

1. ZhihuRec 不含用户-用户关注边，本数据集的显式关注图与之**互补而非被取代**；
2. 快照时点在知乎 Live 及整个知识付费浪潮之前，是研究"商业化前的知乎"的**基线快照**——Marketing Science 的 DiD 研究 [2] 正是围绕这一事件设计的，而公开数据中此类"事前"网络结构数据极为稀缺；
3. ZhihuRec 无原始文本、话题以 ID 形式给出，本数据集的话题标签原文可支撑话题层面的语义分析。

代价是必须正视的：2.6 万用户的 BFS 爬取带有强种子偏差（原报告已自承），任何正式发表都需要做偏差处理或将结论限定于种子邻域。

## 6. 差距分析与创新点建议

综合以上文献，按"新颖性 × 可行性"给出六个方向，均基于现有数据集（必要处注明需补充数据）：

### 6.1 异质网络专家发现：完成原计划，且填补"知乎缺口"（推荐，最高优先级）

原项目的用户-话题-问题数据天然构成异质信息网络。TUEF [10] 证明"按话题分层的多层图 + 排序"是当前 SOTA，但其评测全部在 Stack Exchange；Roy et al. [7] 确认绝大多数研究单平台且知乎缺席。**在 2015 知乎快照上构建用户-话题-问题异质图，比较 metapath 嵌入 / HGNN / 简单 GAT（含 HGB [14] 的"简单基线要调优"教训）与 PageRank/HITS 的专家发现效果**，既完成原计划，又是文献中可辨识的空白。赞同数/感谢数可作为专家性的弱标签。

### 6.2 同数据方法学基准：2015 工具箱 vs. 三代新方法

在完全相同的数据上系统比较 PageRank/HITS → node2vec 一代 → GNN 一代在影响力排序、链接预测、用户聚类三个任务上的表现。文献中方法比较通常跨数据集进行，同一真实 CQA 关注图上的受控三代对比少见，且工程量适中（数据已在手）。

### 6.3 影响力回溯研究：十年后的高影响力用户去哪了（需补爬少量数据）

2015 年 Net10k/Net50k 的 PageRank/HITS 头部用户名单是现成的"历史预测"。**重访这批用户的现状**（留存/注销/停更、粉丝增长、是否转型知识付费），检验 2015 年结构性影响力指标对十年后结果的预测力。结合 Electronic Markets [3] "权威信号不影响付费"与 SAGE Open [6] "贡献强度下降"的发现，可以讲一个完整的"早期结构位置 vs. 长期命运"的故事。仅需对约 2 千个头部账号做轻量现状采集，是典型的纵向研究设计，而文献中利用 2015 级早期中文平台快照做纵向对比的研究未见先例。

### 6.4 商业化前基线研究：作为"事前"网络快照的考古价值

围绕知乎 Live 的研究 [2][3][4] 都关心商业化对贡献行为的影响，但都缺少**事件前的网络结构数据**。本数据集恰好提供了 2015 年（事件前）的关注网络与用户-话题分布，可支撑"商业化前知乎的结构特征"刻画，或与 ZhihuRec（事件后多年）做跨时点结构对比（需处理两数据集字段不对齐问题：ZhihuRec 无关注边，只能在度分布、话题分布等聚合层面对比）。

### 6.5 话题图治理：Quora 话题合并研究的知乎版

以 Mathew et al. [11] 为模板，用 Question-topic 与 UserTopic 数据构建话题共现图，研究知乎话题体系中的冗余/竞争命名与层级结构（原爬虫的 topic 漏爬问题需先评估影响）。结合 LLM 做话题语义聚类是 2015 年不可能、现在低成本的增量。

### 6.6 严格化既有结论：幂律的统计检验

原报告的幂律结论基于 log-log 目测，当前网络科学标准要求 Clauset–Shalizi–Newman 式的最大似然拟合 + 对数正态等备择分布的似然比检验（`powerlaw` 库即可）。这是小工作量、高性价比的严格化，也是任何后续发表的必要前置。

**优先级建议**：6.1 + 6.6 组合是一篇完整论文的骨架（新方法 + 严格化的数据刻画）；6.3 是数据独特性最强、故事性最好的方向，若能补爬则潜在影响最大。

## 7. 方法与局限

本综述由深度研究工作流完成：问题分解为 5 个检索角度（知乎本体研究、跨平台 CQA、方法演进、公开数据集、平台演化与商业化），并行网络检索后抓取 20 个来源、提取 84 条候选声明，对其中 25 条核心声明做三票对抗式核验（24 条确认、1 条驳回）。主要局限：

1. **中文文献严重欠采样**：CNKI 不可直接访问，仅一篇 CSSCI 论文 [5] 获验证；中文知乎研究的真实体量远大于此，正式论文的相关工作一节必须补查 CNKI（尤其 2021 年后关于知乎商业化、内容质量与用户流失的研究）。
2. **LLM 时代文献未覆盖**：2023–2026 年 LLM×CQA 研究及 ChatGPT 对问答社区冲击的实证研究未获验证声明，需补查。
3. **部分引用信息依赖检索索引交叉印证**：多家出版商（Springer、SAGE、Wiley、lis.ac.cn）对自动抓取返回 403，个别页码/卷期未经落地页逐一核对；TUEF 的性能数字为作者自报。
4. 第 2.2 节两篇论文（[2][3]）、第 4 节方法综述（[12][14][15]）与 ZhihuRec 规格（[16]）的细节提取自原始来源但未走三票对抗核验流程，置信度略低于其余条目。

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
