# N2 heat geometry candidate: properties and limits

Use the same original affinity A and its symmetric normalized Laplacian L. No self-loops or new pixel preprocessing are introduced.

K_t=exp(-tL); exact features are H_t=exp(-tL/2), so H_t H_t^T=K_t and d_t^2(i,j)=K_ii+K_jj-2K_ij. Distances between rows of K_t instead correspond to K_(2t), and are not substituted.

Duhamel's formula and contraction of exp(-sL) for symmetric PSD L give ||exp(-tL)-exp(-tL')||_2<=t||L-L'||_2. For v=e_i-e_j with ||v||^2=2, squared-distance change is bounded by 2t||L-L'||_2. A kNN squared-distance boundary gap greater than 4t||L-L'||_2 therefore cannot cross under that perturbation. None is an ACC guarantee; very large t may erase useful distinctions.

Scalable features Z=expm_multiply(-tL/2,R), Gaussian R_ij~N(0,1/r), use the full spectrum action but approximate geometry. They are not exact H and do not automatically inherit exact distance bounds. The frozen primary is t=4,r=128,seed=20261108; other settings are sensitivities. R is fixed within a perturbation comparison. No final truncation to c vectors is permitted.

Principal angles use raw eigenvectors, not row-normalized F. Sign/orthogonal coordinate changes preserve Euclidean geometry and are not eigenspace failures. Hard-r, heat-only, heat+SSC and W-only controls distinguish dimensions, filtering and shrinkage. N2 is a candidate after evidence, not an established explanation for YaleB.
