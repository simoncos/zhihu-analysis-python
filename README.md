# 知乎社交网络分析

## 简介

项目包含基于[zhihu-python](https://github.com/egrcc/zhihu-python)的多线程爬虫，数据I/O（`SQLite`,`csv`），以及基于用户关注网络的分析（使用[networkx](https://networkx.github.io/)作为图算法库）。

注：[本项目所使用的zhihu-python](https://github.com/simoncos/zhihu-analysis-python/tree/master/crawler)已与原版存在差异

## 文件说明

- `crawler`文件夹：爬虫部分，以广度优先策略爬取知乎数据，并以csv格式储存（这一部分代码目前版本有误，爬到的数据文件与`zhihu_database.py`无法衔接，此外存在topic爬漏的问题，待修复）
- `zhihu_schema.sql`：SQLite数据库的schema
- `zhihu_database.py`：将csv中的数据导入至数据库中
- `zhihu_analysis.py`：从数据库中提取数据并进行分析

## 详细内容

- [Dataset](http://pan.baidu.com/s/1bos5RqR)
- 中文
	- [知乎社交网络分析（上）：基本统计](http://www.jianshu.com/p/60ffb949113f)
	- [知乎社交网络分析（下）：关注网络](http://www.jianshu.com/p/3b2a1895a12d)
- English
	- [Project Report](https://github.com/simoncos/zhihu-analysis-python/tree/master/analysis-report)
