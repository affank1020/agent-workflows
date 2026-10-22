# Pull latest — Prepare PR

**Source of truth:** the reviewed `main` branch of this repository. Never edit the installed ChatGPT skill separately.

The builder reads only Git-tracked, commit-matching files and constructs both portable and legacy plugin manifests. It cannot contact Plugin Creator, install plugins, or publish releases.

## Controlled update procedure

1. Resolve current remote `main` to a full commit SHA and check it out in a clean, dedicated directory. Avoid relying on a stale VPS checkout. Run `python3 -m unittest discover -s tests -v` and `python3 scripts/validate.py` with the dependencies from `requirements-dev.txt`.
2. Read **the existing** private Prepare PR plugin `plugins_6ad9fe3ef0688191af1c9c4a7d5934ac` using Plugin Creator's `get_plugin_files` or `get_plugin_metadata`. Capture **both** its current version (e.g. `0.1.1`) and its **current_release_id**. If access is unavailable, stop before publication.
3. Compare its installed skill, references, shared workflow and presentation configuration against the reviewed GitHub source. Ignore only generated release-version differences. **Do nothing if the installed content is already equivalent.**
4. When content actually changed, build the archive using the version read in step 2:

   ```bash
   python3 scripts/build_plugin.py \
     --installed-version 0.1.1 \
     --output /tmp/prepare-pr-latest.zip \
     --report /tmp/prepare-pr-provenance.json
   ```

   Replace `0.1.1` with the live installed version; **never reuse this example value**. The builder chooses the greater of the checked-in baseline and current installed version. Plugin Creator automatically advances a submitted equal version to the next patch (for example, `0.1.1` becomes `0.1.2`); lower versions are rejected. Only stable `MAJOR.MINOR.PATCH` versions are currently supported. If the installed version is prerelease/build-metadata versioned, stop for an explicit packaging change.
5. Inspect the provenance report, ZIP SHA-256, complete file inventory and both manifests. Ensure that the **source commit matches the reviewed main SHA**, every source file was verified byte-for-byte against that commit, both manifests have the same effective version, and the ZIP only contains expected files. The manifest version is a **generated field** derived from canonical config and the live installed version; the rest of the packaged content is tracked in Git. The CI artifact, by contrast, is only an offline **preview** built using the checked-in baseline; do not publish it unmodified.
6. **Re-read** the installed plugin's current version and `current_release_id` immediately before updating. If either differs from step 2, discard the ZIP and restart comparison/build using the new version. Submit the ZIP via the authenticated Plugin Creator `update_plugin` operation using exactly that plugin ID and `expected_release_id`. **Never create a replacement plugin.**
7. Confirm the returned plugin ID, release ID and generated version, and inspect the installed file inventory for any missing or stale files. If source files have deliberately been removed, pass the current installed paths using `delete_paths` after reviewing impact: omitted files are otherwise preserved by the overlay update. Verify `@Prepare PR` remains available.
8. Report the Git source SHA, ZIP checksum and resulting plugin release. Do not commit credentials or edit source after creating the ZIP without rebuilding.

### Offline package preview

```bash
python3 scripts/build_plugin.py --output /tmp/prepare-pr-preview.zip
```

Without `--installed-version` the builder deliberately uses the checked-in version for testing only; **this is not a safe publish command after the installed plugin has advanced**.

## Example user request

> Pull the latest reviewed Prepare PR skill from `affank1020/agent-workflows` main, validate and rebuild its package, and update my existing private `@Prepare PR` plugin in place. Don't make changes if already current.

GitHub Actions builds and tests but **never publishes automatically**. This separation prevents unreviewed merges or CI credentials from changing installed behavior. Additional skills can later adopt the same model with separately declared plugin identities.
