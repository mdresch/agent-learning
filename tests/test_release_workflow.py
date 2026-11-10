"""Release workflow contract tests."""

from pathlib import Path


def test_release_job_uses_flattened_linux_artifact_path() -> None:
    workflow = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "publish.yaml"
    ).read_text(encoding="utf-8")

    expected = 'release-assets/agent-learning-cli-${VERSION}-linux-x64.tar.gz'
    obsolete = (
        'release-assets/dist-installer/'
        'agent-learning-cli-${VERSION}-linux-x64.tar.gz'
    )
    assert expected in workflow
    assert obsolete not in workflow


def test_release_job_uses_flattened_windows_artifact_paths() -> None:
    workflow = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "publish.yaml"
    ).read_text(encoding="utf-8")

    for suffix in ("exe", "zip"):
        filename = f"agent-learning-cli-${{VERSION}}-windows-x64.{suffix}"
        assert f'release-assets/{filename}' in workflow
        assert f'release-assets/dist-installer/{filename}' not in workflow


def test_windows_installer_uses_directory_bundle_and_precedes_old_shims() -> None:
    root = Path(__file__).resolve().parents[1]
    build_script = (root / "scripts" / "build_windows_installer.ps1").read_text(
        encoding="utf-8"
    )
    installer = (
        root / "packaging" / "windows" / "agent-learning-installer.iss"
    ).read_text(encoding="utf-8")

    assert "--onedir" in build_script
    assert "--onefile" not in build_script
    assert "$env:LOCALAPPDATA" in build_script
    assert 'Source: "dist\\agent-learn\\*"' in installer
    assert "recursesubdirs" in installer
    assert "PrivilegesRequired=lowest" in installer
    assert 'ValueData: "{code:PathWithEntryFirst|{app}}"' in installer
    assert 'ValueData: "{olddata};{app}"' not in installer

def _publish_workflow() -> str:
    return (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "publish.yaml").read_text(
        encoding="utf-8"
    ).replace("\r\n", "\n")


def test_a_push_without_a_version_bump_skips_the_release_instead_of_failing() -> None:
    """IMP-052: the already-tagged guard writes release=false and exits 0 on a push."""
    workflow = _publish_workflow()
    guard = workflow.split("name: Reject a version already tagged at another commit", 1)[1].split("\n  build:", 1)[0]

    # The push branch is closed by the `fi` indented 12 spaces; the first `fi` of the step belongs to another check.
    push_branch, after_push = guard.split('if [[ "$GITHUB_EVENT_NAME" == "push" ]]; then', 1)[1].split("\n            fi\n", 1)
    assert 'echo "release=false" >> "$GITHUB_OUTPUT"' in push_branch
    assert "exit 0" in push_branch
    assert "exit 1" not in push_branch
    # A manual publish of an already tagged version still fails.
    assert "::error::" in after_push and "exit 1" in after_push
    assert "      release: ${{ steps.existing-tag.outputs.release }}" in workflow


def test_the_release_jobs_wait_on_the_release_output() -> None:
    workflow = _publish_workflow()
    gate = "needs.release-metadata.outputs.release != 'false'"
    for job in ("build", "build-windows", "build-linux"):
        body = workflow.split(f"\n  {job}:\n", 1)[1].split("\n\n  ", 1)[0]
        assert gate in body, f"{job} does not check the release output"
