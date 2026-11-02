# Street CEO repository boundaries

The published repository contains the customer shop product and source needed to
build, run and test it. The Project Operations Office is a separate local app.

Tracked: web and Android source, Gradle wrapper, npm lockfiles, backend/domain
code, starter catalogue, tests, setup tools, documentation, logo and development
records. Agent brains are records, not the team-view application, and stay tracked.

Ignored: secrets, runtime databases/traces, logs, temporary tests, chat attachments,
dependencies, generated bundles, Android outputs, SDK machine paths and signing
keys. Existing local copies are preserved.

Generated product-diagram PNG/PDF exports and the inspection preview are also
local-only. Their editable SVG, standalone HTML and export script remain tracked.
Android APKs belong in separately published release assets, not source commits;
a source push does not upload an APK automatically.

The local team frontend is `apps/web/local-office/`; its output is
`apps/web/dist-office/`. Optional local backend files are
`services/api/local_team.py`, `team_activity.py`, `project_office.py` and their two
team-only tests. These remain local and ignored. Explicit
`STREET_CEO_LOCAL_TEAM_ENABLED=1` enables that backend; normal shop startup never
imports it. Optional `*:office` npm commands require local files and are not part
of clone setup. Historical development notes may still mention the team app.

Previously tracked ignored files are removed from the Git index while their
working copies remain. This does not erase previous Git history.
