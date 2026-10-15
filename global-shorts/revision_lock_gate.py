#!/usr/bin/env python3
"""Fail closed on edits outside locked Global Shorts areas; not a visual QA gate."""
import argparse, json, subprocess, sys
from pathlib import Path

class LockError(ValueError): pass

CHECKOUT="      - uses: actions/checkout@v4\n"
FULL_CHECKOUT=CHECKOUT+"        with:\n          fetch-depth: 0\n"
GUARD=("      - name: Revision lock preflight (fail closed)\n"
       "        run: |\n"
       "          python3 global-shorts/test_revision_lock.py\n"
       "          python3 global-shorts/revision_lock_gate.py --contract global-shorts/revision_contracts/odd_factory_v6.json\n")

def normalize_workflow(s):
    if s.count(FULL_CHECKOUT)!=1 or s.count(GUARD)!=1:
        raise LockError("Missing, altered or duplicate revision guard")
    if s.index(GUARD)>s.index("      - name: Install Blender and FFmpeg"):
        raise LockError("Must run lock gate before Blender")
    return s.replace(GUARD,"",1).replace(FULL_CHECKOUT,CHECKOUT,1)

def chunks(s,regions):
    offset=0; parts=[]
    for i,r in enumerate(regions):
        a,b=r.get("start"),r.get("end")
        if not isinstance(a,str) or not isinstance(b,str) or not a or not b or s.count(a)!=1 or s.count(b)!=1:
            raise LockError(f"Invalid/ambiguous bounds for region {i}")
        left=s.find(a,offset)
        if left<offset: raise LockError("Region order invalid")
        after=left+len(a); right=s.find(b,after)
        if right<0: raise LockError("Region end missing")
        parts.append(s[offset:after]);offset=right
    parts.append(s[offset:])
    return parts

def protect(baseline,current,regions,path):
    if chunks(baseline,regions)!=chunks(current,regions):
        raise LockError(f"Protected code drift: {path}")
    return {"path":path,"editable_regions":len(regions),"same_as_baseline":baseline==current}

def validate(contract,root):
    ref=contract.get("baseline_commit","")
    if len(ref)!=40 or any(c not in "0123456789abcdef" for c in ref):
        raise LockError("Missing immutable commit SHA")
    if contract.get("baseline_status")!="PRESERVE_BASELINE_NOT_COMMERCIAL_PASS":
        raise LockError("Commercial PASS may not be inferred")
    files=contract.get("files")
    if not isinstance(files,dict) or not files: raise LockError("No protected files")
    results=[]
    for path,opt in files.items():
        target=(root/path).resolve()
        if path.startswith("/") or ".." in Path(path).parts or not target.is_relative_to(root.resolve()) or not target.is_file():
            raise LockError(f"Unsafe/missing path: {path}")
        try:
            previous=subprocess.run(["git","show",f"{ref}:{path}"],cwd=root,check=True,text=True,capture_output=True,timeout=15).stdout
        except (OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
            raise LockError(f"Missing historical baseline for {path}: {e}")
        current=target.read_text(encoding="utf-8")
        if opt.get("workflow_guard"): current=normalize_workflow(current)
        results.append(protect(previous,current,opt.get("edit_regions",[]),path))
    return {"status":"REVISION_SCOPE_PASS","commercial_approved":False,"files":results}

def main():
    p=argparse.ArgumentParser();p.add_argument("--contract",type=Path,required=True);p.add_argument("--root",type=Path,default=Path.cwd())
    a=p.parse_args()
    try:
        path=a.contract if a.contract.is_absolute() else a.root/a.contract
        result=validate(json.loads(path.read_text(encoding="utf-8")),a.root)
    except (LockError,ValueError,TypeError,OSError) as e:
        print(json.dumps({"status":"EDIT_SCOPE_BLOCKED","reason":str(e)},ensure_ascii=False));return 1
    print(json.dumps(result,ensure_ascii=False));return 0

if __name__=="__main__":sys.exit(main())
