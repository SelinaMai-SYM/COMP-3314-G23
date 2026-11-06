# ORL

Historical v1/v2 scores are not copied into this file.

# Nine methods

| method | execution_status | blocker | locked_acc | locked_nmi | reason |
| --- | --- | --- | --- | --- | --- |
| kmeans | PLANNED |  |  |  |  |
| sc | PLANNED |  |  |  |  |
| pca_kmeans | PLANNED |  |  |  |  |
| pca_sc | PLANNED |  |  |  |  |
| lda_kmeans | PLANNED |  |  |  |  |
| lda_sc | BLOCKED_METHOD | BLOCKED_METHOD |  |  | Chang et al. name LDA-SC and cite no algorithm. The SLPS paper defines LdaKm, and Ding and Li define LDA-Kmeans. Neither document defines LDA-SC. Status METHOD_DEFINITION_UNRESOLVED. |
| llc | PLANNED |  |  |  |  |
| spls | PLANNED |  |  |  |  |
| ssc | PLANNED |  |  |  |  |

# Y0 configuration summaries

| method | dataset_id | config_name | variant | initialization | report_role | per_run_acc_mean | per_run_acc_sd | batch0_selected_acc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kmeans | ORL_att92 | raw |  | RANDOM | reference | 0.61455 | 0.028511947012594206 | 0.6425 |
| kmeans | ORL_att92 | raw |  | SKLEARN_GREEDY_KMEANSPP | reference | 0.6918500000000001 | 0.03507575620666485 | 0.725 |
| lda_kmeans | ORL_att92 | k-1=39 |  | FULL_REFIT | reference | 0.56305 | 0.04142330631567752 |  |
| llc | ORL_att92 | ridge=0.1|mult=1 |  | YU_SHI | grid | 0.8370500000000001 | 0.003017381619340646 | 0.835 |
| llc | ORL_att92 | ridge=1.5|mult=1 |  | YU_SHI | grid | 0.81575 | 0.007235999853340994 | 0.8125 |
| llc | ORL_att92 | ridge=1|mult=0.0625 |  | YU_SHI | grid | 0.82545 | 0.0027053424092008047 | 0.8275 |
| llc | ORL_att92 | ridge=1|mult=0.25 |  | YU_SHI | grid | 0.8290500000000001 | 0.002075734440960055 | 0.83 |
| llc | ORL_att92 | ridge=1|mult=1 |  | YU_SHI | reference | 0.8156 | 0.007045044574821667 | 0.815 |
| llc | ORL_att92 | ridge=1|mult=16 |  | YU_SHI | grid | 0.8107000000000001 | 0.006061757002650611 | 0.8025 |
| llc | ORL_att92 | ridge=1|mult=4 |  | YU_SHI | grid | 0.8112500000000001 | 0.00449631368286219 | 0.805 |
| pca_kmeans | ORL_att92 | d10 |  | RANDOM | grid | 0.5902 | 0.03131407716301773 | 0.645 |
| pca_kmeans | ORL_att92 | d10 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6308 | 0.022640941784695244 | 0.6325 |
| pca_kmeans | ORL_att92 | d20 |  | RANDOM | grid | 0.62105 | 0.026332305370446566 | 0.645 |
| pca_kmeans | ORL_att92 | d20 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6839999999999999 | 0.025773740789526736 | 0.725 |
| pca_kmeans | ORL_att92 | d30 |  | RANDOM | grid | 0.6306499999999999 | 0.02855271708719197 | 0.6575 |
| pca_kmeans | ORL_att92 | d30 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7066 | 0.02998622132559812 | 0.715 |
| pca_kmeans | ORL_att92 | d40 |  | RANDOM | grid | 0.63115 | 0.03275297930053424 | 0.655 |
| pca_kmeans | ORL_att92 | d40 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7161500000000001 | 0.025789621785453437 | 0.7425 |
| pca_kmeans | ORL_att92 | d50 |  | RANDOM | grid | 0.6285000000000001 | 0.02662571259945114 | 0.6775 |
| pca_kmeans | ORL_att92 | d50 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7143999999999999 | 0.027300108394791155 | 0.7925 |
| pca_kmeans | ORL_att92 | d60 |  | RANDOM | grid | 0.6259 | 0.028712864214992057 | 0.6625 |
| pca_kmeans | ORL_att92 | d60 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.709 | 0.02509166867178614 | 0.7175 |
| pca_kmeans | ORL_att92 | d70 |  | RANDOM | grid | 0.6233000000000001 | 0.02950458283323567 | 0.6 |
| pca_kmeans | ORL_att92 | d70 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7061 | 0.0260746573343168 | 0.74 |
| pca_kmeans | ORL_att92 | d80 |  | RANDOM | grid | 0.62275 | 0.029085772172269084 | 0.61 |
| pca_kmeans | ORL_att92 | d80 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.69625 | 0.031972764238664506 | 0.7075 |
| pca_kmeans | ORL_att92 | d90 |  | RANDOM | grid | 0.6202000000000001 | 0.028534976747128845 | 0.6325 |
| pca_kmeans | ORL_att92 | d90 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7034999999999999 | 0.03377597262153398 | 0.755 |
| pca_kmeans | ORL_att92 | d100 |  | RANDOM | grid | 0.61625 | 0.02880374302490734 | 0.6475 |
| pca_kmeans | ORL_att92 | d100 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7027000000000001 | 0.03584205715670474 | 0.7725 |
| pca_kmeans | ORL_att92 | d110 |  | RANDOM | grid | 0.61795 | 0.028832247040210982 | 0.6475 |
| pca_kmeans | ORL_att92 | d110 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7043499999999999 | 0.034377889488947475 | 0.7275 |
| pca_kmeans | ORL_att92 | d120 |  | RANDOM | grid | 0.6175999999999999 | 0.029867735646564524 | 0.6375 |
| pca_kmeans | ORL_att92 | d120 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.70455 | 0.031346036106529265 | 0.7525 |
| pca_kmeans | ORL_att92 | d130 |  | RANDOM | grid | 0.6156 | 0.028241668448140484 | 0.6475 |
| pca_kmeans | ORL_att92 | d130 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.69355 | 0.029233795441549623 | 0.7475 |
| pca_kmeans | ORL_att92 | d140 |  | RANDOM | grid | 0.6147500000000001 | 0.02906822551677136 | 0.6475 |
| pca_kmeans | ORL_att92 | d140 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6995999999999999 | 0.03332875818942225 | 0.77 |
| pca_kmeans | ORL_att92 | d150 |  | RANDOM | grid | 0.61315 | 0.02879736559663266 | 0.6525 |
| pca_kmeans | ORL_att92 | d150 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7003499999999999 | 0.031457008238974966 | 0.7375 |
| pca_sc | ORL_att92 | d10 |  | RANDOM | grid | 0.5015499999999999 | 0.04001559007411476 | 0.5875 |
| pca_sc | ORL_att92 | d10 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6523 | 0.009607607529920213 | 0.645 |
| pca_sc | ORL_att92 | d20 |  | RANDOM | grid | 0.5486000000000001 | 0.0410113224784153 | 0.67 |
| pca_sc | ORL_att92 | d20 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.722 | 0.015518257844571745 | 0.7125 |
| pca_sc | ORL_att92 | d30 |  | RANDOM | grid | 0.55195 | 0.039687201710272256 | 0.6125 |
| pca_sc | ORL_att92 | d30 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7761 | 0.015204054239120654 | 0.7825 |
| pca_sc | ORL_att92 | d40 |  | RANDOM | grid | 0.55395 | 0.0425767314530424 | 0.6425 |
| pca_sc | ORL_att92 | d40 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7667500000000002 | 0.012987926104262998 | 0.775 |
| pca_sc | ORL_att92 | d50 |  | RANDOM | grid | 0.54945 | 0.04014733706573063 | 0.58 |
| pca_sc | ORL_att92 | d50 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7597999999999999 | 0.011854130426280338 | 0.7775 |
| pca_sc | ORL_att92 | d60 |  | RANDOM | grid | 0.5528 | 0.04276967264264697 | 0.6475 |
| pca_sc | ORL_att92 | d60 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7620499999999999 | 0.009458421363730705 | 0.76 |
| pca_sc | ORL_att92 | d70 |  | RANDOM | grid | 0.5524999999999999 | 0.03873971226174052 | 0.65 |
| pca_sc | ORL_att92 | d70 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.75315 | 0.01055609409057059 | 0.7575 |
| pca_sc | ORL_att92 | d80 |  | RANDOM | grid | 0.5508500000000001 | 0.044041984839144434 | 0.6575 |
| pca_sc | ORL_att92 | d80 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.76545 | 0.012903586750218255 | 0.76 |
| pca_sc | ORL_att92 | d90 |  | RANDOM | grid | 0.5570999999999999 | 0.042418469215805575 | 0.665 |
| pca_sc | ORL_att92 | d90 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7799499999999999 | 0.013937634414104305 | 0.8025 |
| pca_sc | ORL_att92 | d100 |  | RANDOM | grid | 0.5543999999999999 | 0.042790305024405145 | 0.6425 |
| pca_sc | ORL_att92 | d100 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.78175 | 0.013153819186216355 | 0.7975 |
| pca_sc | ORL_att92 | d110 |  | RANDOM | grid | 0.5639 | 0.04467615900761243 | 0.63 |
| pca_sc | ORL_att92 | d110 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7757000000000001 | 0.014223435676691482 | 0.8 |
| pca_sc | ORL_att92 | d120 |  | RANDOM | grid | 0.5698500000000001 | 0.04442779627252126 | 0.6425 |
| pca_sc | ORL_att92 | d120 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7839500000000001 | 0.014169977604291499 | 0.82 |
| pca_sc | ORL_att92 | d130 |  | RANDOM | grid | 0.5719000000000001 | 0.044967562004772525 | 0.6475 |
| pca_sc | ORL_att92 | d130 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7883999999999999 | 0.012874591334905209 | 0.815 |
| pca_sc | ORL_att92 | d140 |  | RANDOM | grid | 0.56835 | 0.04419232664947477 | 0.625 |
| pca_sc | ORL_att92 | d140 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7848999999999999 | 0.012110882271236701 | 0.81 |
| pca_sc | ORL_att92 | d150 |  | RANDOM | grid | 0.5664999999999999 | 0.04668609896676626 | 0.6325 |
| pca_sc | ORL_att92 | d150 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7796499999999998 | 0.011327792262882502 | 0.7925 |
| sc | ORL_att92 | k5_median_delta2 |  | RANDOM | reference | 0.5618 | 0.041927537100895154 | 0.6225 |
| sc | ORL_att92 | k5_median_delta2 |  | SKLEARN_GREEDY_KMEANSPP | reference | 0.7832500000000002 | 0.013095508655213665 | 0.79 |
| spls | ORL_att92 | alpha=0.05|d=10 | one_shot | RANDOM | grid | 0.62805 | 0.03473401115063223 | 0.69 |
| spls | ORL_att92 | alpha=0.05|d=10 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.6953999999999999 | 0.018621909413486078 | 0.6975 |
| spls | ORL_att92 | alpha=0.05|d=20 | one_shot | RANDOM | grid | 0.63205 | 0.032244640434259675 | 0.6875 |
| spls | ORL_att92 | alpha=0.05|d=20 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.7044 | 0.01937518926833164 | 0.7325 |
| spls | ORL_att92 | alpha=0.05|d=30 | one_shot | RANDOM | grid | 0.6346999999999999 | 0.031645517463144826 | 0.6925 |
| spls | ORL_att92 | alpha=0.05|d=30 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.7163 | 0.013917028183825314 | 0.725 |
| spls | ORL_att92 | alpha=0.05|d=40 | one_shot | RANDOM | grid | 0.6364 | 0.03256531897586756 | 0.6775 |
| spls | ORL_att92 | alpha=0.05|d=40 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.71485 | 0.017564821638253937 | 0.7325 |
