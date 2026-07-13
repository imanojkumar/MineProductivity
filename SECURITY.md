# Security Policy

## Supported Versions

MineProductivity follows [Semantic Versioning](https://semver.org/). Security
fixes are provided for the latest released minor version. Older versions are
supported on a best-effort basis until the next minor release supersedes them.

| Version | Supported |
|---------|-----------|
| Latest `2.x` | :white_check_mark: |
| `1.11.x` | :white_check_mark: (best-effort until `2.x` adoption) |
| < 1.11 | :x: |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, report vulnerabilities privately via GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability)
feature on this repository, or email the maintainers listed in
[CODEOWNERS](.github/CODEOWNERS).

Please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce, including affected package(s) under `src/mineproductivity/`.
- Any known mitigations.

## Response Process

1. Acknowledgement within 5 business days.
2. Investigation and severity assessment.
3. Coordinated disclosure timeline agreed with the reporter.
4. Patch release and public advisory once a fix is available.

## Scope

MineProductivity is a pure-Python framework whose base install carries **zero
third-party runtime dependencies**; optional extras (`events`, `connectors`,
`analytics`, `notebooks`) pull in well-known scientific and I/O libraries only
when their features are used. The primary security surface is therefore:

- the framework's own code under `src/mineproductivity/` (data ingestion via
  `connectors`, serialization, and plugin/entry-point discovery);
- third-party plugins that implement the interface-only extension points
  (solver adapters, reasoning backends, renderers, connector adapters) —
  these run with the same trust as the host application and are outside this
  repository's control;
- the build/packaging toolchain and CI/CD configuration.

Dependency and static-analysis scanning (`pip-audit`, CodeQL, dependency
review) run in CI; see [`docs/governance/CI_CD_GUIDE.md`](docs/governance/CI_CD_GUIDE.md)
for the pipeline and any documented, time-boxed exceptions.
