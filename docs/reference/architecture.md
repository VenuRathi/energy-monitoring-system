# Architecture Diagram

```mermaid
flowchart LR
  M1[Schneider Meters\nPM5000 / EM6400] --> MB[Modbus RTU Bus]
  MB --> COL[Python Collector Layer\nmodbus_client + pm5000 driver]
  COL --> POLL[Polling Service\naggregation + scheduling]
  POLL --> DB[(PostgreSQL)]
  POLL --> API[Flask API]
  DB --> API
  API --> FE[React + TypeScript Frontend]
  API --> REP[Report Export\nExcel / Word]
  API --> MAIL[SMTP Email Service]

  subgraph Runtime Modes
    DEMO[Demo Mode\nSynthetic readings]
    LIVE[Live Mode\nMeter + DB backed]
  end

  DEMO --> API
  LIVE --> API
```

## Notes

- `DEMO_MODE=true` serves synthetic dashboard and alert data for demos.
- `DEMO_MODE=false` uses live meter/database paths.
- API remains the single integration boundary for frontend and exports.
