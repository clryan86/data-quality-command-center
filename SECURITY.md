# Security Policy

This repository is a portfolio application, not a hosted multi-tenant data platform.

Uploaded filenames are reduced to their basename, accepted file extensions are restricted, and upload size is bounded. Uploaded data is never executed as code.

A production deployment should add authentication/authorization, malware scanning, encrypted object storage, tenant isolation, rate limits, database encryption, structured audit logging, and a retention/deletion policy for uploaded datasets.
