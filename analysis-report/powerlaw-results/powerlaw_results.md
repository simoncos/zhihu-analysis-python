# Power-law statistical tests (CSN method) on 2015 Zhihu features

| feature | n_tail | alpha | xmin | R vs TPL | p | R vs lognormal | p | verdict |
|---|---|---|---|---|---|---|---|---|
| followee_num | 1587 | 2.625 | 550 | -0.96 | 0.0786 | -0.83 | 0.408 | power law plausible; alternatives not distinguishable |
| follower_num | 268 | 2.578 | 75863 | -1.95 | 0.0102 | -1.29 | 0.195 | truncated power law favored over pure power law |
| answer_num | 2938 | 2.282 | 137 | -4.53 | 4.56e-14 | -4.36 | 1.29e-05 | truncated power law favored over pure power law |
| agree_num | 598 | 2.361 | 35086 | -2.37 | 0.000247 | -2.08 | 0.0373 | truncated power law favored over pure power law |
| thanks_num | 536 | 2.426 | 8819 | -2.40 | 0.000183 | -2.11 | 0.0352 | truncated power law favored over pure power law |

R > 0 favors pure power law, R < 0 favors the alternative; sign meaningful only when p < 0.05 (Clauset-Shalizi-Newman 2009).
