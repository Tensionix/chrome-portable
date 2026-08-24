from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pytest

from system_core.core.jobs import JobContext
from system_core.core.manifest import Operation
from system_core.core.paths import ensure_project_dirs, get_project_paths
from system_core.services import chrome_portable_service as service


UTF16_INI = (
    "; Chrome++ configuration\n"
    "[general]\n"
    "data_dir=%app%\\..\\Data\n"
    "cache_dir=%app%\\..\\Cache\n"
    "command_line=\n"
    "launch_on_startup=\n"
    "launch_on_exit=\n"
    "[tabs]\n"
    "double_click_close=1\n"
)


def _context(tmp_path: Path, **parameters: object) -> JobContext:
    paths = get_project_paths(tmp_path)
    ensure_project_dirs(paths)
    return JobContext(
        paths=paths,
        operation=Operation(
            id="test",
            title="Test",
            description="",
            service="system_core.services.chrome_portable_service:build_portable",
            parameters=dict(parameters),
        ),
        log_file=paths.logs / "test.log",
        report_dir=paths.report,
    )


def _build_with_ini(tmp_path: Path, encoding: str = "utf-16-le", bom: bytes = b"\xff\xfe") -> Path:
    build = tmp_path / service.PORTABLE_NAME
    (build / "App").mkdir(parents=True)
    (build / "App" / "chrome++.ini").write_bytes(bom + UTF16_INI.encode(encoding))
    return build


def test_configure_ini_keeps_the_utf16_file_readable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Chrome++ ships the ini as UTF-16 LE; rewriting it as UTF-8 kills it silently."""
    build = _build_with_ini(tmp_path)
    # The wipe only stands where Chrome is not installed; this machine is not
    # the subject of the test.
    monkeypatch.setattr(service, "installed_browser_path", lambda: "")

    service._configure_chrome_plus_ini(_context(tmp_path), build, wipe_registry=True)

    raw = (build / "App" / "chrome++.ini").read_bytes()
    assert raw.startswith(b"\xff\xfe")
    text = raw[2:].decode("utf-16-le")
    assert f'launch_on_exit=reg delete "{service.CHROME_REGISTRY_BRANCH}" /f;' in text
    assert "data_dir=%app%\\..\\Data" in text
    assert "double_click_close=1" in text


def test_configure_ini_leaves_the_hook_empty_by_default(tmp_path: Path) -> None:
    """The Chrome branch is shared with an installed Chrome, so the wipe is opt-in."""
    build = _build_with_ini(tmp_path)

    service._configure_chrome_plus_ini(_context(tmp_path), build, wipe_registry=False)

    text = (build / "App" / "chrome++.ini").read_bytes()[2:].decode("utf-16-le")
    assert "launch_on_exit=\n" in text
    assert "reg delete" not in text


def test_a_release_tag_and_its_file_version_are_the_same_release() -> None:
    assert service.same_version("1.18.2", "1.18.2.0")
    assert service.same_version("151.0.7922.138", "151.0.7922.138")
    assert not service.same_version("151.0.7922.138", "151.0.7922.140")
    assert not service.same_version("1.18.2", "")


def test_build_versions_falls_back_to_the_version_folder(tmp_path: Path) -> None:
    build = tmp_path / service.PORTABLE_NAME
    (build / "App" / "151.0.7922.138").mkdir(parents=True)
    (build / "App" / "150.0.7500.100").mkdir(parents=True)

    assert service.build_versions(build).chrome == "151.0.7922.138"


def test_certificate_wrappers_install_for_the_user_and_remove_by_thumbprint(tmp_path: Path) -> None:
    """Trusting a CA must be reversible, and precise about what it takes back."""
    target = tmp_path / "Certificates"
    target.mkdir()

    written = service._write_certificate_wrappers(_context(tmp_path), target)

    install = (target / "Install-Russian-Trusted-CA.cmd").read_text(encoding="utf-8")
    remove = (target / "Uninstall-Russian-Trusted-CA.cmd").read_text(encoding="utf-8")
    assert [path.name for path in written] == [
        "Install-Russian-Trusted-CA.cmd",
        "Uninstall-Russian-Trusted-CA.cmd",
    ]
    # The user's store, never the machine's: no elevation, no other accounts.
    assert "-addstore -user" in install
    assert "-addstore -enterprise" not in install
    assert 'certutil -addstore -user -f "Root" "%~dp0russian_trusted_root_ca.crt"' in install
    assert 'certutil -addstore -user -f "CA" "%~dp0russian_trusted_sub_ca.crt"' in install
    for item in service.RUSSIAN_TRUSTED_CERTIFICATES:
        assert str(item["thumbprint"]) in remove
    assert "-delstore -user" in remove


def test_certificate_wrappers_are_crlf_utf8_without_bom(tmp_path: Path) -> None:
    """They are .cmd files, and this fleet's .cmd rule is UTF-8 without BOM, CRLF."""
    target = tmp_path / "Certificates"
    target.mkdir()

    service._write_certificate_wrappers(_context(tmp_path), target)

    raw = (target / "Install-Russian-Trusted-CA.cmd").read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" in raw
    assert raw.count(b"\n") == raw.count(b"\r\n")


