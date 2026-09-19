"""
Variant-separation check for Gate 0.

Measures whether the three life stages stay as distinct from each other after generative
refinement as they were in the conventional render. Collapse toward one face is the
"beautifier" failure (design doc §13.1).

Usage:
    python identity_distance.py --conventional C_young/ C_middle/ C_old/ \
                                --generative  G_young/ G_middle/ G_old/

Each directory holds face-closest frames (PNG) for one stage (use extract_frames.sh with the
3 face-closest frame numbers). The script embeds every frame, averages per stage, then compares:

    sep_conv = mean pairwise distance between the three conventional stage embeddings
    sep_gen  = mean pairwise distance between the three generative stage embeddings
    ratio    = sep_gen / sep_conv           (1.0 = separation fully preserved)

    ident[stage] = distance(conv[stage], gen[stage])   (should be small: same person)

Pass (initial threshold, design doc §13.1): ratio >= 0.7 AND every ident[stage] < the smallest
cross-stage distance in the generative set (i.e. each generative stage is closer to its own
conventional source than to any other generative stage).

Requires: insightface, onnxruntime, numpy, opencv-python
    pip install insightface onnxruntime numpy opencv-python
"""
import argparse, itertools, sys
from pathlib import Path

import numpy as np


def load_model():
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app


def embed_dir(app, d: Path) -> np.ndarray:
    import cv2
    embs = []
    for p in sorted(d.glob("*.png")):
        img = cv2.imread(str(p))
        faces = app.get(img)
        if not faces:
            print(f"  no face found in {p.name}", file=sys.stderr)
            continue
        f = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        embs.append(f.normed_embedding)
    if not embs:
        sys.exit(f"no faces in {d}")
    return np.mean(embs, axis=0)


def dist(a, b):
    return float(1.0 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conventional", nargs=3, required=True, metavar=("YOUNG", "MIDDLE", "OLD"))
    ap.add_argument("--generative", nargs=3, required=True, metavar=("YOUNG", "MIDDLE", "OLD"))
    ap.add_argument("--min-ratio", type=float, default=0.7)
    a = ap.parse_args()
    stages = ["young", "middle", "old"]

    app = load_model()
    conv = {s: embed_dir(app, Path(d)) for s, d in zip(stages, a.conventional)}
    gen = {s: embed_dir(app, Path(d)) for s, d in zip(stages, a.generative)}

    pairs = list(itertools.combinations(stages, 2))
    sep_conv = np.mean([dist(conv[x], conv[y]) for x, y in pairs])
    sep_gen = np.mean([dist(gen[x], gen[y]) for x, y in pairs])
    ratio = sep_gen / sep_conv if sep_conv > 0 else float("nan")
    min_cross_gen = min(dist(gen[x], gen[y]) for x, y in pairs)

    print(f"cross-stage separation  conventional={sep_conv:.4f}  generative={sep_gen:.4f}  ratio={ratio:.3f}")
    ok = ratio >= a.min_ratio
    for s in stages:
        d = dist(conv[s], gen[s])
        same = d < min_cross_gen
        ok &= same
        print(f"identity {s:6s}  conv→gen distance={d:.4f}  {'OK' if same else 'FAIL (closer to another stage than to itself)'}")
    print("\nVARIANT SEPARATION:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
