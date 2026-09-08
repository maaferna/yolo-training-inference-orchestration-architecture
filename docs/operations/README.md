# Operations Documents (Retired)

The operational calendar that used to live in this folder — a cloud-to-self-hosted tracking
migration plan, status and delivery reports, a quick reference and an implementation roadmap —
has been retired.

It scheduled work by quarter. This repository dates nothing by calendar: decisions carry an
iteration, and each step of the evolution path waits for its operational trigger (see
[`17-public-release-sanitization.md`](../architecture/17-public-release-sanitization.md) for the
rule and [`16-production-evolution-roadmap.md`](../architecture/16-production-evolution-roadmap.md)
for the criterion). A calendar that has passed is a promise the reader can check, and the
repository would rather record what happened than what was planned.

Where the content went:

| It used to describe | Where it lives now |
|---|---|
| The tracking tool decision and its self-hosted plan | [`ADR-004`](../architecture/adr/ADR-004-clearml-experiment-tracking.md), [`ADR-007`](../architecture/adr/ADR-007-clearml-experiment-tracking.md), and the later revision of that decision in the ADR index |
| Job status, background execution, model registry | `docs/evolution/` — the later revision of the architecture |
| What to build next and why | [`16-production-evolution-roadmap.md`](../architecture/16-production-evolution-roadmap.md) |
| Storage layout, ports, service names | [`06-docker-runtime-architecture.md`](../architecture/06-docker-runtime-architecture.md), [`07-shared-storage-and-artifacts.md`](../architecture/07-shared-storage-and-artifacts.md) |

Nothing operational in the strict sense — hostnames, runbooks, access procedures — was ever
published here, and none will be.
