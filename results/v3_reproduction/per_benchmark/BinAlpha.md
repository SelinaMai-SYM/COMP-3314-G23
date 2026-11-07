# BinAlpha

Historical v1/v2 scores are not copied into this file.

# Nine methods

| method | execution_status | blocker | locked_acc | locked_nmi | reason |
| --- | --- | --- | --- | --- | --- |
| kmeans | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  | The Roweis parent is 1404 images, 36 classes, 20x16, SHA-256 3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7. letters26x30 seed 0 stores every parent index and is not the author's draw. |
| sc | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  | The Roweis parent is 1404 images, 36 classes, 20x16, SHA-256 3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7. letters26x30 seed 0 stores every parent index and is not the author's draw. |
| pca_kmeans | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  | The Roweis parent is 1404 images, 36 classes, 20x16, SHA-256 3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7. letters26x30 seed 0 stores every parent index and is not the author's draw. |
| pca_sc | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  | The Roweis parent is 1404 images, 36 classes, 20x16, SHA-256 3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7. letters26x30 seed 0 stores every parent index and is not the author's draw. |
| lda_kmeans | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  | The Roweis parent is 1404 images, 36 classes, 20x16, SHA-256 3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7. letters26x30 seed 0 stores every parent index and is not the author's draw. |
| lda_sc | BLOCKED_METHOD | BLOCKED_METHOD |  |  | Chang et al. name LDA-SC and cite no algorithm. The SLPS paper defines LdaKm, and Ding and Li define LDA-Kmeans. Neither document defines LDA-SC. Status METHOD_DEFINITION_UNRESOLVED. |
| llc | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  | The Roweis parent is 1404 images, 36 classes, 20x16, SHA-256 3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7. letters26x30 seed 0 stores every parent index and is not the author's draw. |
| spls | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  | The Roweis parent is 1404 images, 36 classes, 20x16, SHA-256 3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7. letters26x30 seed 0 stores every parent index and is not the author's draw. |
| ssc | SUBSET_UNVERIFIED | SUBSET_UNVERIFIED |  |  | The Roweis parent is 1404 images, 36 classes, 20x16, SHA-256 3ee9392e64e4e3bb7b35502b69bf2555a0b4197c1b31048c4189b84bc0bc6ea7. letters26x30 seed 0 stores every parent index and is not the author's draw. |

# Y0 configuration summaries

