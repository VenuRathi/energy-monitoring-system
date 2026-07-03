# Meter Configuration Guide

This system is currently set up for Schneider PM5000 / EM6400-style Modbus RTU meters.

## Key concepts

### `meter_id`

- Internal software identifier
- Used in the UI, API, and PostgreSQL
- Example: `MTR-001`

### `slave_id`

- The actual Modbus address of the physical meter on the RS485 bus
- Example: `1`, `2`, `3`

These are not the same thing.

Good pattern:

- `meter_id = MTR-001`
- `slave_id = 1`

## Serial settings

Meters sharing the same RS485 bus and COM port must use compatible serial settings.

- `com_port`: Windows serial port such as `COM6`
- `baud_rate`: normally `9600` unless the meter is configured differently
- `parity`: `N`, `E`, or `O`
- `stop_bits`: usually `1`
- `byte_size`: usually `8`
- `timeout`: per-read timeout in seconds
- `one_based_map`: register map addressing mode; keep `true` for the current Schneider map unless you have verified otherwise

## Other fields

- `enabled`: whether the meter should be polled
- `driver`: current live driver is `schneider.pm5000`
- `manufacturer` / `model`: descriptive metadata shown in UI and stored in PostgreSQL

## Current example meters

From `config/meter_config.json`:

- `MTR-001`
  - `slave_id = 1`
  - `com_port = COM6`
- `MTR-002`
  - `slave_id = 2`
  - `com_port = COM6`
- `MTR-003`
  - `slave_id = 3`
  - `com_port = COM6`
  - `enabled = false`

## How to configure MTR-001 and MTR-002

Recommended live setup:

- Confirm both meters are on the same RS485 chain
- Confirm both meters use the same baud/parity/stop/byte settings
- Confirm meter one is address `1`
- Confirm meter two is address `2`
- Keep both enabled

Example values:

```text
MTR-001 -> COM6, slave 1, 9600, N, 1, 8, timeout 2.0
MTR-002 -> COM6, slave 2, 9600, N, 1, 8, timeout 2.0
```

## How to disable meters that are not physically connected

If a meter is not installed, not powered, or not wired yet:

- set `enabled=false` in the meter UI or stored meter config
- do not leave fake or planned meters enabled in live polling

For the current project:

- keep `MTR-003` disabled unless there is a real physical meter at slave `3`

## How to avoid polling fake meters like MTR-003

- Do not enable template/demo meters in live mode
- Disable any meter with no physical device on the bus
- Verify the slave ID before enabling it

## How to check COM port in Windows Device Manager

1. Open Device Manager
2. Expand `Ports (COM & LPT)`
3. Find your USB-to-RS485 or serial adapter
4. Note the COM number, for example `COM6`

If the adapter reconnects and the COM number changes, update the meter config.

## How to avoid COM port conflicts

Only one program should hold the serial port at a time.

Common blockers:

- QModMaster
- ModScan
- vendor meter tools
- another Python instance of this project

If the backend cannot open the port:

- close QModMaster or any serial terminal
- unplug/replug the adapter if needed
- verify the backend is the only process using the COM port

## Practical checklist before enabling a meter

- Physical meter is powered
- RS485 wiring polarity is correct
- Correct slave ID is known
- Correct COM port is known
- Correct serial settings are known
- Meter driver is `schneider.pm5000`
- Meter is set `enabled=true`
- No other serial app is holding the COM port

## Safe default approach

For demo or first live test:

- enable only `MTR-001`
- confirm readings
- enable `MTR-002`
- keep `MTR-003` disabled