def test_certificates_state_reads_both_stores(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, str]] = []

    def fake_present(thumbprint: str, store: str) -> bool:
        seen.append((thumbprint, store))
        return store == "Root"

    monkeypatch.setattr(service, "_certificate_present", fake_present)

    state = service.certificates_state(_context(tmp_path))

    assert seen == [
        ("8FF915CCAB7BC16F8C5C8099D53E0E115B3AEC2F", "Root"),
        ("335D43F53451B781535FF3882DF713D3C14F8A01", "CA"),
    ]
    assert state["certificates"] == {"Russian Trusted Root CA": True, "Russian Trusted Sub CA": False}


def test_github_assets_fall_back_to_the_release_page(monkeypatch: pytest.MonkeyPatch) -> None:
    """The API allows 60 anonymous calls an hour; the pages have no quota at all."""
    page = (
        '<a href="/Bush2021/chrome_plus/releases/download/1.18.2/Chrome%2B%2B_v1.18.2_x86_x64_arm64.7z">'
        "</a>"
    )

    class _Response:
        def __init__(self, url: str, body: bytes) -> None:
            self._url = url
            self._body = body

        def geturl(self) -> str:
            return self._url

        def read(self) -> bytes:
            return self._body

    @contextmanager
    def fake_urlopen(request, timeout=0):  # noqa: ANN001 - mirrors urlopen's shape
        url = request.full_url
        if "api.github.com" in url:
            raise RuntimeError("rate limit exceeded")
        if url.endswith("/releases/latest"):
            yield _Response("https://github.com/Bush2021/chrome_plus/releases/tag/1.18.2", b"")
            return
        yield _Response(url, page.encode("utf-8"))

    monkeypatch.setattr(service, "urlopen", fake_urlopen)

    tag, assets = service.github_latest_assets(service.CHROME_PLUS_REPO)

    assert tag == "1.18.2"
    assert assets[0][0] == "Chrome%2B%2B_v1.18.2_x86_x64_arm64.7z"


def test_published_chrome_version_is_read_from_the_api(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Response:
        def read(self) -> bytes:
            return b'{"versions": [{"version": "151.0.7922.138"}]}'

    @contextmanager
    def fake_urlopen(request, timeout=0):  # noqa: ANN001 - mirrors urlopen's shape
        assert "versionhistory.googleapis.com" in request.full_url
        yield _Response()

    monkeypatch.setattr(service, "urlopen", fake_urlopen)

    assert service.chrome_published_version() == "151.0.7922.138"


def test_launcher_points_at_the_browser(tmp_path: Path) -> None:
    build = tmp_path / service.PORTABLE_NAME
    build.mkdir(parents=True)

    launcher = service._write_launcher(_context(tmp_path), build)

    assert launcher.name == f"{service.PORTABLE_NAME}.cmd"
    assert f"App\\{service.BROWSER_EXECUTABLE}" in launcher.read_text(encoding="utf-8")


def test_read_guard_result_parses_status_and_detail(tmp_path: Path) -> None:
    result = tmp_path / "guard.result"
    result.write_text("ADDED\tC:\\out", encoding="utf-8")
    assert service._read_guard_result(result) == "ADDED: C:\\out"

    result.write_text("REMOVED", encoding="utf-8")
    assert service._read_guard_result(result) == "REMOVED"

    assert service._read_guard_result(tmp_path / "missing") == ""


def test_defender_guard_is_a_noop_when_defender_is_inactive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No Defender means no elevation: the guard must never reach for UAC."""
    context = _context(tmp_path)
    monkeypatch.setattr(service, "_defender_active", lambda _ctx: False)

    def fail_if_elevated(*_args: object, **_kwargs: object) -> int:
        raise AssertionError("_defender_guard tried to elevate while Defender was inactive")

    monkeypatch.setattr(service, "_run_elevated_powershell", fail_if_elevated)

    entered = False
    with service._defender_guard(context, context.paths.output):
        entered = True
    assert entered
    # An inactive Defender leaves no guard bookkeeping behind at all.
    assert not (context.paths.workspace / service._DEFENDER_GUARD_DIRNAME).exists()


def test_guard_path_argument_joins_with_a_pipe(tmp_path: Path) -> None:
    """Folders travel through ShellExecute as one '|'-joined argument; spaces stay."""
    joined = service._guard_path_argument([Path(r"E:\out"), Path(r"D:\build x\App")])
    assert joined == r"E:\out|D:\build x\App"
    assert joined.split("|") == [r"E:\out", r"D:\build x\App"]


def test_defender_guard_survives_a_declined_uac(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A declined UAC (ShellExecute code 5) must not abort the build; it proceeds unguarded."""
    context = _context(tmp_path)
    monkeypatch.setattr(service, "_defender_active", lambda _ctx: True)
    monkeypatch.setattr(service, "_run_elevated_powershell", lambda _script, _args: 5)

    entered = False
    with service._defender_guard(context, context.paths.output):
        entered = True
    assert entered

    # The lock file is always cleaned up, guarded or not.
    leftovers = list((context.paths.workspace / service._DEFENDER_GUARD_DIRNAME).glob("*"))
    assert leftovers == []
