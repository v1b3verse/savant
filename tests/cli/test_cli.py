"""Tests for savant_cli.cli using click CliRunner."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from savant_cli.cli import cli


class TestCLIDiscovery:
    def test_discover_no_hosts(self):
        runner = CliRunner()
        with patch("savant_cli.cli._discover_hosts", new_callable=AsyncMock, return_value=[]):
            result = runner.invoke(cli, ["discover", "--timeout", "0.1"])
            assert result.exit_code == 0
            assert "No Savant hosts found" in result.output


class TestCLIRequiresHost:
    def test_light_without_host(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["light", "Kitchen", "50"])
        assert result.exit_code != 0
        assert "host" in result.output.lower() or result.exit_code == 1


class TestCLIHelp:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Savant" in result.output

    def test_light_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["light", "--help"])
        assert result.exit_code == 0
        assert "ZONE" in result.output
        assert "LEVEL" in result.output

    def test_discover_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["discover", "--help"])
        assert result.exit_code == 0

    def test_zones_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["zones", "--help"])
        assert result.exit_code == 0
