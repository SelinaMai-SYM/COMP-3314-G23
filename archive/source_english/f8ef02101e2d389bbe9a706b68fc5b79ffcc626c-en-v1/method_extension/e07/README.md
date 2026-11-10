# E07 — clustering the same representation

E07 does not change F, W, or G. On the control embedding and the control shrunk patterns it compares:

1. random Lloyd, one restart per seed, seeds 0..49;
2. k-means++, one restart per seed, seeds 0..49;
3. the single random run with the smallest K-means inertia;
4. a consensus: align every random partition to that inertia-best partition and take the majority label, breaking ties toward the smallest id.

Inertia, not ACC, selects (3) and the reference for (4). The mean over seeds is not reported for (3) or (4); those cells have one assignment.
