"""Install missing efficiency tools without changing host model/auth configuration.

Run with Python 3.10+. Downloads official RTK release artifacts with pinned SHA256,
Headroom from PyPI into a private venv, and Caveman from npm into a private prefix.
No model inference, lifecycle hooks, provider replacement or public listeners.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import venv
import zipfile

ROOT = Path.home() / ".agent-efficiency"
WINDOWS = os.name == "nt"
SUFFIX = ".exe" if WINDOWS else ""
RTK_ASSETS = {
    ("Linux", "x86_64"): ("rtk-x86_64-unknown-linux-musl.tar.gz", "7278231dfd7e6a730a4ab7f847b195bcf02289c2d57622b0dab75a6411100c8f"),
    ("Linux", "aarch64"): ("rtk-aarch64-unknown-linux-gnu.tar.gz", "c8ea4b6560841e73157c134fd4a3293914c6ede42e786ee985cf491fde691ba7"),
    ("Darwin", "arm64"): ("rtk-aarch64-apple-darwin.tar.gz", "bbbfebabb22686993a80da731aa4d5d35116fb8ae24abb00608efa028e13ae01"),
    ("Darwin", "x86_64"): ("rtk-x86_64-apple-darwin.tar.gz", "d297388f4a8a786e79abe5f55b80451725bfe8c5835b4736c05d7cff4d68f627"),
    ("Windows", "AMD64"): ("rtk-x86_64-pc-windows-msvc.zip", "cb971046598f0e8bd51f6c27780fcdd2c39a4c459a811bd95b0d77ba8c0d7c9f"),
}


def run(args, timeout=30):
    result = subprocess.run([str(a) for a in args], stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=timeout, shell=False)
    if result.returncode:
        # Package manager diagnostics may contain environment credentials.
        raise RuntimeError(f"{Path(str(args[0])).name} exited {result.returncode}; inspect locally")
    return result.stdout.strip()


def candidates(name):
    found = shutil.which(name)
    values = [Path(found)] if found else []
    if name == "rtk":
        values += [Path.home() / ".local/bin" / (name + SUFFIX), ROOT / "bin" / (name + SUFFIX)]
    if name == "headroom":
        values += [ROOT / "headroom" / ("Scripts" if WINDOWS else "bin") / (name + SUFFIX)]
    if name == "caveman":
        values += [ROOT / "npm" / ("caveman.cmd" if WINDOWS else "bin/caveman")]
    return list(dict.fromkeys(values))


def discover(name):
    for path in candidates(name):
        if path.is_file():
            try:
                run([path, "--version"])
                return path
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                continue
    return None


def extract_rtk(data, asset, digest):
    if hashlib.sha256(data).hexdigest() != digest:
        raise RuntimeError("RTK archive SHA256 mismatch; nothing executed")
    binary_name = "rtk.exe" if asset.endswith(".zip") else "rtk"
    if asset.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = [m for m in archive.infolist() if Path(m.filename).name == binary_name and not m.is_dir()]
            if len(members) != 1:
                raise RuntimeError("Unexpected RTK archive layout")
            return archive.read(members[0])
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = [m for m in archive.getmembers() if Path(m.name).name == binary_name and m.isfile()]
        if len(members) != 1:
            raise RuntimeError("Unexpected RTK archive layout")
        return archive.extractfile(members[0]).read()


def install_rtk():
    key = (platform.system(), platform.machine())
    if key not in RTK_ASSETS:
        raise RuntimeError(f"No reviewed RTK artifact for {key}")
    asset, digest = RTK_ASSETS[key]
    url = "https://github.com/rtk-ai/rtk/releases/download/v0.49.0/" + asset
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(80 * 1024 * 1024 + 1)
    if len(data) > 80 * 1024 * 1024:
        raise RuntimeError("RTK archive exceeds size limit")
    binary = extract_rtk(data, asset, digest)
    target = ROOT / "bin" / ("rtk" + SUFFIX)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as tmp:
        tmp.write(binary)
        staged = Path(tmp.name)
    try:
        staged.chmod(0o755)
        os.replace(staged, target)
    finally:
        staged.unlink(missing_ok=True)


def install_headroom():
    target = ROOT / "headroom"
    venv.EnvBuilder(with_pip=True).create(target)
    python = target / ("Scripts/python.exe" if WINDOWS else "bin/python")
    run([python, "-m", "pip", "install", "--disable-pip-version-check", "--index-url",
         "https://pypi.org/simple", "headroom-ai[proxy,mcp]==0.42.0"], timeout=900)


def install_caveman():
    node, npm = shutil.which("node"), shutil.which("npm.cmd" if WINDOWS else "npm")
    if not node or not npm:
        raise RuntimeError("Caveman requires Node.js >=22.13 and npm on this executor")
    version = tuple(int(p) for p in run([node, "--version"]).lstrip("v").split(".")[:2])
    if version < (22, 13):
        raise RuntimeError("Caveman requires Node.js >=22.13 on this executor")
    run([npm, "install", "--global", "--prefix", ROOT / "npm", "--ignore-scripts",
         "--no-audit", "--no-fund", "--registry=https://registry.npmjs.org",
         "@caveman-ai/cli@4.0.1"], timeout=300)


def ensure(check=False):
    report = {"schema": 1, "tools": {}, "integration": "not_verified", "model_test_calls": 0}
    for name, installer in [("rtk", install_rtk), ("headroom", install_headroom), ("caveman", install_caveman)]:
        try:
            path = discover(name)
            installed = False
            if not path and not check:
                installer()
                installed = True
                path = discover(name)
            if not path:
                raise RuntimeError("Missing or unusable executable")
            report["tools"][name] = {"status": "installed_now" if installed else "available", "path": str(path)}
            if name == "caveman":
                binary_dir = Path(os.environ.get("CAVEMAN_HOME", str(Path.home() / ".caveman"))) / "bin"
                required = [binary_dir / (n + SUFFIX) for n in ("caveman-proxy", "caveman-engine", "caveman-mcp")]
                if not all(p.is_file() for p in required) and not check:
                    # Official installer verifies the signed bin-v4.0.1 bundle.
                    # Never enable native integration or rewrite host providers.
                    run([path, "setup", "--install", "--json"], timeout=300)
                if not all(p.is_file() for p in required):
                    raise RuntimeError("Caveman companion binaries missing")
                for binary in required:
                    probe = json.loads(run([binary, "version", "--json"]))
                    if not probe.get("version"):
                        raise RuntimeError("Caveman companion version probe failed")
                report["tools"][name]["companions"] = "available"
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            report["tools"][name] = {"status": "blocked", "reason": str(exc)}
    report["installation_ready"] = all(x["status"] != "blocked" for x in report["tools"].values())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Inspect only; do not install missing tools")
    parser.add_argument("--exec", dest="execute", nargs=argparse.REMAINDER,
                        help="Run rtk/headroom/caveman through the resolved executable")
    args = parser.parse_args()
    if args.execute and args.execute[0] not in ("rtk", "headroom", "caveman"):
        parser.error("--exec must select rtk, headroom or caveman")
    ROOT.mkdir(parents=True, exist_ok=True)
    # Exclusive lock avoids parallel sessions modifying the same user installation.
    lock = ROOT / "install.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        print(json.dumps({"installation_ready": False, "reason": "Installation lock exists; retry after the other session, or inspect stale lock ownership"}))
        return 2
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(str(os.getpid()))
        report = ensure(args.check)
        # Keep machine paths outside Git. No credentials or model responses recorded.
        (ROOT / "last-status.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    finally:
        lock.unlink(missing_ok=True)
    if args.execute:
        tool = report["tools"][args.execute[0]]
        if tool["status"] == "blocked":
            print(json.dumps(tool))
            return 2
        return subprocess.call([tool["path"], *args.execute[1:]], shell=False)
    print(json.dumps(report, indent=2))
    return 0 if report["installation_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
