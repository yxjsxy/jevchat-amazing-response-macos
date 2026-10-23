from pathlib import Path
import subprocess,shutil,plistlib,json,tempfile,hashlib,os
r=Path(__file__).resolve().parents[1];support=Path.home()/'Library/Application Support/Jev Amazing';venv=support/'venv'
if not(venv/'bin/python').exists():raise SystemExit('Install documented Python3.12 cloud runtime first')
# Versioned external Python payloads keep the bundle's code signature unchanged.
h=hashlib.sha256()
files=sorted(p for p in (r/'src').rglob('*.py') if '__pycache__' not in p.parts)
for p in files:h.update(str(p.relative_to(r)).encode());h.update(p.read_bytes())
payload=support/'app'/h.hexdigest()[:16]
if not payload.exists():
 payload.mkdir(parents=True);shutil.copytree(r/'src',payload/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for name in ['LICENSE','NOTICE','README.md','requirements-macos-cloud.txt']:shutil.copy2(r/name,payload/name)
installed=Path.home()/'Applications/Jev Amazing.app'
app=Path(tempfile.mkdtemp(prefix='jev-amazing-build-'))/'Jev Amazing.app'
marker='stable-external-python-v1'
reuse=False
if (installed/'Contents/Info.plist').exists():
 info=plistlib.loads((installed/'Contents/Info.plist').read_bytes());reuse=info.get('JEVLauncherSchema')==marker
if reuse:
 subprocess.run(['codesign','--verify','--deep','--strict',str(installed)],check=True,timeout=15);shutil.copytree(installed,app)
else:
 res=app/'Contents/Resources';mac=app/'Contents/MacOS';res.mkdir(parents=True);mac.mkdir()
 icon=r/'packaging/AmazingAppIcon.icns'
 if icon.exists():shutil.copy2(icon,res/'AppIcon.icns')
 for name in ['LICENSE','NOTICE']:shutil.copy2(r/name,res/name)
 info={'CFBundleName':'Jev Amazing','CFBundleDisplayName':'Jev Amazing 神回复','CFBundleIdentifier':'local.jev.amazing.response','CFBundleVersion':'0.6.2','CFBundleShortVersionString':'0.6.2','CFBundleExecutable':'jev-amazing','CFBundlePackageType':'APPL','LSMinimumSystemVersion':'13.0','NSHighResolutionCapable':True,'CFBundleIconFile':'AppIcon','LSUIElement':False,'NSScreenCaptureUsageDescription':'仅点击时读取当前微信聊天区域。裁剪图片和文字会发往你配置的视觉与回复模型，不持续录屏、不自动发送。','JEVLauncherSchema':marker,'JEVFork':'Amazing Response local modification'}
 (app/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
 (res/'launcher.zsh').write_text('''#!/bin/zsh
set -euo pipefail
SUPPORT="$HOME/Library/Application Support/Jev Amazing"
export JEV_AMAZING_CONFIG="$SUPPORT/config"
export PYTHONDONTWRITEBYTECODE=1 JEV_TARGET_APP=wechat
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
export HF_HUB_DISABLE_TELEMETRY=1 USE_TF=0
mkdir -p "$HOME/Library/Logs"
exec "$SUPPORT/venv/bin/python" -B "$SUPPORT/app/current/src/hud.py" >>"$HOME/Library/Logs/jev-amazing.log" 2>&1
''');(res/'launcher.zsh').chmod(0o755)
 subprocess.run(['clang','-O2','-arch','arm64','-mmacosx-version-min=13.0',str(r/'packaging/launcher.c'),'-o',str(mac/'jev-amazing')],check=True,timeout=30)
 for attr in ['com.apple.FinderInfo','com.apple.ResourceFork']:subprocess.run(['xattr','-dr',attr,str(app)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
 subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True,timeout=20)
subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True,timeout=15)
(r/'.local').mkdir(exist_ok=True)
(r/'.local/app-build.json').write_text(json.dumps({'app_path':str(app),'payload_path':str(payload),'stable_launcher':True,'reused_installed_signature':reuse,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip(),'runtime':str(venv),'signing':'ad-hoc immutable launcher; versioned external Python payload'},indent=2))
print('Built stable launcher; reused signature:',reuse,'payload:',payload.name)
