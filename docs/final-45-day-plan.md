# Final 45-Day Improvement Plan

This is the practical improvement plan from the current pilot-ready state to a more professional internship-final-deliverable state.

The goal is not to pretend this becomes a full enterprise platform in 45 days.

The goal is to:

- deploy something real in the next 2 days
- continue improving after deployment
- end with a strong, defensible final submission

## Guiding principle

Work in this order:

1. make it run reliably
2. make it supportable
3. make it look professional
4. make it easier to install and hand over

## Stage 0: Immediate deployment window (next 2 days)

Objective:

- get the plant-PC instance running
- confirm readings are entering PostgreSQL
- confirm dashboard shows live values

Deliverables:

- cloned repo on plant PC
- Python, PostgreSQL, Node installed
- `.env` configured
- frontend running or built
- backend running
- COM port verified
- 1-2 real meters confirmed online
- `/api/status` verified

Success criteria:

- data is updating continuously
- no disabled/fake meters degrade status
- restart procedure is understood

## Stage 1: Pilot hardening (days 3-10)

Objective:

- reduce risk of operational embarrassment during pilot use

Work items:

- verify backend startup method for 24/7 operation
- confirm log files persist and are readable
- confirm automatic restart plan after reboot/crash
- verify 4-5 meter shared-bus configuration validation
- verify duplicate slave ID handling on the live setup
- verify exports against real data ranges
- confirm backup procedure works on the real PC

Deliverables:

- stable scheduled-task or service-style backend run
- verified plant-PC deployment checklist
- verified operator runbook steps

## Stage 2: UI maturity pass (days 10-24)

Objective:

- make the product look more credible and operator-friendly

Priority areas:

- dashboard layout and visual hierarchy
- better status cards and health presentation
- cleaner meter management flows
- clearer reports page
- stronger empty/loading/error states
- more polished typography, spacing, colors, and tables

Recommended outcome:

- not a redesign for the sake of redesign
- a sharper, more confident industrial dashboard

## Stage 3: Reporting and usability improvement (days 18-30)

Objective:

- make reports feel useful, not just technically present

Work items:

- cleaner report defaults
- clearer export validation messages
- better export metadata and headings
- better operator explanation of date ranges and empty data
- optional lightweight help/instructions view for end users

This is where an in-app help/instructions section can be added later without replacing the developer docs.

## Stage 4: Installable Windows product path (days 24-38)

Objective:

- move from "clone and configure" toward "internal software package"

Deliverables:

- installer plan using Inno Setup
- packaged frontend build
- backend launcher registration
- auto-created folders for logs/config
- first-run `.env` template flow
- desktop shortcut

Important note:

This is not required for the immediate pilot, but it is a strong professionalization step.

## Stage 5: Final submission package (days 35-45)

Objective:

- make the project easy to explain, demo, defend, and hand over

Deliverables:

- clean README/docs package
- architecture explanation
- engineering gap review
- deployment guide
- developer handover package
- demo script
- limitations section
- future roadmap

For your final report/presentation, structure the story as:

- problem statement
- architecture
- implementation
- stabilization phases
- deployment approach
- limitations
- roadmap

## Improvement backlog by priority

## Highest priority

- real plant-PC runtime verification
- scheduled restart strategy
- live meter validation on site
- frontend polish for dashboard credibility
- export/report polish

## Medium priority

- installer/package workflow
- lightweight in-app instructions/help
- richer status/history visibility
- better operator alerts and message wording

## Lower priority for now

- full auth system
- cloud features
- major schema redesign
- multi-site platformization

## Suggested weekly rhythm

### Week 1

- deploy to plant PC
- validate meters
- stabilize runtime behavior

### Week 2

- improve dashboard and meter UX
- improve empty/error states and layout quality

### Week 3

- improve reports and exports
- add operator help/instructions content if needed

### Week 4

- start installer/productization work
- tighten handover and maintenance artifacts

### Week 5-6

- polish final demo
- write final report
- validate deployment repeatability

## Success definition

At the end of this 45-day plan, the ideal result is:

- a plant-PC pilot that runs reliably
- a frontend that looks deliberate and professional
- a handover package another developer can use
- a project story you can defend confidently in front of your company and academic reviewers
