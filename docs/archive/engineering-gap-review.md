# Engineering Gap Review

This document is the blunt assessment of where the current system stands and what still separates it from a more professional industrial software delivery.

It is written for two purposes:

- to guide actual engineering work over the next 45 days
- to help explain the project honestly in an internship/final-submission context

## Current position

The system is no longer a toy prototype.

It already has:

- real Modbus RTU polling
- PostgreSQL persistence
- a working Flask API
- a working React frontend
- meter management
- dashboard and trends
- Excel/Word exports
- runtime health via `/api/status`
- safer polling/runtime behavior than the original build

That said, it is still closer to a strong pilot build than a polished commercial product.

## Summary judgment

Current rating by area:

| Area | Current state | Honest assessment |
|---|---|---|
| Core data acquisition | Working | Good enough for a supervised pilot |
| Runtime resilience | Improved | Acceptable for pilot, still not enterprise-grade |
| Deployment | Partially prepared | Usable with engineering supervision, not installer-grade |
| Security | Basic | Controlled-network only |
| UI/UX | Functional | Clearly weaker than commercial competition |
| Maintainability | Improving | Much better with docs, but still code-centralized |
| Productization | Early | Not yet "install and forget" software |

## Major shortcomings

## 1. The UI is functional, not polished

Current reality:

- dashboard works
- status and meter flows are safer than before
- reports exist
- pages are usable

But:

- visual hierarchy is still basic
- layout and interactions do not yet feel premium
- data density and navigation are not as operator-friendly as mature products
- overall confidence/fit-and-finish still trails products like the one your company currently pays for

Why this matters:

- industrial buyers judge trust partly through UX clarity
- a rough UI makes the whole system feel less reliable, even if backend behavior is solid

Fix direction:

- improve information hierarchy
- improve status presentation
- improve chart usability
- improve meter management clarity
- add clearer empty/error/loading states consistently

## 2. 24/7 operation is possible, but still ops-dependent

Current reality:

- backend can run continuously
- polling is isolated better than before
- status endpoint helps operational diagnosis
- plant-PC deployment docs now exist

But:

- restart behavior still depends on deployment setup discipline
- runtime state resets on restart
- watchdog/service story is practical, not deeply hardened
- long-run log/backup/retention ownership is still mostly operational rather than automatic

Why this matters:

- plant software fails in the real world mostly at the operations boundary, not only in business logic

Fix direction:

- tighten Windows service or scheduled-task deployment process
- verify auto-start, auto-restart, and log persistence on the real machine
- add simple operational checklists and repeatable recovery steps

## 3. Security is acceptable only for a controlled local network

Current reality:

- API key mode exists
- CORS is configurable
- debug mode is no longer hardcoded on

But:

- there is still no real user authentication
- frontend API key exposure means the browser is not a secure secret store
- the system should not be treated as internet-safe

Why this matters:

- pilot deployment inside a controlled plant LAN is fine
- wider deployment requires a different security posture

Fix direction:

- keep current API key mode for pilot control access
- do not expose PostgreSQL to the network
- later add real auth/authorization if the rollout broadens

## 4. Polling is reliable enough for pilot, but not yet highly scalable

Current reality:

- one bad meter should not stop others
- reconnect behavior is better
- repeated failures are less noisy
- per-meter status is tracked

But:

- polling is still sequential
- one slow or unstable bus can still stretch total cycle time
- runtime history is in memory, not persisted as an operational event log

Why this matters:

- for 4-5 meters this is still acceptable
- for broader deployment this becomes a scaling and observability issue

Fix direction:

- keep current architecture for pilot
- measure real cycle timing on site
- only consider bigger polling redesign if growth justifies it

## 5. Database design is practical, but not deeply lifecycle-managed

Current reality:

- PostgreSQL storage works
- schema is usable
- indexes are sufficient for the pilot scale

But:

- retention is not automated
- backup/restore discipline must be enforced operationally
- wide readings storage is still a pragmatic choice rather than a long-term analytics model

Why this matters:

- for a few meters at 3-minute polling, the current setup is fine
- for months/years of growth, maintenance discipline matters more

Fix direction:

- keep current schema
- enforce backup checks
- track size growth
- add retention/archive policy later if real usage demands it

## 6. Code maintainability is better, but key logic is still concentrated

Current reality:

- docs are much stronger now
- file ownership is clearer
- debugging and maintenance guidance exists

But:

- `app/api/service.py` is still a central heavy file
- `main.py` still owns many responsibilities
- some flows remain tightly coupled

Why this matters:

- a new developer can work on it now
- but larger feature growth will increase friction unless complexity is reduced over time

Fix direction:

- do not redesign during pilot prep
- refactor only when a concrete change becomes painful or risky

## 7. Productization is still incomplete

Current reality:

- repo can be cloned and run
- docs can guide setup
- plant-PC deployment is now realistic

But:

- there is no true installer yet
- there is no signed Windows package
- there is no one-click first-run experience
- there is no polished support/upgrade path

Why this matters:

- this is the gap between "engineering project" and "software product"

Fix direction:

- after pilot stabilization, create an installable Windows package
- package backend, frontend build, logs/config folders, and startup registration

## What should be fixed first

If the goal is to balance:

- deployment in the next 2 days
- strong final result in the next 45 days

then priority should be:

1. plant-PC deployment success
2. 24/7 runtime confidence
3. UI quality improvements
4. installable Windows packaging
5. stronger authentication and longer-term productization

## What not to waste time on right now

Do not spend the next few days on:

- Docker/Kubernetes
- cloud sync
- major schema redesign
- multi-tenant architecture
- full enterprise auth platform
- premature microservice refactors

Those would burn time without helping the immediate plant pilot or final internship outcome enough.

## Best framing for your final submission

The strongest honest narrative is:

- Phase 1-3 stabilized a fragile prototype into a pilot-capable system
- Phase 4 made it maintainable and deployable by others
- next work focuses on UI maturity, deployment packaging, and operator confidence
- long-term work would productize security, installation, and operational tooling

That is a credible engineering story.
