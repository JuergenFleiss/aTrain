# MSIX packaging

Files that drive the Windows MSIX build in `.github/workflows/release.yml`.

## `AppxManifest.xml.template`

Template for the package manifest. The release workflow substitutes
`{{VERSION}}` (from the tag, e.g. `1.5.0`) and writes the concrete
`AppxManifest.xml` into the PyInstaller output directory before packing
with `makeappx.exe`.

**Phase 1 (this PR) — unsigned**:

- `Publisher="CN=aTrain unsigned build"` is a placeholder.
- MSIX is packed with `makeappx.exe pack /d dist/aTrain /p aTrain-<version>.msix`.
- The result is **not** installable via double-click on Windows without
  either signing or enabling developer mode + explicit trust.
- Useful for smoke tests, download-and-inspect, and as a foundation for
  Phase 2.

**Phase 2 (future, #211)**:

- `Publisher` must match the signing certificate's subject `CN=…` exactly.
- If distributing via MS Store, the identity (`Name`, `Publisher`) must
  match what's registered in Microsoft Partner Center.
- Recommended signing path: SignPath.io OSS Community Edition (free,
  HSM-backed, GitHub Actions integration). See the #211 discussion for
  the current cert-provider trade-off (Certum vs SignPath).

## Assets

`makeappx.exe` requires PNG assets referenced by the manifest
(`StoreLogo.png`, `Square150x150Logo.png`, `Square44x44Logo.png`,
`Wide310x150Logo.png`). Placeholder assets are placed in
`packaging/msix/Assets/` and copied into the PyInstaller output during
packaging. They should be replaced with the aTrain brand marks Armin
already has for the MS Store submission before Phase 2 ships.
