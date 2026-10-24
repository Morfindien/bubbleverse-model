#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, shutil, stat, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

BASE = "458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee"
RUN_ID = "BV-CLEANUP-BM-20261024-458d6c33-v330"
TARGET = "morfindien/bubbleverse-model"

MOVES = [{'operation_id': 'ARCH-Q045-WF', 'old_path': '.github/workflows/install-q045-model-v07.yml', 'new_path': 'archive/programs/Q045/install-q045-model-v07/v0.7/payload/.github/workflows/install-q045-model-v07.yml', 'git_blob_sha': '9449ee232a5d41d70c4cc754ee8255981f890fe8', 'sha256': None, 'known_hash_note': 'Git blob identity is verified at BASE_SHA; SHA-256 is computed by APPLY_CLEANUP.py before mutation.', 'bundle_id': 'Q045-install-v0.7'}, {'operation_id': 'ARCH-Q045-BUNDLE', 'old_path': 'Bubbleverse_Q045_v0.7.bundle', 'new_path': 'archive/programs/Q045/install-q045-model-v07/v0.7/payload/Bubbleverse_Q045_v0.7.bundle', 'git_blob_sha': '427fdb0de3164782fa4d681a0e9295e15714f611', 'sha256': 'fd1bb405dbde3b357543ac1ed301253fedd4df8a0faed69d2c8d712ce24aaf36', 'bundle_id': 'Q045-install-v0.7'}, {'operation_id': 'ARCH-Q046-WF', 'old_path': '.github/workflows/install-q046-model-v08.yml', 'new_path': 'archive/programs/Q046/install-q046-model-v08/v0.8/payload/.github/workflows/install-q046-model-v08.yml', 'git_blob_sha': '91e10c4325d80f094b6a1e45ad1851b3c807a296', 'sha256': None, 'known_hash_note': 'Git blob identity is verified at BASE_SHA; SHA-256 is computed by APPLY_CLEANUP.py before mutation.', 'bundle_id': 'Q046-install-v0.8'}, {'operation_id': 'ARCH-Q046-PY', 'old_path': 'q046_model_update.py', 'new_path': 'archive/programs/Q046/install-q046-model-v08/v0.8/payload/q046_model_update.py', 'git_blob_sha': '5b23d0b52d8d7584d4672e2794ebc0caaa75009d', 'sha256': '7bc8da5bbb1fa224d22da80384cb40b0b5b5441d6d4018326e948b466ca41522', 'bundle_id': 'Q046-install-v0.8'}, {'operation_id': 'ARCH-Q047-WF', 'old_path': '.github/workflows/install-q047-model-v09.yml', 'new_path': 'archive/programs/Q047/install-q047-model-v09/v0.9/payload/.github/workflows/install-q047-model-v09.yml', 'git_blob_sha': '9b101b1ee08079f60cc8d97b82e5c7aa538a20d3', 'sha256': None, 'known_hash_note': 'Git blob identity is verified at BASE_SHA; SHA-256 is computed by APPLY_CLEANUP.py before mutation.', 'bundle_id': 'Q047-install-v0.9'}, {'operation_id': 'ARCH-Q047-PY', 'old_path': 'q047_model_update.py', 'new_path': 'archive/programs/Q047/install-q047-model-v09/v0.9/payload/q047_model_update.py', 'git_blob_sha': '9e90cc1d5858e463e87328920f82a3333491e288', 'sha256': 'df246ad14dc83b9bcb3226af5787583b6dfdff0843116d7cd54f764435cc5c98', 'bundle_id': 'Q047-install-v0.9'}, {'operation_id': 'ARCH-Q048-WF', 'old_path': '.github/workflows/install-q048-model-v010.yml', 'new_path': 'archive/programs/Q048/install-q048-model-v010/v0.10/payload/.github/workflows/install-q048-model-v010.yml', 'git_blob_sha': 'f9d6e3add055f83b7661056d3d563ddf33cefe81', 'sha256': None, 'known_hash_note': 'Git blob identity is verified at BASE_SHA; SHA-256 is computed by APPLY_CLEANUP.py before mutation.', 'bundle_id': 'Q048-install-v0.10'}, {'operation_id': 'ARCH-Q048-PY', 'old_path': 'q048_model_update.py', 'new_path': 'archive/programs/Q048/install-q048-model-v010/v0.10/payload/q048_model_update.py', 'git_blob_sha': '03b47bd6275fa8725faffdbc2fb845ac239d187d', 'sha256': '3342ce4ffc33b918765310b81b216d83387a7e38ef8e4cdde8751020994a9c61', 'bundle_id': 'Q048-install-v0.10'}]

