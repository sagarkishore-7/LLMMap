# Authorization and Safety

## Legal Disclaimer

LLMMap is a security testing tool intended for authorized use only. Usage of LLMMap against targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws. The developers assume no liability and are not responsible for any misuse or damage caused by this program.

**Only test systems you own or have explicit written authorization to test.**

Unauthorized access to computer systems is a criminal offense in most jurisdictions, including under the Computer Fraud and Abuse Act (CFAA) in the United States, the Computer Misuse Act in the United Kingdom, and equivalent legislation worldwide. Prompt injection testing may trigger security monitoring, violate terms of service, or cause unintended side effects on production systems.

## Safe Mode

Safe mode is enabled by default. When active, LLMMap restricts the scan to low-risk prompt families and obfuscation techniques. Risky families such as tool abuse and system override are blocked.

Safe mode restrictions apply automatically. Aggressive prompt families are excluded from the default scan pipeline to reduce risk during routine testing.

## Dry-Run Mode

Use `--mode dry` to load and plan a scan without sending any HTTP requests. This is useful for reviewing which prompts would be selected, validating configuration, and auditing scan plans before execution.

```bash
llmmap --mode dry --target-url https://example.com --goal "..."
```

Dry-run mode produces the same scan plan and prompt selection output but makes no network connections to the target.

## Run Artifacts

Each scan creates a workspace under `runs/<run_id>/` containing request metadata, scan configuration, and timing information. Sensitive prompt text and response bodies are kept in memory only and are not written to disk by default.

Use `--output-dir` to change the artifact directory:

```bash
llmmap -r request.txt --goal "..." --output-dir /tmp/scans
```

## Responsible Disclosure

If you discover a vulnerability using LLMMap, follow responsible disclosure practices:

1. **Report privately.** Contact the affected vendor or maintainer through their published security contact or vulnerability disclosure program before publishing any findings.
2. **Provide sufficient detail.** Include the technique used, the observed behavior, and steps to reproduce, so the issue can be triaged and fixed.
3. **Allow reasonable time.** Give the vendor adequate time to develop and deploy a fix before any public disclosure. Industry norms typically allow 90 days.
4. **Do not exploit.** Use findings solely to improve security. Do not exfiltrate data, escalate access, or cause disruption beyond what is necessary to demonstrate the issue.
5. **Document your authorization.** Retain evidence of your testing authorization (scope, dates, contacts) in case questions arise later.

If you discover a security issue in LLMMap itself, please report it by opening a security advisory on the GitHub repository or contacting the maintainers directly.
