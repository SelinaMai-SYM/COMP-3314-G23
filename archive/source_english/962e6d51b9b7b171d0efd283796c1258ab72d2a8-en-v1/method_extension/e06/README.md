# E06 — alternating graph and shrinkage

Start from the control F. For three outer iterations, build a kNN affinity on the current representation, freeze it, and run E8 with the data term still anchored at the original F. The next graph is built on the new G.

Each inner problem is convex while W is frozen and nonnegative. The alternation is not claimed to converge to a global minimizer of a joint objective. The recorded objective is the alpha-weighted (here α = 1) objective of the last frozen W. It is not comparable to the control objective on a different W.
