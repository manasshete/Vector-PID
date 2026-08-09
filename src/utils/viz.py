"""Reusable visualization helpers for scripts and tests."""
import math
import matplotlib.pyplot as plt
import numpy as np


def show_image(image: np.ndarray, title: str = "", figsize: tuple[int, int] = (12, 8)) -> None:
    """Display single image. Blocks until window closed in script mode."""
    plt.figure(figsize=figsize)
    cmap = "gray" if len(image.shape) == 2 else None
    plt.imshow(image, cmap=cmap)
    plt.title(title, fontsize=14)
    plt.axis("off")
    plt.tight_layout()
    plt.show(block=True)


def show_preprocessing_grid(stages: dict[str, np.ndarray], figsize: tuple[int, int] = (20, 12)) -> None:
    """Display all preprocessing stages in a labeled grid. Blocks in script mode."""
    keys = list(stages.keys())
    n = len(keys)
    cols = min(3, n)
    rows = math.ceil(n / cols)

    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    axes = np.atleast_2d(axes)

    for idx, key in enumerate(keys):
        r, c = divmod(idx, cols)
        ax = axes[r][c]
        ax.imshow(stages[key], cmap="gray")
        ax.set_title(key.replace("_", " ").title(), fontsize=12)
        ax.axis("off")

    for idx in range(n, rows * cols):
        r, c = divmod(idx, cols)
        axes[r][c].axis("off")

    plt.tight_layout()
    plt.show(block=True)