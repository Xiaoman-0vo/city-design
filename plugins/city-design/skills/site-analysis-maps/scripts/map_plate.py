"""Transparent static grid plates; inputs must already share a display frame."""

from pathlib import Path
from typing import Any, Callable, Sequence
from numpy.typing import ArrayLike
import hashlib
import json
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, Normalize, BoundaryNorm
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
from PIL import Image

# Blue and red anchors from the selected Nature-style family. The narrower
# light transition keeps the colors legible after alpha blending.
VIVID_BLUE_RED = [
    (0, "#0F4D92"),
    (0.42, "#3775BA"),
    (0.5, "#F7F7F7"),
    (0.58, "#E53935"),
    (1, "#B64342"),
]
GREEN_COLORS = ["#eef5e8", "#c7e9b4", "#7fcdbb", "#41b6a6", "#238b65", "#005a32"]


def render_plate(
    values: ArrayLike,
    extent: Sequence[float],
    output: str | Path,
    label: str,
    vmin: float,
    vmax: float,
    buildings: Any = None,
    alpha: float = 0.74,
    crop: Sequence[float] | None = None,
    origin: str = "lower",
    basemap: ArrayLike | None = None,
    colors: Sequence[Any] | None = None,
    bins: Sequence[float] | None = None,
    ticks: Sequence[float] | None = None,
    alignment_validator: Callable[..., Any] | None = None,
    nodata_label: bool = True,
) -> dict[str, Any]:
    """Render saved values; alpha/crop/style never modify their numeric array."""
    extent = list(map(float, extent))
    crop = list(map(float, crop)) if crop is not None else None
    bins = list(map(float, bins)) if bins is not None else None
    values = np.asarray(values, dtype=float)
    if values.ndim != 2 or not np.isfinite(values).any():
        raise ValueError("A nonempty 2D grid is required")
    if not (0 < alpha <= 1 and vmin < vmax):
        raise ValueError("Invalid opacity or legend limits")
    if (
        len(extent) != 4
        or not np.isfinite(extent).all()
        or not (extent[0] < extent[1] and extent[2] < extent[3])
    ):
        raise ValueError("Extent order is xmin,xmax,ymin,ymax")
    if origin not in ["lower", "upper"]:
        raise ValueError("Unknown grid origin")
    if crop is not None and (
        len(crop) != 4
        or not np.isfinite(crop).all()
        or not (crop[0] < crop[1] and crop[2] < crop[3])
    ):
        raise ValueError("Invalid display crop")
    if bins is not None and colors is None:
        raise ValueError("Binned plates require explicit colors")
    before = hashlib.sha256(values.tobytes()).hexdigest()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    cmap = (
        ListedColormap(colors)
        if bins is not None
        else LinearSegmentedColormap.from_list(
            "blue_red", colors if colors is not None else VIVID_BLUE_RED
        )
    )
    cmap.set_bad((0, 0, 0, 0))
    if bins is not None:
        if not np.all(np.diff(bins) > 0):
            raise ValueError("Legend bins must increase")
        if len(bins) != len(colors) + 1:
            raise ValueError("One color per bin is required")
        norm = BoundaryNorm(bins, cmap.N)
    else:
        norm = Normalize(vmin, vmax)
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial Unicode MS", "Arial", "DejaVu Sans"],
            "font.size": 10,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "axes.unicode_minus": False,
        }
    )
    fig = plt.figure(figsize=(14, 12.5), facecolor="none")
    ax = fig.add_axes([0.012, 0.03, 0.838, 0.94], facecolor="none", label="map")
    if basemap is not None:
        ax.imshow(basemap, extent=extent, origin=origin, interpolation="bilinear", zorder=0)
    ax.imshow(
        np.ma.masked_invalid(values),
        extent=extent,
        origin=origin,
        cmap=cmap,
        norm=norm,
        alpha=alpha,
        interpolation="nearest",
        zorder=1,
    )
    if buildings is not None:
        buildings.plot(ax=ax, facecolor="white", edgecolor="#838b95", linewidth=0.25, zorder=3)
    box = crop or extent
    ax.set_xlim(box[:2])
    ax.set_ylim(box[2:])
    ax.set_aspect("equal")
    ax.set_axis_off()
    cax = fig.add_axes([0.885, 0.405, 0.018, 0.24], facecolor="none", label="<colorbar>")
    cb = fig.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap=cmap),
        cax=cax,
        ticks=ticks if ticks is not None else bins,
        alpha=alpha,
        spacing="uniform",
    )
    cb.ax.yaxis.set_major_formatter(
        FuncFormatter(lambda value, pos: f"{value:.1f}".rstrip("0").rstrip("."))
    )
    cb.ax.tick_params(labelsize=10, width=0.35, length=2.5, pad=5, colors="#344252")
    cb.outline.set_visible(False)
    fig.text(
        0.875, 0.678, label, fontsize=10, ha="left", va="bottom", color="#2e3c50", linespacing=1.6
    )
    if buildings is not None:
        fig.add_artist(
            Rectangle(
                (0.881, 0.347),
                0.022,
                0.012,
                transform=fig.transFigure,
                facecolor="white",
                edgecolor="#838b95",
                linewidth=0.5,
            )
        )
        fig.text(0.913, 0.353, "建筑", fontsize=9, ha="left", va="center", color="#344252")
    if nodata_label and np.isnan(values).any():
        fig.text(0.881, 0.313, "空缺：无数据", fontsize=8, ha="left", va="center", color="#667183")
    fig.canvas.draw()
    # A caller with an installed figure-audit skill can pass its real
    # render-time validator; the legend axis is labelled as a colorbar.
    require_matplotlib_panel_alignment = alignment_validator
    if require_matplotlib_panel_alignment is not None:
        require_matplotlib_panel_alignment(
            fig,
            json_out=str(output.with_suffix(".alignment.json")),
            overlay_svg=str(output.with_suffix(".alignment.svg")),
            strict=True,
        )
    fig.savefig(output, dpi=400, transparent=True)
    fig.savefig(output.with_suffix(".pdf"), transparent=True)
    fig.savefig(output.with_suffix(".svg"), transparent=True)
    plt.close(fig)
    with Image.open(output) as im:
        assert im.size == (5600, 5000) and im.mode == "RGBA" and im.getpixel((0, 0))[3] == 0
        preview = im.copy()
        preview.thumbnail((1400, 1250))
        preview.save(output.with_name(output.stem + "_preview.png"))
        white = Image.new("RGBA", preview.size, "white")
        white.alpha_composite(preview)
        white.convert("RGB").save(output.with_name(output.stem + "_white_check.png"))
    assert before == hashlib.sha256(values.tobytes()).hexdigest()
    record = {
        "file": output.name,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "grid_shape": list(values.shape),
        "extent": extent,
        "display_crop": box,
        "origin": origin,
        "alpha": alpha,
        "legend_limits": [vmin, vmax],
        "legend_bins": bins,
        "label": label,
        "numeric_values_unchanged": True,
        "finite_count": int(np.isfinite(values).sum()),
        "missing_count": int(np.isnan(values).sum()),
        "output_size": [5600, 5000],
        "plot_contract": "Single map plus compact legend; transparent canvas; no IDs; output resolution is not measurement resolution",
    }
    output.with_suffix(".json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return record
