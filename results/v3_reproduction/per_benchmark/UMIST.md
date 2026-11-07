# UMIST

Historical v1/v2 scores are not copied into this file.

# Nine methods

| method | execution_status | blocker | locked_acc | locked_nmi | reason |
| --- | --- | --- | --- | --- | --- |
| kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  | No 564-image file. LZUFE umist.mat is 574x10304 with 10 exact duplicate rows, which were not removed. Zenodo 3634017 is 575x644 (28x23), MD5 matched. Roweis umist_cropped.mat is 575 images at 112x92 and does not share pixels with the wayback 575. None of these is the SSC 564-image set. |
| sc | BLOCKED_DATA | BLOCKED_DATA |  |  | No 564-image file. LZUFE umist.mat is 574x10304 with 10 exact duplicate rows, which were not removed. Zenodo 3634017 is 575x644 (28x23), MD5 matched. Roweis umist_cropped.mat is 575 images at 112x92 and does not share pixels with the wayback 575. None of these is the SSC 564-image set. |
| pca_kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  | No 564-image file. LZUFE umist.mat is 574x10304 with 10 exact duplicate rows, which were not removed. Zenodo 3634017 is 575x644 (28x23), MD5 matched. Roweis umist_cropped.mat is 575 images at 112x92 and does not share pixels with the wayback 575. None of these is the SSC 564-image set. |
| pca_sc | BLOCKED_DATA | BLOCKED_DATA |  |  | No 564-image file. LZUFE umist.mat is 574x10304 with 10 exact duplicate rows, which were not removed. Zenodo 3634017 is 575x644 (28x23), MD5 matched. Roweis umist_cropped.mat is 575 images at 112x92 and does not share pixels with the wayback 575. None of these is the SSC 564-image set. |
| lda_kmeans | BLOCKED_DATA | BLOCKED_DATA |  |  | No 564-image file. LZUFE umist.mat is 574x10304 with 10 exact duplicate rows, which were not removed. Zenodo 3634017 is 575x644 (28x23), MD5 matched. Roweis umist_cropped.mat is 575 images at 112x92 and does not share pixels with the wayback 575. None of these is the SSC 564-image set. |
| lda_sc | BLOCKED_METHOD | BLOCKED_METHOD |  |  | Chang et al. name LDA-SC and cite no algorithm. The SLPS paper defines LdaKm, and Ding and Li define LDA-Kmeans. Neither document defines LDA-SC. Status METHOD_DEFINITION_UNRESOLVED. |
| llc | BLOCKED_DATA | BLOCKED_DATA |  |  | No 564-image file. LZUFE umist.mat is 574x10304 with 10 exact duplicate rows, which were not removed. Zenodo 3634017 is 575x644 (28x23), MD5 matched. Roweis umist_cropped.mat is 575 images at 112x92 and does not share pixels with the wayback 575. None of these is the SSC 564-image set. |
| spls | BLOCKED_DATA | BLOCKED_DATA |  |  | No 564-image file. LZUFE umist.mat is 574x10304 with 10 exact duplicate rows, which were not removed. Zenodo 3634017 is 575x644 (28x23), MD5 matched. Roweis umist_cropped.mat is 575 images at 112x92 and does not share pixels with the wayback 575. None of these is the SSC 564-image set. |
| ssc | BLOCKED_DATA | BLOCKED_DATA |  |  | No 564-image file. LZUFE umist.mat is 574x10304 with 10 exact duplicate rows, which were not removed. Zenodo 3634017 is 575x644 (28x23), MD5 matched. Roweis umist_cropped.mat is 575 images at 112x92 and does not share pixels with the wayback 575. None of these is the SSC 564-image set. |

# Y0 configuration summaries

