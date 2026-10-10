#!/usr/bin/env python3
"""Fail-closed release gate (검증 증거 없으면 게시 승인 차단)."""
import argparse, json, pathlib, sys
p=argparse.ArgumentParser()
p.add_argument('--validation',default='output/validation.json')
p.add_argument('--visual',default='output/visual_qa.json')
p.add_argument('--video',default='output/odd_factory_v6.mp4')
a=p.parse_args()
try:
    v=json.loads(pathlib.Path(a.validation).read_text())
    q=json.loads(pathlib.Path(a.visual).read_text())
    assert v.get('status')=='TECHNICAL_PASS','Technical checks not passed'
    assert q.get('status')=='PASS','Visual QA not passed'
    assert isinstance(q.get('score'),(int,float)) and q['score']>=90,'Score below 90'
    assert q.get('reviewed_actual_video') is True,'Actual video not reviewed'
    assert q.get('reviewer') and q.get('evidence'),'Reviewer or evidence missing'
    assert pathlib.Path(a.video).is_file() and pathlib.Path(a.video).stat().st_size>100000,'Video missing'
except (OSError,ValueError,AssertionError) as exc:
    print('RELEASE_BLOCKED (게시 차단):',exc)
    sys.exit(1)
print('RELEASE_APPROVED (게시 승인)')
