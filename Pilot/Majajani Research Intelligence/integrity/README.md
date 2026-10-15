# Release fingerprint

`SHA256SUMS` is the SHA-256 baseline for the manuscript source, final DOCX/PDF, visual assets, satellite crops, data tables, scripts, repository documentation and build files. It excludes itself and Git metadata.

Verify the baseline:

```sh
python3 scripts/fingerprint_release.py --verify
```

After a deliberate, reviewed edit and regeneration of the relevant outputs, refresh the baseline:

```sh
python3 scripts/fingerprint_release.py --write
```

This detects byte changes, missing files and newly added files relative to the recorded baseline. It does **not** determine whether an edit was made by a person, an AI system or other software; it does not prevent editing; and an unsigned manifest can itself be replaced by someone who can write to the repository. For stronger authorship assurance, retain the manifest somewhere independently controlled or sign it with the author’s own GPG/minisign key. No private signing key is stored in this repository.
