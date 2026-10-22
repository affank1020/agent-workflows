# Pull latest — Prepare PR

**Source of truth:** this GitHub repository's reviewed main branch. Do not edit the installed ChatGPT plugin directly.

The package builder creates a ZIP containing exactly the files the existing private **Prepare PR** plugin needs. It has **no GitHub write access** and **cannot publish a ChatGPT plugin**. Publication is a separate, explicit authenticated step.

## Build an update from the latest merged commit

1. Fetch the repository's **current** remote main and check out that exact commit in a clean, dedicated working directory. Do not assume a longstanding Linux checkout is up to date. Inspect for unrelated changes before proceeding.
2. Run the repository validation and regression tests.
3. Run the deterministic builder:

   ```bash
python3 scripts/build_plugin.py --output /tmp/prepare-pr-latest.zip --report /tmp/prepare-pr-provenance.json
```

4. Verify the resulting ZIP inventory, file contents, SHA-256 and provenance. The manifest's `name` must remain `prepare-pr`, and the visible display name must remain `Prepare PR`.
5. Obtain the **current release ID** of the existing private plugin (ID `plugins_6ad9fe3ef0688191af1c9c4a7d5934ac`) from the authenticated Plugin Creator's plugin-files/metadata API. Never create a new plugin for an update.
6. Compare the source release with the installed release. If their contents are equivalent, **do not publish a no-op**. If changed, submit the ZIP to Plugin Creator's **update_plugin** operation with the exact plugin ID and **expected_release_id**. It rejects stale concurrent updates.
7. Check the response for status, release ID, correct plugin identity, expected files and warnings. Keep the existing plugin private; verify `@Prepare PR` is still discoverable. If a source file has been removed, update references and explicitly request its deletion using the current installed inventory. The update operation otherwise preserves omitted files.
8. Record the source SHA and new plugin release ID in the operator's update summary. Do not commit release credentials or change the source files after packaging without rebuilding.

**Important:** GitHub Actions in this repository **builds and validates** the plugin archive; it does **not** hold ChatGPT credentials or automatically publish it. This is a deliberate on-demand rollout.

## Example user request

> Pull the latest reviewed Prepare PR skill from `affank1020/agent-workflows` main, validate and rebuild its package, and update my existing private `@Prepare PR` plugin in place. Don't make changes if already current.

This procedure is suitable for any AI client with repository-reading, local packaging and authorized plugin-update tools. If one of those capabilities is unavailable, report the specific blocker rather than inventing publication success.

## Longer-term

More skills may be added under `skills/`, each with its own packaging configuration and plugin identity. Don't bundle them all into Prepare PR unless intentionally changing its scope.
