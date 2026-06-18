from __future__ import annotations

from importlib.metadata import version

import pytest

import service_ontology_lite as sol
from service_ontology_lite import cli
from service_ontology_lite.mcp_server import SERVER_INFO


def test_package_version_matches_installed_metadata():
    assert sol.__version__ == version("service-ontology-lite")
    assert SERVER_INFO["version"] == sol.__version__
    assert "__version__" in sol.__all__


@pytest.mark.parametrize("flag", ["--version", "-V"])
def test_cli_version_prints_package_version(flag: str, capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exc_info:
        cli.main([flag])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"service-ontology {sol.__version__}"
