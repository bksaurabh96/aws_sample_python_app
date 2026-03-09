"""
Tests for the CDK stack. Run from the repo root with:
  pytest infra/tests/ -v
or from infra/ with:
  cd infra && pytest tests/ -v

Requires: Docker (for image asset), CDK CLI (npm install -g aws-cdk), and infra deps installed.
"""
import subprocess
from pathlib import Path

import pytest

# Project root (parent of infra/)
INFRA_DIR = Path(__file__).resolve().parent.parent


def test_cdk_synth_succeeds():
    """Run 'cdk synth' from infra/ to validate the stack synthesizes."""
    result = subprocess.run(
        ["cdk", "synth", "--quiet"],
        cwd=str(INFRA_DIR),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        f"cdk synth failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "AwsSamplePythonAppStack" in result.stdout or "Resources" in result.stdout
