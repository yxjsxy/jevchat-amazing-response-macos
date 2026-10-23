from pathlib import Path
import subprocess,os,signal,time,shutil,json
r=Path(__file__).resolve().parents[1];app=Path.home()/'Applications/Jev Amazing.app'
exe=str(app/'Contents/MacOS/jev-amazing')
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
 bits=line.strip().split(None,1)
 if len(bits)==2 and bits[1]==exe:os.kill(int(bits[0]),signal.SIGTERM)
time.sleep(1)
meta=json.loads((r/'.local/app-build.json').read_text());new=Path(meta['app_path'])
if meta.get('payload_path'):
 current=Path.home()/'Library/Application Support/Jev Amazing/app/current';temp=current.with_name('current.next')
 temp.unlink(missing_ok=True);temp.symlink_to(Path(meta['payload_path']).name);temp.replace(current)
if not(meta.get('reused_installed_signature') and app.exists()):
 if app.exists():shutil.rmtree(app)
 app.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(new,app)
subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True,timeout=15)
print('Installed and signature verified')
