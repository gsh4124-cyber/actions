#!/usr/bin/env python3
"""Fail-closed V6 gate regression tests; synthetic receipts are fixtures only."""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

GATE = Path(__file__).with_name('validate_release.py')


def run(case, folder, validation, visual, approval, media, expected):
    technical_file = folder / 'technical.json'
    visual_file = folder / 'visual.json'
    approval_file = folder / 'approval.json'
    for p, v in ((technical_file, validation), (visual_file, visual), (approval_file, approval)):
        if v is None:
            p.unlink(missing_ok=True)
        else:
            p.write_text(json.dumps(v))
    cmd = [sys.executable, str(GATE), '--validation', str(technical_file),
           '--visual', str(visual_file), '--approval', str(approval_file), '--video', str(media)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    assert (r.returncode == 0) == expected, f'{case}: {r.returncode}: {r.stdout} {r.stderr}'
    print(f'{case}: PASS')


with tempfile.TemporaryDirectory() as directory:
    p = Path(directory)
    mp4 = p / 'fixture.mp4'
    # Small, synthetic 10-second valid MP4; NOT an actual commercial quality approval.
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi',
                    '-i', 'color=black:s=1080x1920:r=30:d=10', '-an', '-threads', '2',
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '35', '-pix_fmt', 'yuv420p',
                    str(mp4)], check=True, timeout=60)
    digest = hashlib.sha256(mp4.read_bytes()).hexdigest()
    tech = {'status': 'TECHNICAL_PASS', 'video_sha256': digest, 'duration': 10.0}
    qa = {'status': 'PASS', 'score': 90, 'reviewed_actual_video': True, 'reviewer': 'FIXTURE',
          'evidence': 'SYNTHETIC_TEST_ONLY', 'video_sha256': digest}
    approval = {'status': 'APPROVED', 'scope': 'THIS_VIDEO', 'channel': 'oddfactory',
                'video_sha256': digest, 'approved_by': 'FIXTURE', 'evidence': 'SYNTHETIC_TEST_ONLY'}
    run('missing technical QA', p, None, qa, approval, mp4, False)
    run('missing visual QA', p, tech, None, approval, mp4, False)
    run('missing publish approval', p, tech, qa, None, mp4, False)
    run('unreviewed video', p, tech, {**qa, 'reviewed_actual_video': False}, approval, mp4, False)
    run('score below 90', p, tech, {**qa, 'score': 89}, approval, mp4, False)
    run('technical digest mismatch', p, {**tech, 'video_sha256': '0'*64}, qa, approval, mp4, False)
    run('visual digest mismatch', p, tech, {**qa, 'video_sha256': '0'*64}, approval, mp4, False)
    run('approval digest mismatch', p, tech, qa, {**approval, 'video_sha256': '0'*64}, mp4, False)
    run('approval target mismatch', p, tech, qa, {**approval, 'channel': 'other'}, mp4, False)
    run('broad approval rejected', p, tech, qa, {**approval, 'scope': 'ALL_FUTURE'}, mp4, False)
    run('damaged MP4 rejected', p, tech, qa, approval, p/'nonexistent.mp4', False)
    fake = p/'fake.mp4'
    fake.write_bytes(b'0'*150000)
    fake_digest = hashlib.sha256(fake.read_bytes()).hexdigest()
    run('fake bytes despite receipts', p, {**tech, 'video_sha256': fake_digest},
        {**qa, 'video_sha256': fake_digest}, {**approval, 'video_sha256': fake_digest}, fake, False)
    run('synthetic fully documented fixture only', p, tech, qa, approval, mp4, True)
