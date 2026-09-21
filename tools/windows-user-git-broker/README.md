# Windows User-Scoped Authenticated Git Broker V1

Capability: `host_runtime.git_authenticated_v1`

This component keeps the SentinelX Windows service running as LocalSystem while routing only authenticated Git remote operations through a Limited Scheduled Task owned by the currently logged-in Windows user.

It exists for the common split where:

- interactive PowerShell can fetch/push a private repository through Git Credential Manager;
- the SentinelX LocalSystem service cannot access that user's credential store;
- remote Git calls otherwise block on credential/network timeout.

## Security boundary

The broker accepts only:

- `preflight`
- `ls_remote`
- `fetch`
- `push`

It does not expose arbitrary run-as-user command execution.

Additional guarantees:

- repository paths are restricted by `allowed_roots`;
- Git runs with terminal prompting disabled;
- credential material is never requested or returned;
- output is scrubbed for credential-looking URL and token/password fields;
- force push requires an exact `--force-with-lease` SHA;
- timeouts are bounded;
- the Scheduled Task runs with `RunLevel Limited`;
- the existing SentinelX LocalSystem service remains unchanged.

## Install

Copy this directory to a host-controlled location, create `broker-config.json` from the example, then run `setup.ps1` from an administrative or LocalSystem context while the intended Windows user is logged in.

The setup registers `DevForgeUserGitBroker` using:

- the current interactive Windows user;
- `LogonType Interactive`;
- `RunLevel Limited`;
- restart-on-failure;
- start-at-logon.

## Host Runtime usage

```powershell
python client.py preflight --repo D:\coco\DevForge --write
python client.py fetch --repo D:\coco\DevForge
python client.py ls-remote --repo D:\coco\DevForge --pattern HEAD
python client.py push --repo D:\coco\DevForge --branch main --source HEAD
```

Successful preflight returns evidence equivalent to:

```json
{
  "capability": "host_runtime.git_authenticated_v1",
  "context_class": "user_scoped",
  "non_interactive": true,
  "canonical_remote_verified": true,
  "credential_material_exposed": false,
  "bounded_timeout": true,
  "bounded_retry": true,
  "state": "READY"
}
```

Credential failures are classified as BLOCKED. Transport timeout/reset/unavailability is classified as INTERRUPTED so the caller can preserve the logical Run/Slice and resume without replaying verified side effects.

## Validation

Run:

```powershell
python test_broker.py
```

The regression covers secret scrubbing, failure classification, path escape rejection, local bare-remote preflight/fetch/push, and force-with-lease enforcement.

A real private-remote acceptance test should additionally verify:

```powershell
python client.py preflight --repo <private-repo> --write --timeout 20
python client.py fetch --repo <private-repo> --timeout 30
```

No credential value should appear in either response.
