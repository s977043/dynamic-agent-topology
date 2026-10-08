import json,sys
src,out,*names=sys.argv[1:]
d=json.load(open(src))
if 'clone3' in names:
    d['syscalls']=[s for s in d['syscalls'] if not (s['names']==['clone3'] and s['action']=='SCMP_ACT_ERRNO')]
if names:
    d['syscalls'].append({"names":sorted(names),"action":"SCMP_ACT_ALLOW","comment":"bwrap (Codex sandbox) user/mount/pid namespaces without CAP_SYS_ADMIN"})
json.dump(d,open(out,'w'),indent=1)
