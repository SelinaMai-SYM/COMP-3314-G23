"""Score-independent sample catalogues for retrospective SSC reconstruction.

Class labels are used only to implement declared sampling quotas. All fitting
operates on the returned features, without access to this catalogue's labels.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from functools import lru_cache
from pathlib import Path

import numpy as np

from benchmarks import load_dataset
from benchmarks.data_paths import resolve_data_root
from experiments.v3_reproduction.provenance import fingerprint_matrix, sha256_array

REPO = Path(__file__).resolve().parents[2]
PARENTS = {
    "AR_LZUFE1680": ("AR", "ar/data", "lzuf_superset1680"),
    "UMIST_LZUFE574": ("UMIST", "umist/data", "lzuf574"),
    "UMIST_Wayback575": ("UMIST", "umist/data", "precropped575"),
    "UMIST_Wayback_dedup565": ("UMIST", "umist/data", "derived_wayback_dedup565"),
    "UMIST_Roweis575": ("UMIST", "umist/data", "roweis575"),
    "UMIST_Figshare575": ("UMIST", "umist/data", "figshare575"),
    "UMIST_Zenodo575_28x23": ("UMIST", "umist/data", "zenodo3634017"),
    "BinAlpha_parent36": ("BinAlpha", "binalpha/data", "binaryalphadigs36"),
    "YaleB_dengcai32": ("YaleB", "yaleb/data", "dengcai32"),
    "YaleB_cropped2414": ("YaleB", "yaleb/data", "cropped2414"),
    "YaleB_cropped2414_nearest": ("YaleB", "yaleb/data", "cropped2414_nearest"),
    "YaleB_cropped2414_bicubic": ("YaleB", "yaleb/data", "cropped2414_bicubic"),
    "USPS": ("USPS", "usps/data", "libsvm"),
    "MSRA25_EBSA_16x16": ("MSRA25_EBSA_16x16", "msra50/data", "ebsa16"),
    "ORL_att92": ("ORL", "orl/data", "att92"),
    "JAFFE": ("JAFFE", "jaffe/data", "zenodo"),
}


@lru_cache(maxsize=16)
def load_parent(parent_id, data_root):
    """Resolve every source through the same independent benchmark root."""
    name, folder, version = PARENTS[parent_id]
    if version == "derived_wayback_dedup565":
        X, y, meta = load_parent("UMIST_Wayback575", data_root)
        retained, mapping = exact_deduplicate(X, y)
        return X[retained], y[retained], {**meta, "version": version, "n": len(retained),
            "original_parent_id": "UMIST_Wayback575", "original_row_indices": retained.tolist(),
            "construction": "first occurrence of exact duplicate pixels in canonical source order"}
    return load_dataset(name, root=Path(data_root) / folder, version=version)


def exact_deduplicate(X, y):
    """First occurrence in source order, with a complete inverse row map."""
    _, first, inverse = np.unique(X, axis=0, return_index=True, return_inverse=True)
    retained = np.sort(first)
    group_to_retained = np.empty(len(first), dtype=np.int64)
    group_to_retained[inverse[retained]] = np.arange(len(retained))
    mapping = group_to_retained[inverse]
    for k, original in enumerate(retained):
        if np.any(y[mapping == k] != y[original]):
            raise ValueError("exact duplicate rows have conflicting class labels")
    return retained, mapping


def proportional_quotas(y, total):
    classes, counts = np.unique(y, return_counts=True)
    if total < len(classes) or total > len(y):
        raise ValueError("infeasible stratified quota")
    real = total * counts / len(y)
    quotas = np.floor(real).astype(int)
    order = sorted(range(len(classes)), key=lambda i: (-(real[i]-quotas[i]), int(classes[i])))
    for i in order[:total-int(quotas.sum())]:
        quotas[i] += 1
    if np.any(quotas == 0):
        raise ValueError("proportional quota loses a class")
    return dict(zip(map(int, classes), map(int, quotas)))


def draw_by_class(y, quotas, seed):
    rng = np.random.RandomState(seed)
    return np.concatenate([np.sort(rng.choice(np.flatnonzero(y == k), size=quotas[int(k)], replace=False))
                           for k in np.unique(y)]).astype(np.int64)


def prepare(X, factor):
    if factor not in {"Y0", "Y1", "Y2", "Y3"}:
        raise ValueError(f"unknown preprocessing factor {factor}")
    if factor in {"Y1", "Y3"}:
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        return X / np.maximum(norms, 1e-12)
    return X


def _manifest(candidate):
    if "selected_indices" in candidate:
        return candidate
    path = Path(candidate["manifest_path"])
    if not path.is_absolute():
        path = REPO / path
    data = json.loads(path.read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != candidate["manifest_sha256"]:
        raise ValueError("sample manifest hash mismatch")
    return data


def materialize(candidate, data_root, *, verify=True):
    """Replay exact indices; rebuild A/F/W/G downstream for every changed input.

    Y2/Y3 also request row normalization of the resulting spectral embedding;
    that explicit factor is returned as metadata rather than applied to X here.
    """
    manifest = _manifest(candidate)
    resolved_root = resolve_data_root(data_root)
    if verify:
        for source in manifest.get("source_files", []):
            path = resolved_root / source["path_relative_to_data_root"]
            if not path.is_file() or hashlib.file_digest(path.open("rb"), "sha256").hexdigest() != source["sha256"]:
                raise ValueError(f"candidate source hash mismatch: {path}")
    X, y, meta = load_parent(manifest["parent_id"], str(resolved_root))
    ids = np.asarray(manifest["selected_indices"], dtype=np.int64)
    if ids.ndim != 1 or len(ids) != len(np.unique(ids)) or np.any(ids < 0) or np.any(ids >= len(X)):
        raise ValueError("invalid sample indices")
    X = prepare(X[ids], manifest.get("preprocessing", "Y0"))
    y = y[ids]
    # BinAlpha parent codes are 10..35 for letters; use contiguous local IDs.
    _, y = np.unique(y, return_inverse=True)
    if verify and fingerprint_matrix(X, y) != manifest["fingerprint"]:
        raise ValueError("candidate replay fingerprint mismatch")
    return X, y, {**meta, "candidate_id": manifest["candidate_id"],
                  "parent_id": manifest["parent_id"], "selected_indices": ids.tolist(),
                  "preprocessing": manifest.get("preprocessing", "Y0"),
                  "embedding_row_normalization": manifest.get("preprocessing", "Y0") in {"Y2", "Y3"},
                  "historical_identity": "unverified", "pool": manifest["pool"],
                  "fingerprint": manifest["fingerprint"]}


def build_catalogue(data_root, output=Path("results/subset_search")):
    data_root = resolve_data_root(data_root)
    output = Path(output)
    if not output.is_absolute():
        output = REPO / output
    output.mkdir(parents=True, exist_ok=True)
    manifests = output / "sample_manifests"
    manifests.mkdir(exist_ok=True)
    source_rows, parents, candidates, identity = [], {}, [], {}

    for pid, (benchmark, folder, version) in PARENTS.items():
        try:
            X, y, meta = load_parent(pid, str(data_root))
        except (OSError, ValueError) as exc:
            parents[pid] = {"status": "UNAVAILABLE", "reason": repr(exc)}
            continue
        paths = meta.get("archive_paths", [meta.get("archive_path")])
        files = [{"path_relative_to_data_root": str(Path(p).relative_to(data_root)),
                  "sha256": hashlib.file_digest(Path(p).open("rb"), "sha256").hexdigest(),
                  "bytes": Path(p).stat().st_size} for p in paths if p and Path(p).is_file()]
        parent = {"parent_id": pid, "benchmark": benchmark, "version": version,
                  "status": "AVAILABLE", "source_url": meta.get("source_url"), "source_files": files,
                  "n": len(X), "p": X.shape[1], "classes": len(np.unique(y)),
                  "source_order": "loader's canonical source order; zero-based row indices",
                  "original_parent_id": meta.get("original_parent_id", pid),
                  "original_row_indices": meta.get("original_row_indices", list(range(len(X)))),
                  "sample_ids": [f"{pid}:row:{i}" for i in range(len(X))],
                  "fingerprint": fingerprint_matrix(X, y),
                  "class_counts": {str(int(k)): int(n) for k,n in zip(*np.unique(y, return_counts=True))}}
        if "UMIST" in pid or "MSRA" in pid:
            keep, mapping = exact_deduplicate(X, y)
            parent.update(unique_rows=len(keep), duplicate_extra_rows=len(X)-len(keep),
                          dedup_retained_original_indices=keep.tolist(), original_to_retained_row=mapping.tolist())
        parents[pid] = parent
        source_rows.append({"parent_id": pid, "benchmark": benchmark, "n": len(X), "p": X.shape[1],
                            "classes": len(np.unique(y)), "native_resolution": meta.get("original_spatial_size", meta.get("processed_spatial_size")),
                            "source_url": meta.get("source_url"), "source_sha256": ";".join(f["sha256"] for f in files),
                            "historical_identity": "unverified", "unique_rows": parent.get("unique_rows", "not audited"),
                            "source_alias_of": "UMIST_Roweis575" if pid == "UMIST_Figshare575" else ""})

    def add(pid, cid, family, ids, pool="specification_compatible", seed=None, prep="Y0", deviations=None, **extra):
        if parents.get(pid, {}).get("status") != "AVAILABLE":
            return
        X, y, meta = load_parent(pid, str(data_root))
        ids = np.asarray(ids, dtype=np.int64)
        if len(np.unique(ids)) != len(ids):
            raise ValueError(f"repeated selected row in {cid}")
        sample = prepare(X[ids], prep)
        _, labels = np.unique(y[ids], return_inverse=True)
        fp = fingerprint_matrix(sample, labels)
        key = (fp["x_sha256"], fp["y_sha256"], prep)
        alias = identity.get(key)
        identity.setdefault(key, cid)
        manifest = {"candidate_id": cid, "parent_id": pid, "family": family,
                    "benchmark": "MSRA50" if pid == "MSRA25_EBSA_16x16" else PARENTS[pid][0],
                    "pool": pool, "historical_identity": "unverified", "index_convention": "zero-based parent row index",
                    "selected_indices": ids.tolist(), "original_parent_id": parents[pid]["original_parent_id"],
                    "original_row_indices": [parents[pid]["original_row_indices"][i] for i in ids], "excluded_indices": np.setdiff1d(np.arange(len(X)), ids).tolist(),
                    "excluded_reason": "not selected by the predeclared rule", "final_order": "selected indices in the declared canonical class/source order",
                    "preprocessing": prep, "prep": prep, "embedding_row_normalization": prep in {"Y2", "Y3"}, "subset_seed": seed, "rng": "numpy.random.RandomState" if seed is not None else None,
                    "n": len(ids), "p": X.shape[1], "classes": len(np.unique(labels)),
                    "class_counts": {str(int(k)): int(n) for k,n in zip(*np.unique(labels, return_counts=True))},
                    "fingerprint": fp, "source_files": parents[pid]["source_files"],
                    "source_url": parents[pid]["source_url"], "specification_deviations": deviations or [],
                    "aliases": [alias] if alias else [], **extra}
        p = manifests / (cid + ".json")
        p.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")
        try: rel = str(p.relative_to(REPO))
        except ValueError: rel = str(p)
        candidates.append({k:v for k,v in manifest.items() if k not in {"selected_indices","excluded_indices","source_files"}} |
                          {"manifest_path": rel, "manifest_sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "alias_of": alias,
                           "execution_status": "CATALOGUED_NOT_SCHEDULED"})

    pid = "AR_LZUFE1680"
    X, y, _ = load_parent(pid, str(data_root))
    groups = [np.flatnonzero(y == k) for k in np.unique(y)]
    assert len(groups) == 120 and all(len(g) == 14 for g in groups)
    for name, positions in [("first7", range(7)), ("last7", range(7,14)), ("even7", range(0,14,2)), ("odd7", range(1,14,2))]:
        add(pid, "AR_"+name, "AR_fixed7", np.concatenate([g[list(positions)] for g in groups]), construction_rule="index-order hypothesis; no session metadata")
    for seed in range(100):
        add(pid, f"AR_random_seed{seed:03d}", "AR_random7", draw_by_class(y, {int(k):7 for k in np.unique(y)}, seed), seed=seed)
    for i, mask in enumerate(itertools.combinations(range(14), 7)):
        add(pid, f"AR_common_mask{i:04d}", "AR_common_mask", np.concatenate([g[list(mask)] for g in groups]),
            common_positions=list(mask), construction_rule="common seven-of-fourteen index-order hypothesis; position alignment unverified")
    add(pid, "AR_parent1680", "AR_parent", np.arange(len(X)), "diagnostic", deviations=["1680 samples instead of 840"])

    for pid in [p for p in PARENTS if p.startswith("UMIST_")]:
        if parents.get(pid, {}).get("status") != "AVAILABLE":
            continue
        X, y, _ = load_parent(pid, str(data_root))
        add(pid, pid+"_parent", "UMIST_parent", np.arange(len(X)), "diagnostic", deviations=[f"{len(X)} samples instead of 564"])
        keep, mapping = exact_deduplicate(X, y)
        if pid == "UMIST_LZUFE574":
            assert len(keep) == 564 and len(np.unique(y[keep])) == 20
            add(pid, "UMIST_LZUFE574_exact_dedup564", "UMIST_exact_dedup564", keep,
                construction_rule="first occurrence of each exact pixel row; label-consistent duplicates", original_to_retained_row=mapping.tolist())
        if pid == "UMIST_Wayback575":
            assert len(keep) == 565
            add(pid, "UMIST_Wayback_exact_dedup565", "UMIST_dedup565", keep, "diagnostic", deviations=["565 samples instead of 564"], original_to_retained_row=mapping.tolist())
            for omitted in range(len(keep)):
                selected = np.delete(keep, omitted)
                if len(np.unique(y[selected])) == 20:
                    add(pid, f"UMIST_Wayback_omit{omitted:03d}", "UMIST_single_omission", selected,
                        construction_rule="deduplicated565 plus one unknown omission", omitted_original_row=int(keep[omitted]))
        # Figshare is an alias, not an independent source family.
        if pid == "UMIST_Figshare575":
            continue
        if len(X) > 564:
            quotas = proportional_quotas(y, 564)
            for seed in range(100):
                add(pid, f"{pid}_stratified_seed{seed:03d}", pid+"_stratified564", draw_by_class(y, quotas, seed), seed=seed,
                    quotas={str(k):v for k,v in quotas.items()}, construction_rule="proportional quota with largest remainder, stable class-ID ties")

    pid = "BinAlpha_parent36"
    X, y, _ = load_parent(pid, str(data_root))
    letters = np.flatnonzero(y >= 10)
    letter_y = y[letters]
    old = json.loads((REPO/"benchmarks/binalpha/reconstructions/letters26x30_seed0.json").read_text())
    expected = np.array([item["class_index_in_parent"]*39+i for item in old["selection"] for i in item["example_indices_0based"]])
    for seed in range(100):
        ids = letters[draw_by_class(letter_y, {int(k):30 for k in np.unique(letter_y)}, seed)]
        if seed == 0 and not np.array_equal(ids, expected):
            raise ValueError("BinAlpha seed0 does not replay the unchanged historical manifest")
        add(pid, f"BinAlpha_random_seed{seed:03d}", "BinAlpha_random30", ids, seed=seed,
            previously_examined=seed == 0, seed0_compatibility="exact" if seed == 0 else None)
    for name, positions in [("first30", range(30)), ("last30", range(9,39))]:
        ids = np.concatenate([np.flatnonzero(y == k)[list(positions)] for k in range(10,36)])
        add(pid, "BinAlpha_"+name, "BinAlpha_order_sensitivity", ids, "adapted", deviations=["deterministic ordering instead of random selection"])
    add(pid, "BinAlpha_letters1014", "BinAlpha_parent", letters, "diagnostic", deviations=["39 instead of 30 samples per letter"])
    add(pid, "BinAlpha_all36_1404", "BinAlpha_parent", np.arange(len(X)), "diagnostic", deviations=["36 classes instead of 26; 39 instead of 30 samples per class"])

    for pid in ["YaleB_dengcai32", "YaleB_cropped2414", "YaleB_cropped2414_nearest", "YaleB_cropped2414_bicubic"]:
        X, _, _ = load_parent(pid, str(data_root))
        for prep in ["Y0", "Y1", "Y2", "Y3"]:
            add(pid, f"{pid}_{prep}", "YaleB_source_preparation", np.arange(len(X)), prep=prep,
                construction_rule="full membership; source/resize and normalization factors kept separate", previously_examined=True)
    for pid in ["ORL_att92", "JAFFE", "USPS", "MSRA25_EBSA_16x16"]:
        X, _, _ = load_parent(pid, str(data_root))
        is_msra = pid.startswith("MSRA")
        add(pid, pid, "fixed_membership", np.arange(len(X)), "adapted" if is_msra else "specification_compatible",
            deviations=["native 16x16 instead of the stated 32x32"] if is_msra else [], previously_examined=not is_msra)
    for split, ids in [("train7291", np.arange(7291)), ("test2007", np.arange(7291,9298))]:
        add("USPS", "USPS_"+split, "USPS_split", ids, "diagnostic", deviations=["sample count differs from 9298"])

    catalogue = {"schema": "ssc-candidate-catalogue-v1", "frozen_before_scoring": True,
                 "index_convention": "zero based", "selection_does_not_prove_historical_identity": True,
                 "parents": parents, "candidates": candidates,
                 "intended_candidate_count": len(candidates), "unique_physical_inputs": len(identity),
                 "finite_family_order": "lexicographic common masks; omission original row order; executable prefix from fixed permutation seed 20261110",
                 "random_family_order": "prefix of seeds 0..99, cohort chosen only from 10/32/100 before scores"}
    (output/"candidate_catalogue.json").write_text(json.dumps(catalogue, indent=2, sort_keys=True)+"\n")
    with (output/"source_inventory.csv").open("w", newline="") as f:
        writer=csv.DictWriter(f, fieldnames=list(source_rows[0]));writer.writeheader();writer.writerows(source_rows)
    config = REPO/"configs/subset_search/candidate_catalogue.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps({"schema":catalogue["schema"],"frozen_before_scoring":True,
                                 "catalogue_path":str((output/"candidate_catalogue.json").relative_to(REPO)),
                                 "catalogue_sha256":hashlib.sha256((output/"candidate_catalogue.json").read_bytes()).hexdigest(),
                                 "intended_candidate_count":len(candidates),"unique_physical_inputs":len(identity)},indent=2)+"\n")
    return catalogue


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--output", type=Path, default=Path("results/subset_search"))
    args=parser.parse_args()
    catalogue=build_catalogue(args.data_root,args.output)
    print(json.dumps({"intended":catalogue["intended_candidate_count"],"unique":catalogue["unique_physical_inputs"]}))

if __name__ == "__main__":
    main()
