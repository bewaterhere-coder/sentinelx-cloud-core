# Unity 6.6 AppContainer DLL Initialization Compatibility V1 — Provisional Bootstrap

Status: transport bootstrap only.

Source command:

```text
#开发 SentinelX Unity 6.6 AppContainer DLL Initialization Compatibility V1
```

Stacked transport baseline:

```text
bewaterhere-coder/sentinelx-cloud-core
PR-017 head@3858c7d0e46295d5e0dc184bb21e76da7c963346
base branch: task/large-runtime-root-acl-cleanup-timeout-recovery-v1
```

Observed upstream evidence from PR-017:

```text
Unity 6000.6.4f1
scoped/AppContainer child creation succeeds
large runtime-root ACL cleanup succeeds under bounded timeout
classified child exit = 0xC0000142 / STATUS_DLL_INIT_FAILED
```

Existing repository evidence from PR-011 also proves that LocalSystem Session-0 USER32-dependent AppContainer descendants can fail DLL initialization when the unique AppContainer SID lacks minimum read authority on the broker window station/desktop.

This bootstrap does not authorize product implementation. Requirement and Plan must first prove whether Unity reproduces that same Session-0 USER32 authority gap before any generic scoped-runtime authority is widened.
