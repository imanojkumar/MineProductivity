# Security Policy

## Supported Versions

MineProductivity is currently in the repository-skeleton / pre-alpha phase.
No released version currently carries security support guarantees.

| Version | Supported |
|---------|-----------|
| 0.1.x   | :white_check_mark: (best-effort, pre-alpha) |
| < 0.1   | :x: |

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

As this repository currently contains no business logic (structural skeleton
only), the primary security surface is the build/packaging toolchain and
CI/CD configuration. This policy will expand in scope as implementation
proceeds.
