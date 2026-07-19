# Expert finding on the 2015 Zhihu snapshot: four method generations

Task: predict log10(1+agree_num) from network structure only; test split of 5233 users.

> Pilot evidence only: one fixed split/seed, no confidence intervals, and a
> comparison between supervised GNNs and unsupervised structural scores. These
> values must not be presented as a stable method ranking until repeated and
> matched-baseline evaluation is complete.

| method | Spearman ρ | NDCG@100 | P@100 |
|---|---|---|---|
| in-degree | 0.649 | 0.781 | 0.50 |
| PageRank | 0.528 | 0.679 | 0.40 |
| HITS authority | 0.649 | 0.817 | 0.53 |
| DeepWalk + ridge | 0.745 | 0.648 | 0.36 |
| GraphSAGE | 0.843 | 0.820 | 0.56 |
| Metapath walks + ridge | 0.751 | 0.659 | 0.40 |
| Hetero-GraphSAGE | 0.871 | 0.845 | 0.60 |