DEFERRED = [{'path': '.github/workflows/apply-reviewed-repository-cleanup.yml', 'placement_decision': 'DEFER_BLOCKED', 'reason': 'One-time semantics are likely, but the workflow was deleted and later reintroduced; explicit current retirement is not established.'}, {'path': '.github/workflows/q046-model-admission.yml', 'placement_decision': 'DEFER_BLOCKED', 'reason': 'Historical Q046 admission semantics are apparent, but retirement is not explicitly recorded by the current lifecycle registry.'}, {'path': '.github/workflows/repair-q048-final-selftests.yml', 'placement_decision': 'DEFER_BLOCKED', 'reason': 'The current HEAD records the repair result, but future repair/re-entry intent is not explicitly retired.'}]

def run(repo: Path, *args, check=True):
    cp = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
    if check and cp.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed\n{cp.stdout}{cp.stderr}")
    return cp

def git(repo: Path, *args):
    return run(repo, *args).stdout.strip()

def sha256(path: Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def safe_rel(p: str):
    x=Path(p)
    if x.is_absolute() or ".." in x.parts or not x.parts:
        raise RuntimeError(f"unsafe path: {p}")
    return x

def package_root():
    return Path(__file__).resolve().parent

def origin_ok(url: str):
    u=url.strip().lower().rstrip("/")
    if u.endswith(".git"): u=u[:-4]
    return u in {
        "https://github.com/morfindien/bubbleverse-model",
        "git@github.com:morfindien/bubbleverse-model",
        "ssh://git@github.com/morfindien/bubbleverse-model",
    }

def file_mode(path: Path):
    return oct(stat.S_IMODE(path.lstat().st_mode))

def tracked(repo: Path):
    raw=subprocess.check_output(["git","ls-files","-z"],cwd=repo)
    return [x.decode() for x in raw.split(b"\0") if x]

def inventory(repo: Path, paths):
    rows=[]
    for p in paths:
        f=repo/p
        if not f.exists() and not f.is_symlink():
            raise RuntimeError(f"tracked path missing: {p}")
        if f.is_symlink():
            digest=hashlib.sha256(os.readlink(f).encode()).hexdigest()
            target=os.readlink(f)
            size=len(os.readlink(f).encode())
        else:
            digest=sha256(f); target=None; size=f.stat().st_size
        rows.append({
            "path":p,
            "git_blob_sha":git(repo,"hash-object","--",p),
            "sha256":digest,
            "size":size,
            "mode":file_mode(f),
            "symlink_target":target,
        })
    return rows

def accepted_identity(repo: Path):
    a=json.loads((repo/"accepted/model_state.json").read_text())
    if a.get("current_q")!="Q048" or a.get("accepted_model_version")!="v0.10":
        raise RuntimeError("accepted identity is not Q048/v0.10")
    return a

def receipt_gate(repo: Path):
    checks=[
        ("provenance/Q045_GITHUB_INSTALLATION_RECEIPT.json","Q045","v0.7"),
        ("provenance/Q046_INSTALLATION_RECEIPT.json","Q046","v0.8"),
        ("provenance/Q047_INSTALLATION_RECEIPT.json","Q047","v0.9"),
        ("provenance/Q048_INSTALLATION_RECEIPT.json","Q048","v0.10"),
    ]
    for path,q,v in checks:
        d=json.loads((repo/path).read_text())
        if d.get("target_q")!=q:
            raise RuntimeError(f"{path}: target_q mismatch")
        observed=d.get("accepted_version") or d.get("accepted_after")
        if observed!=v:
            raise RuntimeError(f"{path}: accepted version mismatch")
        snap=repo/"versions/accepted"/v
        if not snap.is_dir():
            raise RuntimeError(f"{path}: accepted snapshot missing")

def guard(repo: Path):
    repo=repo.resolve()
    if not (repo/".git").exists():
        raise RuntimeError("not a normal Git checkout")
    if not origin_ok(git(repo,"config","--get","remote.origin.url")):
        raise RuntimeError("wrong repository origin")
    if git(repo,"branch","--show-current")!="main":
        raise RuntimeError("cleanup requires branch main")
    if git(repo,"rev-parse","HEAD")!=BASE:
        raise RuntimeError(f"HEAD mismatch: package requires {BASE}")
    if git(repo,"status","--porcelain","--untracked-files=all"):
        raise RuntimeError("working tree must be completely clean")
    accepted_identity(repo)
    receipt_gate(repo)

    for m in MOVES:
        old=safe_rel(m["old_path"]); new=safe_rel(m["new_path"])
        src=repo/old; dst=repo/new
        if not src.is_file():
            raise RuntimeError(f"archive source missing: {old}")
        if dst.exists() or dst.is_symlink():
            raise RuntimeError(f"archive destination exists: {new}")
        blob=git(repo,"hash-object","--",old.as_posix())
        if blob!=m["git_blob_sha"]:
            raise RuntimeError(f"Git blob changed: {old}: {blob} != {m['git_blob_sha']}")
        if m.get("sha256") and sha256(src)!=m["sha256"]:
            raise RuntimeError(f"SHA-256 changed: {old}")
    for rel in [
        "START_CODES.md","docs/REPOSITORY_STRUCTURE.md","archive/programs/INDEX.md",
        "archive/programs/Q045/install-q045-model-v07/v0.7/ARCHIVE_INFO.md",
        "archive/programs/Q046/install-q046-model-v08/v0.8/ARCHIVE_INFO.md",
        "archive/programs/Q047/install-q047-model-v09/v0.9/ARCHIVE_INFO.md",
        "archive/programs/Q048/install-q048-model-v010/v0.10/ARCHIVE_INFO.md",
        f"provenance/cleanup/{RUN_ID}"
    ]:
        q=repo/rel
        if q.exists() or q.is_symlink():
            raise RuntimeError(f"new cleanup destination already exists: {rel}")
    return repo

def validators(repo: Path):
    commands=[
        [sys.executable,"tests/programs/formal_model_validate.py"],
        [sys.executable,"tests/programs/q048_model_validate.py"],
        [sys.executable,"tests/programs/model_campaign.py","validate"],
        [sys.executable,"-m","unittest","discover","-s","tests/programs","-p","test*.py"],
    ]
    results=[]
    for cmd in commands:
        cp=subprocess.run(cmd,cwd=repo,text=True,capture_output=True)
        results.append({
            "command":" ".join(cmd),
            "returncode":cp.returncode,
            "stdout_tail":cp.stdout[-4000:],
            "stderr_tail":cp.stderr[-4000:],
            "status":"PASS" if cp.returncode==0 else "FAIL",
        })
        if cp.returncode:
            raise RuntimeError(f"validation failed: {' '.join(cmd)}\n{cp.stdout}\n{cp.stderr}")
    return results

def classify(path: str):
    move={m["old_path"]:m for m in MOVES}
    if path in move:
        return "ARCHIVE_RETIRED","ARCHIVE"
    if path=="README.md":
        return "KEEP_REQUIRED_ROOT","UPDATE"
    if path=="tests/TEST_PLAN_CURRENT.md":
        return "KEEP_CORRECT_LOCATION","UPDATE"
    if path in {".gitattributes",".gitignore","bubbleverse_model_program_registry.json","repository_cleanup.py"}:
        return "KEEP_REQUIRED_ROOT","KEEP"
    if path in {d["path"] for d in DEFERRED}:
        return "DEFER_BLOCKED","KEEP"
    if path.startswith(("accepted/","candidate/","model/","evidence/","provenance/","release/","versions/accepted/","tests/results/","changelog/")):
        return "KEEP_PROTECTED","KEEP"
    return "KEEP_CORRECT_LOCATION","KEEP"

def archive_info_files(pkg: Path):
    return [
        "archive/programs/INDEX.md",
        "archive/programs/Q045/install-q045-model-v07/v0.7/ARCHIVE_INFO.md",
        "archive/programs/Q046/install-q046-model-v08/v0.8/ARCHIVE_INFO.md",
        "archive/programs/Q047/install-q047-model-v09/v0.9/ARCHIVE_INFO.md",
        "archive/programs/Q048/install-q048-model-v010/v0.10/ARCHIVE_INFO.md",
    ]

def copy_new_doc(repo: Path, rel: str, pkg_rel: str | None=None):
    src=package_root()/(pkg_rel or rel)
    dst=repo/rel
    if dst.exists() or dst.is_symlink():
        raise RuntimeError(f"refuse to overwrite new destination: {rel}")
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")

def runtime_records(repo: Path, before_rows, protected_before, pre_checks, post_checks=None):
    run_dir=repo/"provenance/cleanup"/RUN_ID
    run_dir.mkdir(parents=True,exist_ok=True)
    move_source={m["old_path"]:m for m in MOVES}
    relocation=[]
    for r in before_rows:
        placement,op=classify(r["path"])
        item=dict(r)
        item.update({"placement_decision":placement,"operation":op})
        if r["path"] in move_source:
            m=move_source[r["path"]]
            item.update({"new_path":m["new_path"],"expected_destination_git_blob_sha":m["git_blob_sha"],"batch_id":m["bundle_id"]})
        relocation.append(item)
    for rel in [
        "START_CODES.md","docs/REPOSITORY_STRUCTURE.md","archive/programs/INDEX.md",
        "archive/programs/Q045/install-q045-model-v07/v0.7/ARCHIVE_INFO.md",
        "archive/programs/Q046/install-q046-model-v08/v0.8/ARCHIVE_INFO.md",
        "archive/programs/Q047/install-q047-model-v09/v0.9/ARCHIVE_INFO.md",
        "archive/programs/Q048/install-q048-model-v010/v0.10/ARCHIVE_INFO.md",
    ]:
        relocation.append({"path":rel,"placement_decision":"KEEP_CORRECT_LOCATION","operation":"ADD"})
    write_json(run_dir/"RELOCATION_MANIFEST.json",{"schema_version":"1.0","run_id":RUN_ID,"base_sha":BASE,"entries":relocation})
    write_json(run_dir/"PROTECTED_INVENTORY.json",{"schema_version":"1.0","run_id":RUN_ID,"records":protected_before})
    write_json(run_dir/"VALIDATION_RESULTS.json",{"schema_version":"1.0","run_id":RUN_ID,"baseline":pre_checks,"post_change":post_checks or []})
    write_json(run_dir/"RUN_MANIFEST.json",{
        "schema_version":"1.0","run_id":RUN_ID,"prompt_id":"BV-REPOSITORY-CLEANUP","prompt_version":"3.3.0",
        "repository":"Morfindien/bubbleverse-model","base_sha":BASE,"mode":"CLEAN","target_q":"UNSET",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),"scientific_change":False,
        "archive_moves":len(MOVES),"deletions":0,"delivery_state":"LOCAL_STAGED_NOT_COMMITTED"
    })
    return run_dir

