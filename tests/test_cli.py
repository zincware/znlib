"""Test the 'znlib' CLI."""
import pytest

import znlib.cli


@pytest.mark.parametrize("package", [("znlib", True), ("zn", False)])
def test_installed(capsys, package) -> None:
    """Test installed packages."""
    assert znlib.cli.ZnModules(package[0]).installed is package[1]
    captured = capsys.readouterr()
    if package[1]:
        assert "✓" in captured.out
    else:
        assert "✗" in captured.out
