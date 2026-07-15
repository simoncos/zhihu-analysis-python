# 幂律拟合结果 (T1.2)

- R>0 且 p<0.1：幂律优于该备择分布；R<0 且 p<0.1：备择分布更优；p≥0.1：无法区分
- gof_p < 0.1 时幂律假设本身被拒绝（CSN bootstrap）

| series               |     n |   n_tail |   alpha |   xmin |   sigma |   gof_p |   R_lognormal |   p_lognormal |   R_exponential |   p_exponential |   R_truncated_power_law |   p_truncated_power_law | verdict                                   |
|:---------------------|------:|---------:|--------:|-------:|--------:|--------:|--------------:|--------------:|----------------:|----------------:|------------------------:|------------------------:|:------------------------------------------|
| profile:followee_num | 25781 |     1587 |  2.625  |    550 |  0.0408 |    0.55 |       -0.8267 |        0.4084 |          4.773  |          0      |                 -0.9593 |                  0.0786 | Alternative favored (truncated_power_law) |
| profile:follower_num | 26161 |      268 |  2.5782 |  75863 |  0.0964 |    0.08 |       -1.2948 |        0.1954 |          2.3637 |          0.0181 |                 -1.9461 |                  0.0102 | Not power law (GOF rejected)              |
| profile:answer_num   | 22614 |     2938 |  2.2818 |    137 |  0.0236 |    0    |       -4.3624 |        0      |          7.6092 |          0      |                 -4.5253 |                  0      | Not power law (GOF rejected)              |
| profile:agree_num    | 21416 |      598 |  2.3612 |  35086 |  0.0557 |    0.05 |       -2.082  |        0.0373 |          3.4531 |          0.0006 |                 -2.3743 |                  0.0002 | Not power law (GOF rejected)              |
| profile:thanks_num   | 20961 |      536 |  2.4256 |   8819 |  0.0616 |    0    |       -2.1057 |        0.0352 |          2.8518 |          0.0043 |                 -2.3995 |                  0.0002 | Not power law (GOF rejected)              |
| induced:in_degree    | 26161 |     2049 |  2.1634 |    311 |  0.0257 |    0    |       -5.3518 |        0      |          6.9737 |          0      |                 -6.5138 |                  0      | Not power law (GOF rejected)              |
| induced:out_degree   | 25648 |     1546 |  2.8698 |    403 |  0.0476 |    0    |       -2.387  |        0.017  |          4.1558 |          0      |                 -2.4441 |                  0      | Not power law (GOF rejected)              |
