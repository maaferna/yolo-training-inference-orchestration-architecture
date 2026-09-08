# ADR-012: Withdraw the SaaS-Default Tracking Tool; Adopt Self-Hosted Tracking-Only, Not Yet Deployed

**Status**: Accepted — **not implemented**. The withdrawal is in effect; the replacement is
decided and not deployed.
**Iteration**: revision
**Public-Safe**: Yes
**Supersedes**: [ADR-004](./ADR-004-clearml-experiment-tracking.md) and
[ADR-007](./ADR-007-clearml-experiment-tracking.md).

---

## Context

ADR-004 adopted ClearML for experiment tracking with local artifacts as the source of truth,
and ADR-007 recorded why it was preferred over MLflow and Weights & Biases, noting that none of
the candidates offered a model registry strong enough to rely on. The initial iteration ran
against the tool's hosted service, with a self-hosted deployment planned.

The revision reopened the decision for a reason the initial evaluation had not weighed as a
security property:

- The tool's SDK, when not explicitly configured, **defaults to the vendor's hosted service**.
  A developer machine or a container with the SDK installed and no configuration file sends
  metadata off-premises silently.
- The training library's integration with the tool **uploads sample imagery** as part of its
  default logging. In an environment where images are the confidential asset, a default is a
  leak path.
- The self-hosted deployment is heavy (a multi-container stack with its own databases) for a
  platform that at this iteration runs three containers, and its licensing terms for the
  self-hosted server were judged unsuitable.
- Model identity had meanwhile moved to the platform's own registry (ADR-010), so the tracking
  tool no longer needed to carry it.

## Decision

1. **Withdraw** the tool: no SDK in the AI service image, no callbacks in the training code,
   no configuration that could reach a hosted endpoint. This part is in effect.
2. **Adopt** a self-hosted MLflow tracking server for run metrics and parameters only —
   tracking, not registry, not artifact store. Model identity stays in ADR-010's registry;
   artifacts stay on the shared volume with the run manifest as their record. The registry keeps
   an optional field for a tracking run identifier, so a version can point at its run when the
   server exists.
3. **Do not deploy it yet.** No tracking server runs in the revision. Run metrics live in the
   run manifest and the validation outputs. The deployment waits for the trigger below.

### Addendum: training outside the platform

The revision's training stack required a newer deep-learning runtime than the inference
service's pinned dependency set. Rather than couple inference releases to training upgrades,
training was moved to notebooks outside the platform, and weights enter through the registry's
import path with a fingerprint (ADR-010). This is the reason the tracking server has no
in-platform producer yet, and the reason its deployment is deferred rather than urgent.

## Alternatives Considered

### Keep the tool, configure it strictly
Rejected. A default that is safe only when configured is a default that will eventually be
unconfigured. The image-upload behaviour would also have to be disabled in every training
entry point, forever.

### Self-host the same tool
Rejected: footprint and licensing, as above, for a benefit (its UI) the revision did not need.

### Weights & Biases
Rejected: hosted by default, with the same egress concern in stronger form.

### No tracking tool; manifests only
Adopted as the **interim state**, and it is what the revision runs. Rejected as the end state
because comparing runs across a season from manifests alone is manual work the roadmap says
should be tooled once training returns to the platform.

## Consequences

### Positive
- No metadata or imagery leaves the premises by default; there is no SDK that could.
- Model identity and artifact provenance are already covered by the registry and manifests.
- The replacement, when deployed, is a single lightweight service.

### Negative
- Run comparison across many experiments is manual until the server exists.
- Two ADRs of the initial iteration are superseded, and every document that names the original
  tool as current is now historical (`12-clearml-experiment-tracking.md` carries a banner).

### Neutral
- The initial iteration's principle — local artifacts as the source of truth, tracking as
  metadata only — is unchanged and is what made the withdrawal cheap.

## Revisit When

- Training returns to the platform, or notebook training produces more runs than manifests can
  be compared by hand → deploy the tracking server.
- A tracking tool offers an SDK that refuses to send anything without explicit configuration →
  re-evaluate on that property first.

## Public-Safe Note

Tool names are those of publicly available products. No workspace, account, endpoint or
credential is mentioned. The security observations concern default behaviours documented by
the tools themselves.
