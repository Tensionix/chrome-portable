# Audion Chrome Portable - user guide

**Contents**

- [How the window works](#how-the-window-works)
- [First run](#first-run)
- [What is inside the build](#what-is-inside-the-build)
- [Updating](#updating)
- [The certificate block](#the-certificate-block)
- [Build settings](#build-settings)

This program makes a portable Google Chrome: it lives in a folder, starts from
anywhere, and is never installed into Windows. Bookmarks, passwords and tabs stay
inside that folder. It does not disturb an installed Chrome — both can be open at
the same time.

## How the window works

Four tabs across the top: `INSTALL`, `UPDATE`, `CERTIFICATE`, `SERVICE`. That is
the whole menu: press a tab and its commands, with their settings, are right
underneath. Above the tabs sits a service strip with the folder cleanups, which
belong to the program as a whole.

Choices are made with buttons — the chosen one washed with blue, the rest
outlined. Captions are short; the explanation appears in the tooltip when the
pointer rests on a button or a checkbox.

## First run

1. Tab `SERVICE` → `7-ZIP`. The installer cannot be unpacked without it.
2. Tab `INSTALL` → `BUILD`.

About 120 MB is downloaded. The finished build appears in the Target folder
(`output\Portable\Google Chrome Portable`); start it with
`Google Chrome Portable.cmd` in its root.

## What is inside the build

| Folder or file | What it is |
| --- | --- |
| `App` | The browser itself. Replaced wholesale on update. |
| `Data` | Your profile: bookmarks, passwords, tabs, extensions. |
| `Cache` | Cache. Safe to delete. |
| `Certificates` | The Ministry of Digital Development certificates and two files: install and remove. |
| `Google Chrome Portable.cmd` | Starts the browser. |
| `Portable-Build.json` | Which versions are inside. |

## Updating

The `UPDATE` tab.

`CHECK` reads the published Chrome version and shows it next to the version of
your build. The installer is not downloaded for this.

`UPDATE` replaces only the browser inside the build: `Data` and `Cache` are kept,
so the profile stays.

**The update happens where the build lies.** Point Source at its folder — a flash
drive, a network share, wherever it lives — and it is updated in place. Nothing
has to be copied, and the Target folder is not used here: that one is for new
builds. With nothing in Source, the program looks in `output\Portable`.

`CHROME++` refreshes the wrapper alone — 180 KB. It is released more often than
Chrome itself, and the browser and the profile are left untouched.

## The certificate block

Russian state sites are signed by an authority Windows does not trust out of the
box, so such a site opens with a security warning. The steps are separate so that
nothing happens by itself. They all live on the `CERTIFICATE` tab.

**`INTO THE BUILD`.** Downloads both certificates into the build folder along
with `Install-Russian-Trusted-CA.cmd` and `Uninstall-Russian-Trusted-CA.cmd`. No
trust is added — these are files, and they can be handed over with the build.

**`INSTALL`.** Adds the certificates to your own Windows account's store, which
Chrome reads. No administrator rights are needed and other users of the machine
see no change. The `Install-Russian-Trusted-CA.cmd` file in the build does the
same thing.

**`REVOKE`.** Removes exactly those two certificates — by fingerprint rather than
by name, so nothing else is touched.

**`CHECK`** shows whether they are installed and changes nothing.

Worth understanding: a certificate cannot be kept "in the browser's folder only".
Chrome on Windows reads the user's store, not a file beside itself. That is why
trust is a separate decision — and always reversible.

Yandex Browser needs none of this: it trusts that CA out of the box. It has its
own program — Audion Yandex Portable.

## Build settings

**State site certificates.** On. Places the files and two shortcuts into the
build. Installs nothing.

**Leave no traces in Windows.** Off, deliberately: with it on, Chrome wipes
`HKCU\Software\Google\Chrome` when it exits, and that branch is shared with an
installed Chrome, which is present almost everywhere. Turn it on only on a
machine without one.

**Pack into an archive.** Turn it on when the build is to be handed over: one
file instead of a folder. The format sits next to it — `ZIP` opens anywhere, `7Z`
is smaller but needs 7-Zip on the other side.

**Portability.** What keeps the profile inside the build folder. `CHROME++` is
the wrapper this program started with: its `version.dll` goes next to the
browser. `PROXY LIBRARY` is another wrapper of the same kind, by neyrostalker: it does
the same job, additionally blocks writes to the registry, and Microsoft's
antivirus does not treat it as a threat. The differences and the check results are in
`docs/CHROME_PLUS_AND_DEFENDER.md`.

**Wrapper architecture.** Leave it at `X64` — that is what the Chrome installer
is.

**Keep working files** (under `Advanced`). The download and the unpacked
installer stay in `workspace` — useful when a build failed and the reason has to
be found.
