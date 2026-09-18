# Audion Chrome Portable

<!-- audion:release -->
<p align="center">
  <a href="https://audion.dev/downloads/chrome-portable"><img alt="Windows" src="https://img.shields.io/badge/Windows-10%20%7C%2011-0b6db8?style=flat-square&logo=windows&logoColor=white"></a>
  <a href="https://github.com/Tensionix/chrome-portable/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/Tensionix/chrome-portable?style=flat-square&label=release&color=e08a63"></a>
  <a href="https://github.com/Tensionix/chrome-portable/releases"><img alt="Downloads" src="https://img.shields.io/github/downloads/Tensionix/chrome-portable/total?style=flat-square&label=downloads&color=5fd08a"></a>
  <a href="https://github.com/Tensionix/chrome-portable/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/Tensionix/chrome-portable?style=flat-square&color=5fd08a&logo=apache&logoColor=white&cacheSeconds=3600"></a>
</p>

**Version 1.0.2** · 2026-09-18 · 4.2 MB

- [Direct download](https://dl.audion.dev/chrome-portable/1.0.2/Audion_Chrome_Portable_v1.0.2.zip) — unmetered, no rate limits
- [Project page](https://audion.dev/downloads/chrome-portable) — every version and how to install

<p align="center"><img src="docs/screenshot.png" alt="The program window" width="560"></p>

`SHA-256: 26a5d40bb1dae907007ec6f4f3068b05b01d18e469e9f4a305c94b0c59162163`

---

An **Audion** tool, published by [Tensionix](https://github.com/Tensionix).
<!-- /audion:release -->


[Русский](docs/README_RU.md) · [User Guide](docs/USER_GUIDE_EN.md)

**Contents**

- [Why It Exists](#why-it-exists)
- [What Is in the Build](#what-is-in-the-build)
- [Certificates](#certificates)
- [Chrome++](#chrome)
- [Next](#next)
- [Technical Reference](#technical-reference)

Builds a portable Google Chrome, keeps it updated, keeps Chrome++ current, and
places the Russian state root certificates into the build.

## Why It Exists

Google Chrome has **no portable build at all** — neither official nor a
maintained third-party one. Yet the browser itself is perfectly portable:
everything it needs sits beside the executable, and the only obstacle is an
installer insistent on spreading it across the system.

The answer is simple: **do not run the installer — unpack it**.

```
ChromeStandaloneSetup64.exe (~120 MB)
└── Chrome.7z
    └── Chrome-bin\  →  <build>\App\
          chrome.exe
```

Out of a hundred and twenty megabytes of installer comes the thing it was built
to deliver, placed into a build folder. Nothing is installed into Windows.

## What Is in the Build

```
App\                          the browser itself
Data\                         the profile: bookmarks, extensions, settings
Certificates\                 the state root certificates and two wrappers
Google Chrome Portable.cmd    launcher
Portable-Build.json           which versions are inside
```

It travels whole. The profile is inside — moving to another machine loses neither
bookmarks nor extensions.

## Certificates

Russian state portals issue certificates absent from the Windows store — and
without them those sites will not open. The program places them into the build
along with **two wrappers: install and remove**.

The second matters as much as the first. Installing a root certificate changes
the system, and that change must be undoable in one action rather than by hunting
through the certificate store.

## Chrome++

The add-on the build's convenience rests on. The program keeps it current
alongside the browser itself.

One thing is worth knowing about it: **a build can fail during packing with a
file access error** — and that is neither the disk nor a corrupt archive, but the
antivirus inspecting a freshly written executable. Covered in
`tools\CHROME_PLUS_AND_DEFENDER.md` (Russian).

## Next

* [User Guide](docs/USER_GUIDE_EN.md) — step by step.
* [Checklist](docs/SMOKE_TEST_RU.md) — what is run before a release (Russian).
* `tools\CHROME_PLUS_AND_DEFENDER.md` — Chrome++ and the antivirus.
* `tools\DECISIONS_EN.md` — decisions taken.

---

## Technical Reference

### The Window

Four switchable tabs. A command with its parameters unfolds on the tab itself: its
own run button named after the action, with the parameters beside it — not in a
separate settings dialog.

### Updating

What the vendor released is compared against what is in the build. Only what
changed is updated; the profile is left alone.