| method | dataset_id | config_name | variant | initialization | report_role | per_run_acc_mean | per_run_acc_sd | batch0_selected_acc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kmeans | BinAlpha_candidate26x30 | raw |  | RANDOM | reference | 0.43866666666666665 | 0.02590181351626592 | 0.4846153846153846 |
| kmeans | BinAlpha_candidate26x30 | raw |  | SKLEARN_GREEDY_KMEANSPP | reference | 0.44233333333333336 | 0.025151648629051632 | 0.4358974358974359 |
| lda_kmeans | BinAlpha_candidate26x30 | k-1=25 |  | FULL_REFIT | reference | 0.439948717948718 | 0.026849292130658772 |  |
| llc | BinAlpha_candidate26x30 | ridge=0.1|mult=1 |  | YU_SHI | grid | 0.48707692307692313 | 0.005211515853335552 | 0.48717948717948717 |
| llc | BinAlpha_candidate26x30 | ridge=1.5|mult=1 |  | YU_SHI | grid | 0.4744102564102564 | 0.003806352582568449 | 0.47435897435897434 |
| llc | BinAlpha_candidate26x30 | ridge=1|mult=0.0625 |  | YU_SHI | grid | 0.28564102564102556 | 0.0010679399074808203 | 0.2858974358974359 |
| llc | BinAlpha_candidate26x30 | ridge=1|mult=0.25 |  | YU_SHI | grid | 0.3756153846153845 | 0.0012283357243301947 | 0.3769230769230769 |
| llc | BinAlpha_candidate26x30 | ridge=1|mult=1 |  | YU_SHI | reference | 0.4798205128205128 | 0.0016546481288080867 | 0.4782051282051282 |
| llc | BinAlpha_candidate26x30 | ridge=1|mult=16 |  | YU_SHI | grid | 0.49212820512820515 | 0.001003489196469083 | 0.49230769230769234 |
| llc | BinAlpha_candidate26x30 | ridge=1|mult=4 |  | YU_SHI | grid | 0.4944615384615385 | 0.0014053718749634293 | 0.4935897435897436 |
| pca_kmeans | BinAlpha_candidate26x30 | d10 |  | RANDOM | grid | 0.4458974358974359 | 0.01681194980565996 | 0.47435897435897434 |
| pca_kmeans | BinAlpha_candidate26x30 | d10 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.46153846153846145 | 0.020695160281063055 | 0.4705128205128205 |
| pca_kmeans | BinAlpha_candidate26x30 | d20 |  | RANDOM | grid | 0.4612307692307692 | 0.023496905113370735 | 0.4858974358974359 |
| pca_kmeans | BinAlpha_candidate26x30 | d20 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.47482051282051285 | 0.020603801375232617 | 0.5 |
| pca_kmeans | BinAlpha_candidate26x30 | d30 |  | RANDOM | grid | 0.4602820512820513 | 0.024838959914040122 | 0.49743589743589745 |
| pca_kmeans | BinAlpha_candidate26x30 | d30 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.47615384615384604 | 0.02168300159259889 | 0.4846153846153846 |
| pca_kmeans | BinAlpha_candidate26x30 | d40 |  | RANDOM | grid | 0.452025641025641 | 0.02260267681807927 | 0.491025641025641 |
| pca_kmeans | BinAlpha_candidate26x30 | d40 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4627692307692308 | 0.022850449851300397 | 0.47307692307692306 |
| pca_kmeans | BinAlpha_candidate26x30 | d50 |  | RANDOM | grid | 0.45082051282051283 | 0.02667054071605923 | 0.5243589743589744 |
| pca_kmeans | BinAlpha_candidate26x30 | d50 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.46541025641025646 | 0.02593951071752915 | 0.4948717948717949 |
| pca_kmeans | BinAlpha_candidate26x30 | d60 |  | RANDOM | grid | 0.44807692307692304 | 0.025897785616074958 | 0.5038461538461538 |
| pca_kmeans | BinAlpha_candidate26x30 | d60 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.45443589743589746 | 0.02503497533325733 | 0.46282051282051284 |
| pca_kmeans | BinAlpha_candidate26x30 | d70 |  | RANDOM | grid | 0.44705128205128214 | 0.024927607890086422 | 0.45897435897435895 |
| pca_kmeans | BinAlpha_candidate26x30 | d70 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4598974358974358 | 0.025262830985845995 | 0.4858974358974359 |
| pca_kmeans | BinAlpha_candidate26x30 | d80 |  | RANDOM | grid | 0.4460256410256411 | 0.024296582079861795 | 0.44743589743589746 |
| pca_kmeans | BinAlpha_candidate26x30 | d80 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.45784615384615385 | 0.02715647258772887 | 0.4756410256410256 |
| pca_kmeans | BinAlpha_candidate26x30 | d90 |  | RANDOM | grid | 0.44653846153846155 | 0.027573988467306822 | 0.4756410256410256 |
| pca_kmeans | BinAlpha_candidate26x30 | d90 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4629743589743589 | 0.026222654992970905 | 0.5038461538461538 |
| pca_kmeans | BinAlpha_candidate26x30 | d100 |  | RANDOM | grid | 0.44382051282051277 | 0.02996472452762721 | 0.491025641025641 |
| pca_kmeans | BinAlpha_candidate26x30 | d100 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.455 | 0.02215473826624035 | 0.4935897435897436 |
| pca_kmeans | BinAlpha_candidate26x30 | d110 |  | RANDOM | grid | 0.44494871794871793 | 0.026741695460596505 | 0.4282051282051282 |
| pca_kmeans | BinAlpha_candidate26x30 | d110 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.459051282051282 | 0.023077519034109515 | 0.4576923076923077 |
| pca_kmeans | BinAlpha_candidate26x30 | d120 |  | RANDOM | grid | 0.4414615384615385 | 0.027489140276213814 | 0.5 |
| pca_kmeans | BinAlpha_candidate26x30 | d120 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4511025641025641 | 0.01975478285747407 | 0.47307692307692306 |
| pca_kmeans | BinAlpha_candidate26x30 | d130 |  | RANDOM | grid | 0.4455641025641025 | 0.027097823170058453 | 0.5115384615384615 |
| pca_kmeans | BinAlpha_candidate26x30 | d130 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.45166666666666666 | 0.018864024319951486 | 0.46923076923076923 |
| pca_kmeans | BinAlpha_candidate26x30 | d140 |  | RANDOM | grid | 0.4432820512820513 | 0.026333608222770206 | 0.5 |
| pca_kmeans | BinAlpha_candidate26x30 | d140 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4496410256410256 | 0.02089363931957981 | 0.4794871794871795 |
| pca_kmeans | BinAlpha_candidate26x30 | d150 |  | RANDOM | grid | 0.4442051282051282 | 0.025704056489962428 | 0.4858974358974359 |
| pca_kmeans | BinAlpha_candidate26x30 | d150 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4546923076923077 | 0.0242943177816874 | 0.4717948717948718 |
| pca_sc | BinAlpha_candidate26x30 | d10 |  | RANDOM | grid | 0.421076923076923 | 0.019237152263546817 | 0.42948717948717946 |
| pca_sc | BinAlpha_candidate26x30 | d10 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.45587179487179486 | 0.01052146394558982 | 0.4641025641025641 |
| pca_sc | BinAlpha_candidate26x30 | d20 |  | RANDOM | grid | 0.443948717948718 | 0.023567436498617558 | 0.4794871794871795 |
| pca_sc | BinAlpha_candidate26x30 | d20 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4643076923076923 | 0.013228363517957456 | 0.46153846153846156 |
| pca_sc | BinAlpha_candidate26x30 | d30 |  | RANDOM | grid | 0.4445128205128205 | 0.028508007002523237 | 0.49230769230769234 |
| pca_sc | BinAlpha_candidate26x30 | d30 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.47984615384615387 | 0.01452333605092746 | 0.4935897435897436 |
| pca_sc | BinAlpha_candidate26x30 | d40 |  | RANDOM | grid | 0.45376923076923076 | 0.023939361398999874 | 0.5025641025641026 |
| pca_sc | BinAlpha_candidate26x30 | d40 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4825384615384615 | 0.0124404416433289 | 0.4935897435897436 |
| pca_sc | BinAlpha_candidate26x30 | d50 |  | RANDOM | grid | 0.44561538461538464 | 0.02877042795980401 | 0.5012820512820513 |
| pca_sc | BinAlpha_candidate26x30 | d50 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4879230769230769 | 0.01145264324105982 | 0.5038461538461538 |
| pca_sc | BinAlpha_candidate26x30 | d60 |  | RANDOM | grid | 0.44128205128205134 | 0.024755780936414964 | 0.4897435897435897 |
| pca_sc | BinAlpha_candidate26x30 | d60 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4743333333333334 | 0.01885733710633662 | 0.46923076923076923 |
| pca_sc | BinAlpha_candidate26x30 | d70 |  | RANDOM | grid | 0.44182051282051277 | 0.02300251099516192 | 0.47435897435897434 |
| pca_sc | BinAlpha_candidate26x30 | d70 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.47812820512820514 | 0.012918022692420992 | 0.48846153846153845 |
| pca_sc | BinAlpha_candidate26x30 | d80 |  | RANDOM | grid | 0.4444871794871795 | 0.023753456103566054 | 0.491025641025641 |
| pca_sc | BinAlpha_candidate26x30 | d80 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.47894871794871796 | 0.010807692152506588 | 0.48717948717948717 |
| pca_sc | BinAlpha_candidate26x30 | d90 |  | RANDOM | grid | 0.4491025641025641 | 0.026495761662789014 | 0.4807692307692308 |
| pca_sc | BinAlpha_candidate26x30 | d90 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.47900000000000004 | 0.013841816674433892 | 0.4897435897435897 |
| pca_sc | BinAlpha_candidate26x30 | d100 |  | RANDOM | grid | 0.4401538461538461 | 0.021975640896658797 | 0.46794871794871795 |
| pca_sc | BinAlpha_candidate26x30 | d100 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.47533333333333333 | 0.011345144923168583 | 0.48333333333333334 |
| pca_sc | BinAlpha_candidate26x30 | d110 |  | RANDOM | grid | 0.4447692307692307 | 0.02653825298153287 | 0.4794871794871795 |
| pca_sc | BinAlpha_candidate26x30 | d110 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4772564102564102 | 0.011082659570473751 | 0.4858974358974359 |
| pca_sc | BinAlpha_candidate26x30 | d120 |  | RANDOM | grid | 0.43894871794871804 | 0.02337858820947657 | 0.48717948717948717 |
| pca_sc | BinAlpha_candidate26x30 | d120 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.47294871794871796 | 0.012522035750182632 | 0.48205128205128206 |
| pca_sc | BinAlpha_candidate26x30 | d130 |  | RANDOM | grid | 0.4431538461538462 | 0.02530736598068545 | 0.4641025641025641 |
| pca_sc | BinAlpha_candidate26x30 | d130 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.473025641025641 | 0.009530710376723752 | 0.4794871794871795 |
| pca_sc | BinAlpha_candidate26x30 | d140 |  | RANDOM | grid | 0.4322051282051282 | 0.025165181734847664 | 0.4641025641025641 |
| pca_sc | BinAlpha_candidate26x30 | d140 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.46253846153846156 | 0.011621856891006277 | 0.46025641025641023 |
| pca_sc | BinAlpha_candidate26x30 | d150 |  | RANDOM | grid | 0.43369230769230765 | 0.019334345178651208 | 0.46025641025641023 |
| pca_sc | BinAlpha_candidate26x30 | d150 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4641538461538462 | 0.01231869820138066 | 0.46282051282051284 |
| sc | BinAlpha_candidate26x30 | k5_median_delta2 |  | RANDOM | reference | 0.44007692307692303 | 0.025467505491438953 | 0.4576923076923077 |
| sc | BinAlpha_candidate26x30 | k5_median_delta2 |  | SKLEARN_GREEDY_KMEANSPP | reference | 0.47271794871794875 | 0.01370580261099884 | 0.4641025641025641 |
| spls | BinAlpha_candidate26x30 | alpha=0.05|d=10 | one_shot | RANDOM | grid | 0.48543589743589743 | 0.023448602862656927 | 0.5294871794871795 |
| spls | BinAlpha_candidate26x30 | alpha=0.05|d=10 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.500102564102564 | 0.019227873495570657 | 0.5102564102564102 |
| spls | BinAlpha_candidate26x30 | alpha=0.05|d=20 | one_shot | RANDOM | grid | 0.4856153846153846 | 0.024274537618991093 | 0.5217948717948718 |
| spls | BinAlpha_candidate26x30 | alpha=0.05|d=20 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.5011538461538462 | 0.018645822054397666 | 0.5064102564102564 |
| spls | BinAlpha_candidate26x30 | alpha=0.05|d=30 | one_shot | RANDOM | grid | 0.48766666666666675 | 0.025741417805602095 | 0.5217948717948718 |
| spls | BinAlpha_candidate26x30 | alpha=0.05|d=30 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.5052564102564102 | 0.015793982353122907 | 0.5115384615384615 |
| spls | BinAlpha_candidate26x30 | alpha=0.05|d=40 | one_shot | RANDOM | grid | 0.48615384615384616 | 0.0254690728266989 | 0.5166666666666667 |
| spls | BinAlpha_candidate26x30 | alpha=0.05|d=40 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.5024871794871796 | 0.018965393811714415 | 0.5166666666666667 |
