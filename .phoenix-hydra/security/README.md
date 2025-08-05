# Phoenix Hydra Security Database

This directory contains local vulnerability database storage for offline security scanning.

## Structure

- `vulnerability-cache/` - Cached vulnerability data from npm audit and OSV
- `audit-logs/` - Security audit trail logs
- `reports/` - Generated security reports
- `config/` - Local security configuration overrides

## Files

- `vulnerability-db.sqlite` - Local SQLite database for vulnerability records
- `last-update.json` - Timestamp of last vulnerability database update
- `security-metrics.json` - Security posture metrics and trends

## Offline Operation

This local cache enables Phoenix Hydra to perform security scans without internet connectivity,
maintaining the system's offline-first architecture principles.