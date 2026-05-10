# FDU-01 Fault Report

## Summary
- Device: FDU01
- Total Events: 80
- NORMAL: 66
- WARN: 6
- CRITICAL: 8

## Detected Fault Timeline
1. 2026-05-05T14:05:00 - [WARN] temperature elevated
2. 2026-05-05T14:05:10 - [WARN] temperature elevated
3. 2026-05-05T14:05:20 - [WARN] temperature elevated
4. 2026-05-05T14:05:30 - [WARN] temperature elevated
5. 2026-05-05T14:05:40 - [WARN] temperature elevated
6. 2026-05-05T14:05:50 - [WARN] temperature elevated
7. 2026-05-05T14:07:30 - [CRITICAL] battery critical
8. 2026-05-05T14:07:40 - [CRITICAL] battery critical
9. 2026-05-05T14:07:50 - [CRITICAL] battery critical
10. 2026-05-05T14:08:00 - [CRITICAL] battery critical
11. 2026-05-05T14:10:00 - [CRITICAL] gps fix lost
12. 2026-05-05T14:10:10 - [CRITICAL] gps fix lost
13. 2026-05-05T14:10:20 - [CRITICAL] gps fix lost
14. 2026-05-05T14:10:30 - [CRITICAL] gps fix lost

## Possible Cause
Battery degradation or high-load operation may have caused voltage drop and temperature increase.

## Recommended Follow-up
- Check battery condition and load profile.
- Review thermal environment and cooling path.
- Verify GNSS antenna placement and cable connection.
- Compare telemetry timeout pattern with communication logs.
