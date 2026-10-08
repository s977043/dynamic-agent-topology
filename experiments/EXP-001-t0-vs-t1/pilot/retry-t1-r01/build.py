"""Usage: python3 build.py <moby-default.json> <out.json> <syscall>... (appends one SCMP_ACT_ALLOW rule)."""
import json
import sys

src, out, *names = sys.argv[1:]
with open(src) as f:
    d = json.load(f)
if names:
    d["syscalls"].append({"names": sorted(names), "action": "SCMP_ACT_ALLOW", "comment": "bwrap (Codex sandbox) user/mount/pid namespaces without CAP_SYS_ADMIN"})
with open(out, "w") as f:
    json.dump(d, f, indent=1)
