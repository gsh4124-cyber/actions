#!/usr/bin/env python3
"""Regression tests for fail-closed publishing (미검증 게시 차단)."""
import json, pathlib, subprocess, sys, tempfile
from pathlib import Path
GATE=Path(__file__).with_name('validate_release.py')
def run(case,tech=None,visual=None,video=True,expected=1):
 with tempfile.TemporaryDirectory() as d:
  p=Path(d);v=p/'validation.json';q=p/'visual_qa.json';mp4=p/'video.mp4'
  if tech is not None:v.write_text(json.dumps(tech))
  if visual is not None:q.write_text(json.dumps(visual))
  if video:mp4.write_bytes(b'0'*100001)
  r=subprocess.run([sys.executable,str(GATE),'--validation',str(v),'--visual',str(q),'--video',str(mp4)],capture_output=True,text=True)
  assert (r.returncode==0)==(expected==0),f'{case}: unexpected exit {r.returncode}: {r.stdout} {r.stderr}'
  print(f'{case}: PASS')
goodtech={'status':'TECHNICAL_PASS'}
goodqa={'status':'PASS','score':90,'reviewed_actual_video':True,'reviewer':'human','evidence':'review-record'}
run('missing evidence',None,None)
run('missing visual QA',goodtech,None)
run('failed technical QA',{'status':'FAIL'},goodqa)
run('score below 90',goodtech,{**goodqa,'score':89})
run('video not reviewed',goodtech,{**goodqa,'reviewed_actual_video':False})
run('missing actual MP4',goodtech,goodqa,False)
run('complete documented QA',goodtech,goodqa,True,0)
