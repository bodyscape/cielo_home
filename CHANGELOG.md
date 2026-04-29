# Changelog

## Unreleased

- Add temperature offset calibration as a Number entity per supporting device, plus a `cielo_home.set_temperature_offset` service on climate entities. Per-call magnitude is capped at 8 by the protocol, so reaching the extremes of the ±15 range may require multiple calls.

## 1.0.0

- First version support for Cielo Home