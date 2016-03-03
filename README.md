# 知乎社交网络分析

## 简介

项目包含基于[zhihu-python](https://github.com/egrcc/zhihu-python)的多线程爬虫，数据I/O（`SQLite`,`csv`），以及基于用户关注网络的分析（使用[networkx](https://networkx.github.io/)作为图算法库）。

注：目前`zhihu-python`最新版本已与本项目不兼容，但在[这里](https://github.com/simoncos/zhihu-analysis-python/tree/master/crawler)你可以找到其在本项目中所使用的源代码版本。

## 文件说明

- `crawler`文件夹：爬虫部分，以广度优先策略爬取知乎数据，并以csv格式储存
- `zhihu_schema.sql`：SQLite数据库的schema
- `zhihu_database.py`：将csv中的数据导入至数据库中
- `zhihu_analysis.py`：从数据库中提取数据并进行分析

## 详细内容

- 中文
	- [知乎社交网络分析（上）：基本统计](http://www.jianshu.com/p/60ffb949113f)
	- 知乎社交网络分析（下）：关注网络
- English
	- [Project Report](https://github.com/simoncos/zhihu-analysis-python/tree/master/analysis-report)