def apply(repo: Path):
    repo=guard(repo)
    pkg=package_root()
    baseline_paths=tracked(repo)
    before_rows=inventory(repo,baseline_paths)
    mutable={m["old_path"] for m in MOVES}|{"README.md","tests/TEST_PLAN_CURRENT.md"}
    protected_paths=[p for p in baseline_paths if p not in mutable]
    protected_before=inventory(repo,protected_paths)

    pre=validators(repo)

    created=[]
    moved=[]
    try:
        # exact-byte archive moves
        for m in MOVES:
            old=repo/m["old_path"]; new=repo/m["new_path"]
            new.parent.mkdir(parents=True,exist_ok=True)
            subprocess.run(["git","mv","--",m["old_path"],m["new_path"]],cwd=repo,check=True)
            moved.append(m)
            if git(repo,"hash-object","--",m["new_path"])!=m["git_blob_sha"]:
                raise RuntimeError(f"archive blob identity changed: {m['new_path']}")
            if m.get("sha256") and sha256(new)!=m["sha256"]:
                raise RuntimeError(f"archive SHA-256 changed: {m['new_path']}")

        # replacement docs
        shutil.copy2(pkg/"README_AFTER.md",repo/"README.md")
        shutil.copy2(pkg/"tests/TEST_PLAN_CURRENT.md",repo/"tests/TEST_PLAN_CURRENT.md")

        for rel in ["START_CODES.md","docs/REPOSITORY_STRUCTURE.md",*archive_info_files(pkg)]:
            copy_new_doc(repo,rel)
            created.append(rel)

        # cleanup memory index
        cleanup_index=repo/"provenance/cleanup/INDEX.md"
        if cleanup_index.exists():
            original=cleanup_index.read_text()
            if RUN_ID not in original:
                cleanup_index.write_text(original.rstrip()+f"\n\n- `{RUN_ID}` — Q045–Q048 retired-installer archive cleanup; see `{RUN_ID}/RUN_MANIFEST.json`.\n")
        else:
            cleanup_index.write_text(f"# Cleanup Memory Index\n\n- `{RUN_ID}` — Q045–Q048 retired-installer archive cleanup; see `{RUN_ID}/RUN_MANIFEST.json`.\n")
            created.append("provenance/cleanup/INDEX.md")

        run_dir=runtime_records(repo,before_rows,protected_before,pre,[])
        created.append(run_dir.relative_to(repo).as_posix())

        # protected byte check before tests
        after_map={r["path"]:r for r in inventory(repo,protected_paths)}
        for r in protected_before:
            a=after_map[r["path"]]
            if a["sha256"]!=r["sha256"] or a["git_blob_sha"]!=r["git_blob_sha"]:
                raise RuntimeError(f"protected file changed: {r['path']}")

        post=validators(repo)

        # update runtime check results
        val=run_dir/"VALIDATION_RESULTS.json"
        d=json.loads(val.read_text()); d["post_change"]=post; write_json(val,d)

        # Durable cleanup memory: exact runtime result plus prepared registries.
        final_report = f"""# Bubbleverse Model Repository Cleanup — Applied Result

**CLEANUP_VERIFIED**  
**Delivery state: LOCAL_ONLY / STAGED_FOR_REVIEW**

Repository: `Morfindien/bubbleverse-model`  
BASE_SHA: `{BASE}`  
Run ID: `{RUN_ID}`

Four verified retired one-time installer bundles (Q045–Q048) were archived byte-for-byte. Eight source files were relocated; zero files were deleted. Historical scientific state and protected files were verified unchanged by SHA-256 and Git blob identity.

The baseline and post-change validation suites passed:

- `python3 tests/programs/formal_model_validate.py`
- `python3 tests/programs/q048_model_validate.py`
- `python3 tests/programs/model_campaign.py validate`
- `python3 -m unittest discover -s tests/programs -p \"test*.py\"`

`tests/TEST_PLAN_CURRENT.md` was updated from stale Q047/v0.9 guidance to Q048/v0.10. `START_CODES.md`, `docs/REPOSITORY_STRUCTURE.md` and the retired-program archive index were installed.

No commit or push was performed. The cleanup is staged locally for operator review. Historical scientific verdicts are unchanged.

Deferred retirement candidates remain untouched: `apply-reviewed-repository-cleanup.yml`, `q046-model-admission.yml`, and `repair-q048-final-selftests.yml`.

Cheapest next action: review `git diff --cached`, then either commit the cleanup or run the scoped rollback.
"""
        (run_dir/"REPORT.md").write_text(final_report)
        for src_name,dst_name in [
            ("ENTRYPOINT_REGISTRY.json","ENTRYPOINT_REGISTRY.json"),
            ("UPGRADE_COVERAGE.md","UPGRADE_COVERAGE.md"),
            ("DELIVERY_MANIFEST.json","DELIVERY_MANIFEST_PREPARED.json"),
        ]:
            shutil.copy2(package_root()/src_name,run_dir/dst_name)

        # protected byte check after tests
        after_map={r["path"]:r for r in inventory(repo,protected_paths)}
        for r in protected_before:
            a=after_map[r["path"]]
            if a["sha256"]!=r["sha256"] or a["git_blob_sha"]!=r["git_blob_sha"]:
                raise RuntimeError(f"protected file changed after validation: {r['path']}")

        # stage exact scoped working tree
        subprocess.run(["git","add","-A","--",
            "README.md","START_CODES.md","docs/REPOSITORY_STRUCTURE.md","tests/TEST_PLAN_CURRENT.md",
            "archive/programs","provenance/cleanup"
        ],cwd=repo,check=True)
        # old move paths are already represented by git mv
        cp=run(repo,"diff","--cached","--check",check=False)
        if cp.returncode:
            raise RuntimeError("git diff --cached --check failed\n"+cp.stdout+cp.stderr)

        # generate exact binary-safe patch as a local run artifact (not staged)
        patch_path=run_dir/"APPLIED.patch"
        with patch_path.open("wb") as f:
            subprocess.run(["git","diff","--cached","--binary"],cwd=repo,stdout=f,check=True)
        subprocess.run(["git","add","--",patch_path.relative_to(repo).as_posix()],cwd=repo,check=True)

        print("CLEANUP_APPLIED_AND_STAGED")
        print(f"run_record={run_dir.relative_to(repo)}")
        print("No commit or push was performed.")
    except Exception:
        print("APPLY_FAILED: attempting scoped rollback",file=sys.stderr)
        rollback(repo,strict=False)
        raise

