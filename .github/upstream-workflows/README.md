# Upstream PhotoCraft workflows (inactive) <!-- paragon:keep -->

These are PhotoCraft's own GitHub Actions workflows and Dependabot config. GitHub only runs workflows in <!-- paragon:keep -->
`.github/workflows/` (and Dependabot only reads `.github/dependabot.yml`), so here they do nothing. They were moved because they belong to the upstream <!-- paragon:keep -->
project: they call storytold's shared actions, SonarCloud and code-signing secrets, and several run
on a nightly schedule (a full release dry run among them), which would fail every night in this
repository and email you about it.

Git follows the move, so upstream changes to these files still merge in here.

To turn one on, move it back:

```bash
mkdir -p .github/workflows && git mv .github/upstream-workflows/ci.yml .github/workflows/
```