| method | dataset_id | config_name | variant | initialization | report_role | per_run_acc_mean | per_run_acc_sd | batch0_selected_acc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kmeans | UMIST_precropped575 | raw |  | RANDOM | reference | 0.42493913043478265 | 0.02828287451272447 | 0.42434782608695654 |
| kmeans | UMIST_precropped575 | raw |  | SKLEARN_GREEDY_KMEANSPP | reference | 0.42351304347826085 | 0.021722414158646133 | 0.4121739130434783 |
| lda_kmeans | UMIST_precropped575 | k-1=19 |  | FULL_REFIT | reference | 0.4092869565217391 | 0.035312048674717926 |  |
| llc | UMIST_precropped575 | ridge=0.1|mult=1 |  | YU_SHI | grid | 0.665008695652174 | 0.0022740724316022603 | 0.6643478260869565 |
| llc | UMIST_precropped575 | ridge=1.5|mult=1 |  | YU_SHI | grid | 0.5947478260869565 | 0.000895099802964076 | 0.5947826086956521 |
| llc | UMIST_precropped575 | ridge=1|mult=0.0625 |  | YU_SHI | grid | 0.5992695652173914 | 0.004932662573425136 | 0.6 |
| llc | UMIST_precropped575 | ridge=1|mult=0.25 |  | YU_SHI | grid | 0.5938086956521739 | 0.02133512074093344 | 0.577391304347826 |
| llc | UMIST_precropped575 | ridge=1|mult=1 |  | YU_SHI | reference | 0.6208695652173913 | 0.0 | 0.6208695652173913 |
| llc | UMIST_precropped575 | ridge=1|mult=16 |  | YU_SHI | grid | 0.6203130434782609 | 0.000819499254781187 | 0.6191304347826087 |
| llc | UMIST_precropped575 | ridge=1|mult=4 |  | YU_SHI | grid | 0.6195130434782609 | 0.0007277425349504334 | 0.6191304347826087 |
| pca_kmeans | UMIST_precropped575 | d10 |  | RANDOM | grid | 0.4063652173913043 | 0.018991542262811554 | 0.4260869565217391 |
| pca_kmeans | UMIST_precropped575 | d10 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.40643478260869564 | 0.01767034351910936 | 0.39652173913043476 |
| pca_kmeans | UMIST_precropped575 | d20 |  | RANDOM | grid | 0.4292521739130435 | 0.022315178871235707 | 0.42434782608695654 |
| pca_kmeans | UMIST_precropped575 | d20 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4305739130434783 | 0.020342622894754386 | 0.4469565217391304 |
| pca_kmeans | UMIST_precropped575 | d30 |  | RANDOM | grid | 0.429008695652174 | 0.02450309220728759 | 0.4330434782608696 |
| pca_kmeans | UMIST_precropped575 | d30 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4192695652173913 | 0.020447793626387625 | 0.4226086956521739 |
| pca_kmeans | UMIST_precropped575 | d40 |  | RANDOM | grid | 0.4301217391304348 | 0.02478113602623305 | 0.4191304347826087 |
| pca_kmeans | UMIST_precropped575 | d40 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4304347826086956 | 0.0216256131120335 | 0.42782608695652175 |
| pca_kmeans | UMIST_precropped575 | d50 |  | RANDOM | grid | 0.42639999999999995 | 0.02374897982373363 | 0.4747826086956522 |
| pca_kmeans | UMIST_precropped575 | d50 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.42111304347826084 | 0.01962893302669611 | 0.4260869565217391 |
| pca_kmeans | UMIST_precropped575 | d60 |  | RANDOM | grid | 0.4295304347826087 | 0.025107898019496724 | 0.4747826086956522 |
| pca_kmeans | UMIST_precropped575 | d60 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4202782608695652 | 0.02237021172093226 | 0.4469565217391304 |
| pca_kmeans | UMIST_precropped575 | d70 |  | RANDOM | grid | 0.42817391304347824 | 0.02641731080948043 | 0.42434782608695654 |
| pca_kmeans | UMIST_precropped575 | d70 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.42765217391304344 | 0.022618931544064018 | 0.4156521739130435 |
| pca_kmeans | UMIST_precropped575 | d80 |  | RANDOM | grid | 0.4274434782608696 | 0.023942087709840878 | 0.40869565217391307 |
| pca_kmeans | UMIST_precropped575 | d80 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.42445217391304346 | 0.02273097775370185 | 0.4226086956521739 |
| pca_kmeans | UMIST_precropped575 | d90 |  | RANDOM | grid | 0.4261565217391305 | 0.024360397312362475 | 0.47130434782608693 |
| pca_kmeans | UMIST_precropped575 | d90 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.42420869565217395 | 0.02106340033900716 | 0.41739130434782606 |
| pca_kmeans | UMIST_precropped575 | d100 |  | RANDOM | grid | 0.42563478260869564 | 0.025465074977191745 | 0.4747826086956522 |
| pca_kmeans | UMIST_precropped575 | d100 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.42090434782608704 | 0.02265775851808828 | 0.40869565217391307 |
| pca_kmeans | UMIST_precropped575 | d110 |  | RANDOM | grid | 0.42719999999999997 | 0.02645177616584267 | 0.4747826086956522 |
| pca_kmeans | UMIST_precropped575 | d110 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.42553043478260866 | 0.018990989723432373 | 0.43130434782608695 |
| pca_kmeans | UMIST_precropped575 | d120 |  | RANDOM | grid | 0.4262956521739131 | 0.02707878504501093 | 0.42086956521739133 |
| pca_kmeans | UMIST_precropped575 | d120 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.42782608695652163 | 0.018578801585927864 | 0.43130434782608695 |
| pca_kmeans | UMIST_precropped575 | d130 |  | RANDOM | grid | 0.42740869565217393 | 0.02570812780709359 | 0.4747826086956522 |
| pca_kmeans | UMIST_precropped575 | d130 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.42667826086956523 | 0.025525118097109337 | 0.4226086956521739 |
| pca_kmeans | UMIST_precropped575 | d140 |  | RANDOM | grid | 0.4266086956521739 | 0.028343133290754427 | 0.4121739130434783 |
| pca_kmeans | UMIST_precropped575 | d140 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.4299130434782608 | 0.017850201189253224 | 0.4226086956521739 |
| pca_kmeans | UMIST_precropped575 | d150 |  | RANDOM | grid | 0.4246956521739131 | 0.02724096430347167 | 0.4573913043478261 |
| pca_kmeans | UMIST_precropped575 | d150 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.42420869565217395 | 0.02224633509539263 | 0.3808695652173913 |
| pca_sc | UMIST_precropped575 | d10 |  | RANDOM | grid | 0.4705739130434783 | 0.05345264100895432 | 0.5721739130434783 |
| pca_sc | UMIST_precropped575 | d10 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.5361739130434783 | 0.01568664251658571 | 0.52 |
| pca_sc | UMIST_precropped575 | d20 |  | RANDOM | grid | 0.5456 | 0.07466740884480896 | 0.64 |
| pca_sc | UMIST_precropped575 | d20 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.698991304347826 | 0.013248736940395415 | 0.6956521739130435 |
| pca_sc | UMIST_precropped575 | d30 |  | RANDOM | grid | 0.5455304347826087 | 0.07095805276981437 | 0.662608695652174 |
| pca_sc | UMIST_precropped575 | d30 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.698886956521739 | 0.024082750234147302 | 0.7060869565217391 |
| pca_sc | UMIST_precropped575 | d40 |  | RANDOM | grid | 0.5428521739130435 | 0.068992326034545 | 0.6782608695652174 |
| pca_sc | UMIST_precropped575 | d40 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.703582608695652 | 0.018960803143908293 | 0.7060869565217391 |
| pca_sc | UMIST_precropped575 | d50 |  | RANDOM | grid | 0.5469913043478261 | 0.07575663320296566 | 0.6695652173913044 |
| pca_sc | UMIST_precropped575 | d50 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6956521739130436 | 0.017922672096269746 | 0.7026086956521739 |
| pca_sc | UMIST_precropped575 | d60 |  | RANDOM | grid | 0.5452173913043479 | 0.06341514529473692 | 0.6730434782608695 |
| pca_sc | UMIST_precropped575 | d60 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6949217391304348 | 0.016235183676119525 | 0.6956521739130435 |
| pca_sc | UMIST_precropped575 | d70 |  | RANDOM | grid | 0.5475130434782609 | 0.06174669336433919 | 0.6747826086956522 |
| pca_sc | UMIST_precropped575 | d70 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.7001391304347827 | 0.015897088116813316 | 0.7043478260869566 |
| pca_sc | UMIST_precropped575 | d80 |  | RANDOM | grid | 0.5460869565217391 | 0.0656662459871307 | 0.6347826086956522 |
| pca_sc | UMIST_precropped575 | d80 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.698886956521739 | 0.019138531802627975 | 0.7060869565217391 |
| pca_sc | UMIST_precropped575 | d90 |  | RANDOM | grid | 0.5482782608695653 | 0.06432893557101185 | 0.6365217391304347 |
| pca_sc | UMIST_precropped575 | d90 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6940869565217391 | 0.020306664773782783 | 0.7026086956521739 |
| pca_sc | UMIST_precropped575 | d100 |  | RANDOM | grid | 0.5494260869565217 | 0.06051394660641234 | 0.6695652173913044 |
| pca_sc | UMIST_precropped575 | d100 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6929043478260871 | 0.018539189699767592 | 0.7008695652173913 |
| pca_sc | UMIST_precropped575 | d110 |  | RANDOM | grid | 0.5512347826086956 | 0.06620543249382178 | 0.6643478260869565 |
| pca_sc | UMIST_precropped575 | d110 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6946434782608695 | 0.013198557543238395 | 0.6956521739130435 |
| pca_sc | UMIST_precropped575 | d120 |  | RANDOM | grid | 0.5531130434782608 | 0.06282026758187127 | 0.6643478260869565 |
| pca_sc | UMIST_precropped575 | d120 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6920695652173913 | 0.01337195389169154 | 0.6956521739130435 |
| pca_sc | UMIST_precropped575 | d130 |  | RANDOM | grid | 0.5445913043478261 | 0.054022283922633106 | 0.6452173913043479 |
| pca_sc | UMIST_precropped575 | d130 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6098434782608696 | 0.024548821785477383 | 0.6086956521739131 |
| pca_sc | UMIST_precropped575 | d140 |  | RANDOM | grid | 0.5437913043478261 | 0.05450055133722143 | 0.6226086956521739 |
| pca_sc | UMIST_precropped575 | d140 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6120347826086956 | 0.02441324713237607 | 0.6139130434782609 |
| pca_sc | UMIST_precropped575 | d150 |  | RANDOM | grid | 0.5469217391304347 | 0.05506146125247585 | 0.5860869565217391 |
| pca_sc | UMIST_precropped575 | d150 |  | SKLEARN_GREEDY_KMEANSPP | grid | 0.6131478260869565 | 0.0275163775929839 | 0.6139130434782609 |
| sc | UMIST_precropped575 | k5_median_delta2 |  | RANDOM | reference | 0.5612869565217392 | 0.05166365092272939 | 0.6747826086956522 |
| sc | UMIST_precropped575 | k5_median_delta2 |  | SKLEARN_GREEDY_KMEANSPP | reference | 0.6148869565217392 | 0.017621055615895415 | 0.6034782608695652 |
| spls | UMIST_precropped575 | alpha=0.05|d=10 | one_shot | RANDOM | grid | 0.4993739130434783 | 0.038727508496612016 | 0.4817391304347826 |
| spls | UMIST_precropped575 | alpha=0.05|d=10 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.5123478260869565 | 0.033695523370392395 | 0.4817391304347826 |
| spls | UMIST_precropped575 | alpha=0.05|d=20 | one_shot | RANDOM | grid | 0.5073739130434782 | 0.0431208879722424 | 0.5217391304347826 |
| spls | UMIST_precropped575 | alpha=0.05|d=20 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.5198260869565218 | 0.02888245508203747 | 0.5217391304347826 |
| spls | UMIST_precropped575 | alpha=0.05|d=30 | one_shot | RANDOM | grid | 0.5050434782608696 | 0.03964582212237256 | 0.5304347826086957 |
| spls | UMIST_precropped575 | alpha=0.05|d=30 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.520904347826087 | 0.029135644291760163 | 0.5234782608695652 |
| spls | UMIST_precropped575 | alpha=0.05|d=40 | one_shot | RANDOM | grid | 0.5037913043478262 | 0.040061586014172125 | 0.5304347826086957 |
| spls | UMIST_precropped575 | alpha=0.05|d=40 | one_shot | SKLEARN_GREEDY_KMEANSPP | grid | 0.5210782608695652 | 0.032950675266244914 | 0.5234782608695652 |
