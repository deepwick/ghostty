import shutil
import subprocess
from pathlib import Path

import pytest

from deepwick_spec.check_port import check_port
from deepwick_spec.palette import ANSI_KEYS, load_palette

REPO = Path(__file__).resolve().parents[1]
PALETTE = load_palette()
C = PALETTE.colors


requires_ghostty = pytest.mark.skipif(shutil.which("ghostty") is None, reason="requires ghostty")


def entries():
    path = REPO / "deepwick"
    assert path.is_file(), "theme file 'deepwick' missing"
    pairs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            key, _, value = line.partition("=")
            pairs.append((key.strip(), value.strip()))
    return pairs


EXPECTED = {
    "background": C["background"],
    "foreground": C["foreground"],
    "cursor-color": C["foreground"],
    "cursor-text": C["background"],
    "selection-background": C["selection"],
    "selection-foreground": C["foreground"],
    "split-divider-color": C["overlay"],
}


def test_colors():
    single = {k: v for k, v in entries() if k != "palette"}
    assert single == EXPECTED


def test_palette_entries():
    palette = [v for k, v in entries() if k == "palette"]
    assert palette == [f"{i}={PALETTE.ansi[key]}" for i, key in enumerate(ANSI_KEYS)]


def ghostty_env(tmp_path):
    config = tmp_path / "config" / "ghostty"
    (config / "themes").mkdir(parents=True)
    shutil.copy(REPO / "deepwick", config / "themes" / "deepwick")
    (config / "config").write_text("theme = deepwick\n")
    env = {"HOME": str(tmp_path / "home"), "PATH": "/usr/bin:/bin:" + str(Path(shutil.which("ghostty")).parent)}
    for kind in ("CONFIG", "DATA", "STATE", "CACHE"):
        env[f"XDG_{kind}_HOME"] = str(tmp_path / kind.lower())
    return env


@requires_ghostty
def test_ghostty_validates_config(tmp_path):
    result = subprocess.run(["ghostty", "+validate-config"], env=ghostty_env(tmp_path), capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@requires_ghostty
def test_ghostty_show_config_reflects_theme(tmp_path):
    out = subprocess.run(["ghostty", "+show-config"], env=ghostty_env(tmp_path), capture_output=True, text=True, check=True).stdout.lower()
    for key, value in EXPECTED.items():
        assert f"{key} = {value.lower()}" in out, key
    for i, key in enumerate(ANSI_KEYS):
        assert f"palette = {i}={PALETTE.ansi[key].lower()}" in out, key


def test_port_conventions():
    assert check_port(REPO, PALETTE.allowed_hex()) == []