def preview(repo: Path):
    repo=guard(repo)
    print("PREVIEW_OK")
    print(f"repository=Morfindien/bubbleverse-model")
    print(f"base_sha={BASE}")
    print(f"archive_moves={len(MOVES)}")
    for m in MOVES:
        print(f"ARCHIVE {m['old_path']} -> {m['new_path']}")
    for d in DEFERRED:
        print(f"DEFER {d['path']}: {d['reason']}")
    print("No files changed.")

def rollback(repo: Path, strict=True):
    repo=repo.resolve()
    # Only permit rollback in the expected repository.
    if not (repo/".git").exists() or not origin_ok(git(repo,"config","--get","remote.origin.url")):
        raise RuntimeError("wrong repository for rollback")
    # Unstage only cleanup-known surfaces; clean-start is required by apply.
    known=["README.md","START_CODES.md","docs/REPOSITORY_STRUCTURE.md","tests/TEST_PLAN_CURRENT.md","archive/programs","provenance/cleanup"]
    for m in MOVES:
        known.extend([m["old_path"],m["new_path"]])
    run(repo,"reset","HEAD","--",*known,check=False)

    # Reverse archive paths where destination exists and original does not.
    for m in reversed(MOVES):
        old=repo/m["old_path"]; new=repo/m["new_path"]
        if new.exists() and not old.exists():
            old.parent.mkdir(parents=True,exist_ok=True)
            shutil.move(str(new),str(old))
    # Restore tracked mutable docs from BASE.
    for rel in ["README.md","tests/TEST_PLAN_CURRENT.md"]:
        data=subprocess.check_output(["git","show",f"{BASE}:{rel}"],cwd=repo)
        (repo/rel).write_bytes(data)
    # Remove added cleanup files/directories only.
    for rel in ["START_CODES.md","docs/REPOSITORY_STRUCTURE.md","archive/programs"]:
        p=repo/rel
        if p.is_dir(): shutil.rmtree(p)
        elif p.exists(): p.unlink()
    run_dir=repo/"provenance/cleanup"/RUN_ID
    if run_dir.exists(): shutil.rmtree(run_dir)
    # INDEX may preexist; if newly created and only contains this run, remove.
    idx=repo/"provenance/cleanup/INDEX.md"
    if idx.exists():
        txt=idx.read_text()
        if txt.strip()==f"# Cleanup Memory Index\n\n- `{RUN_ID}` — Q045–Q048 retired-installer archive cleanup; see `{RUN_ID}/RUN_MANIFEST.json`.":
            idx.unlink()
        else:
            lines=[ln for ln in txt.splitlines() if RUN_ID not in ln]
            idx.write_text("\n".join(lines).rstrip()+"\n")
    if strict and git(repo,"status","--porcelain","--untracked-files=all"):
        raise RuntimeError("scoped rollback left changes; inspect manually")
    print("SCOPED_ROLLBACK_COMPLETE")

def self_test():
    # No repository required: validate path safety, uniqueness and archive shape.
    olds=set(); news=set()
    for m in MOVES:
        safe_rel(m["old_path"]); safe_rel(m["new_path"])
        assert m["old_path"] not in olds
        assert m["new_path"] not in news
        olds.add(m["old_path"]); news.add(m["new_path"])
        assert m["new_path"].startswith("archive/programs/")
        assert "/payload/" in m["new_path"]
        assert m["git_blob_sha"] and len(m["git_blob_sha"])==40
    assert len(MOVES)==8
    print("PACKAGE_SELF_TEST=PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",default=".")
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--preview",action="store_true")
    g.add_argument("--apply",action="store_true")
    g.add_argument("--rollback",action="store_true")
    g.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test: return self_test()
    repo=Path(a.repo)
    if a.preview: return preview(repo)
    if a.apply: return apply(repo)
    if a.rollback: return rollback(repo)

if __name__=="__main__":
    main()
