# Known Limitations

This project is now stabilized for demo and controlled deployment preparation, but it is not yet a full enterprise-hardened plant platform.

## Current limitations

- API key mode is not full user login or role-based access control
- `VITE_API_KEY` is visible in the frontend build and should only be used in controlled environments
- runtime polling status is stored in memory and resets on backend restart
- polling is sequential, so one slow meter/bus can still lengthen a cycle
- database archiving and long-term purge policy still require plant approval
- a Task Scheduler watchdog is implemented; a native Windows Service is not
- deployment still requires controlled network and security boundaries
- different meter models require verified register maps before live use
- scheduled reports depend on the backend process and report worker being restarted successfully
- frontend and backend are suitable for a supervised local/plant deployment, not open internet exposure

## What this means in practice

- Suitable for: internal demo, engineering review, supervised pilot, controlled local-network use
- Not suitable yet for: internet-exposed production deployment with multi-user auth/compliance requirements

## Recommended next steps after demo readiness

- add real authentication and authorization
- consider native Windows Service packaging if Task Scheduler is not sufficient
- define database retention and backup policy
- add structured operational logging and log rotation policy
- validate each meter model/register map before rollout
