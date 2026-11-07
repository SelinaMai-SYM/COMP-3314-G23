# Table 5. EX1 original SSC vs Reliability-aware SSC

A0 = union kNN W. A1 = mutual kNN W. Same optimizer, gamma=1, k=5 unless noted.

| Dataset | A0 SSC ACC | A1 RSSC ACC | A0 SSC NMI | A1 RSSC NMI | n trials | run ids |
| --- | --- | --- | --- | --- | --- | --- |
| ORL | 53.7 ± 2.8 | 54.0 ± 2.8 | 76.7 ± 1.5 | 76.6 ± 1.5 | 50 | ssc=20261020_015848__EX1__SSC__ORL__26fa9502; rssc=20261020_015850__EX1__RSSC__ORL__536aa460 |
| JAFFE | 68.6 ± 11.3 | 68.7 ± 11.3 | 83.0 ± 5.8 | 83.0 ± 5.9 | 50 | ssc=20261020_015852__EX1__SSC__JAFFE__63609097; rssc=20261020_015854__EX1__RSSC__JAFFE__a0e6ba16 |
| YaleB | 19.7 ± 1.1 | 19.9 ± 1.3 | 29.5 ± 1.0 | 29.8 ± 1.2 | 10 | ssc=20261020_015856__EX1__SSC__YALEB__034ffdfa; rssc=20261020_015905__EX1__RSSC__YALEB__73e58859 |
| USPS | 62.1 ± 0.0 | N/A — not reproduced | 73.3 ± 0.0 | N/A — not reproduced | 1 | ssc=20261020_020231__TRACKA__SSC__USPS__829559a2 |
