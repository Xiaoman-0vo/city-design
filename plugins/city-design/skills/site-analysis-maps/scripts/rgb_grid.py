"""Exactly aggregate saved green/valid masks in their native image pixels."""

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image


def main() -> None:
    """Aggregate native masks and export numeric grids with source hashes."""
    p = argparse.ArgumentParser()
    p.add_argument("--valid-mask", type=Path, required=True)
    p.add_argument("--green-mask", type=Path, required=True)
    p.add_argument("--crop", type=int, nargs=4, required=True, metavar=("X0", "Y0", "X1", "Y1"))
    p.add_argument("--cells", type=int, default=30)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output = a.output.with_suffix(".npz")
    v = np.asarray(Image.open(a.valid_mask).convert("L")) > 0
    g = np.asarray(Image.open(a.green_mask).convert("L")) > 0
    if v.shape != g.shape:
        raise ValueError("Masks must share the same native frame and shape")
    x0, y0, x1, y1 = a.crop
    if not (0 <= x0 < x1 <= v.shape[1] and 0 <= y0 < y1 <= v.shape[0]):
        raise ValueError("Crop outside masks")
    v = v[y0:y1, x0:x1]
    g = g[y0:y1, x0:x1] & v
    if not (1 <= a.cells <= min(v.shape)):
        raise ValueError("Grid finer than native pixels")
    xe = np.round(np.linspace(0, v.shape[1], a.cells + 1)).astype(int)
    ye = np.round(np.linspace(0, v.shape[0], a.cells + 1)).astype(int)
    rows = []
    values = np.full((a.cells, a.cells), np.nan)
    for r in range(a.cells):
        for c in range(a.cells):
            sl = np.s_[ye[r] : ye[r + 1], xe[c] : xe[c + 1]]
            den = int(v[sl].sum())
            num = int(g[sl].sum())
            value = 100 * num / den if den else np.nan
            values[r, c] = value
            rows.append(
                dict(
                    row=r,
                    col=c,
                    green_pixels=num,
                    valid_pixels=den,
                    green_percent=value,
                    x0=x0 + int(xe[c]),
                    y0=y0 + int(ye[r]),
                    x1=x0 + int(xe[c + 1]),
                    y1=y0 + int(ye[r + 1]),
                )
            )
    assert (
        sum(x["valid_pixels"] for x in rows) == v.sum()
        and sum(x["green_pixels"] for x in rows) == g.sum()
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(a.output.with_suffix(".csv"), index=False, encoding="utf-8-sig")
    np.savez_compressed(a.output, values=values, xedges=xe, yedges=ye)
    receipt = {
        "crop_xyxy": a.crop,
        "cells": a.cells,
        "valid_pixels": int(v.sum()),
        "green_pixels": int(g.sum()),
        "green_percent": float(100 * g.sum() / v.sum()) if v.any() else None,
        "hashes": {
            k: hashlib.sha256(q.read_bytes()).hexdigest()
            for k, q in [("valid", a.valid_mask), ("green", a.green_mask)]
        },
    }
    a.output.with_suffix(".json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
