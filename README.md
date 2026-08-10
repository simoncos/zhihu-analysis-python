# 知乎社交网络分析（历史 `master` 快照）

> 本分支保存 2015–2017 年课程项目代码与报告，不是当前知乎数据、可复现研究结论或
> 可公开发布的数据集。旧 crawler、旧分析脚本和两份报告均作为历史材料保留。

## 研究与发布边界

- 原始数据库包含用户 URL、显示名、问题 ID、关注关系和话题活动等可识别信息。
  本分支不再提供原始数据下载入口；在隐私、伦理、平台权利和数据许可得到明确的
  人工决定前，不应重新传播原始或逐行派生数据。
- [2015 项目报告](analysis-report/Social%20Network%20Analysis%20of%20Zhihu.pdf)
  与[演示文稿](analysis-report/Social%20Network%20Analysis%20of%20Zhihu_slides.pdf)
  是归档产物。报告中的“显著幂律”、相关性、热门话题和精英子图结论来自当年的
  可视化/探索性方法，不能视为当前代码已验证的统计结论。
- 仓库内没有 `zhihu.db`，也没有可证明报告数字的精确提交、依赖锁、运行清单或
  本轮真实数据重跑。因此真实数据复现与发布仍是开放门槛。
- 其他分支的实现、合成测试或历史运行结果不构成本 `master` 快照的测试证据。
- 仓库没有数据许可证。不得从代码可见或字段曾公开推导出数据再发布授权。

## 代码与数据流

历史流程为：`crawler/user.py` 写用户、关注与回答问题的制表符文件，
`crawler/topic.py` 写问题—话题文件，`zhihu_database.py` 在本地构建 SQLite，
`zhihu_analysis.py` 再读取 `User`、`Following` 和 `UserTopic`。

当前边界如下：

- `crawler/`：Python 2 时代的站点解析与登录代码，依赖失效页面结构并关闭 TLS
  验证；不支持、不测试，也不应拿来重新抓取知乎。
- `zhihu_analysis.py`：Python 2 / 旧 NetworkX 探索脚本，仅作归档。它没有现代
  Python 或统计有效性保证。
- `zhihu_database.py`：本分支唯一维护的 Python 3 工具，只处理已经合法取得并
  私下保存的本地小型/历史 TSV；它不访问网络。
- `zhihu_schema.sql`：重建数据库的初始化契约。

## 离线数据库重建契约

要求 Python 3.10+，不需要第三方依赖。输入目录必须同时包含以下 UTF-8 TSV：

| 路径模式 | 每行格式 |
|---|---|
| `data/user_*` | `user_url, user_id, followee_num, follower_num, answer_num, agree_num, thanks_num, layer` |
| `data/followee_*` | `user_url, followee_url...` |
| `data/question_*` | `user_url, question_id...` |
| `data/topic/topic_*` | `question_id, topic...` |

表中逗号仅表示字段顺序，实际分隔符均为 tab。请把原始输入和目标数据库放在仓库外
的私有目录；`.gitignore` 只是最后一道防误提交保护，不是访问控制。

```bash
python3 zhihu_database.py \
  --source /private/path/to/crawler-data \
  --db /private/path/to/zhihu.db
```

建库器会：

1. 在打开目标前检查四组输入是否齐全；
2. 严格校验字段数、整数和非负计数，并使用参数化 SQL；
3. 接受完全相同的重复用户行，但拒绝同一用户的冲突画像；对重复关系使用唯一索引去重；
4. 由 `UserQuestion JOIN Question` 确定性生成分析所需的 `UserTopic`；
5. 要求五张表均非空并运行 SQLite integrity check；
6. 聚合报告未抓取 followee 与缺少 topic 的回答关系，不用外键删除这些已知采样边界；
7. 拒绝符号链接目标，只在完整成功后原子安装权限为 `0600` 的数据库，输出聚合行数、
   源文件与 schema 的 SHA-256。

默认拒绝覆盖已有数据库。只有明确需要替换指定目标时才加 `--replace`；失败时旧目标
保持不变，临时数据库会被删除。

## 配置秘密边界

`crawler/config.example.ini` 只是一份空白历史格式示例。真实 `crawler/config.ini`、
cookie、验证码、数据库、crawler 输出、ZIP 和 Parquet 均被忽略，绝不能提交。
这不表示 crawler 获得支持，也不是登录或抓取指南。

## 离线验证

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile zhihu_database.py
```

测试只使用临时目录中的合成用户、关系、问题与话题，覆盖 TSV 契约、包含撇号的文本、
`UserTopic` 派生、SQLite 完整性、私有文件权限、冲突重复、错误信息不回显字段值、
非法编码、CLI 聚合输出、缺失输入、拒绝意外覆盖、失败原子性与敏感路径忽略规则。
新增的 CI 工作流配置为在 Python 3.10 与 3.12 上执行同一离线测试，不安装或调用
crawler/分析依赖；本轮没有把未运行的远端 CI 当作通过证据。

## 已知但未在本轮修复的历史风险

- 当前 crawler 深度参数与报告中的“两层 BFS”表述不一致，并可能在持久连接错误上
  无限重试；确认真实历史运行配置需要原始运行记录或数据，不能靠改代码追认。
- crawler 输出以覆盖方式写文件、错误日志不是可恢复 checkpoint，topic 爬漏也已在
  原 README 中承认。这些问题不能在不访问旧站点/真实数据的前提下闭环。
- 旧分析会遗漏阈值子图中的孤立用户、直接对零计数取对数，并把可视化模式写成统计
  结论；完整修复属于独立的现代分析流水线工作，不在本次 `master` 窄修复范围内。
