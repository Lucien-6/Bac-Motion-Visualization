"""
Natural sorting utilities.

Provides natural sorting for file paths and strings containing numbers.
"""

from pathlib import Path
from natsort import natsorted, ns


def natural_sort_paths(paths: list[str | Path]) -> list[Path]:
    """
    Sort file paths using natural sorting algorithm.

    Natural sorting handles numeric sequences properly:
    - ['img1.png', 'img10.png', 'img2.png'] -> ['img1.png', 'img2.png', 'img10.png']

    Args:
        paths: List of file paths (strings or Path objects).

    Returns:
        Naturally sorted list of Path objects.
    """
    path_objects = [Path(p) for p in paths]
    sorted_paths = natsorted(path_objects, key=lambda x: x.name, alg=ns.PATH)
    return sorted_paths


def natural_sort_strings(strings: list[str]) -> list[str]:
    """
    Sort strings using natural sorting algorithm.

    Args:
        strings: List of strings to sort.

    Returns:
        Naturally sorted list of strings.
    """
    return natsorted(strings, alg=ns.IGNORECASE)
