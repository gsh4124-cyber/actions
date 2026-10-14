#!/usr/bin/env python3
"""Odd Factory V6 fail-closed release gate; PASS never publishes itself."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--validation', default='output/validation.json')
    parser.add_argument('--visual', default='output/visual_qa.json')
    parser.add_argument('--approval', default='output/publish_approval.json')
    parser.add_argument('--video', default='output/odd_factory_v6.mp4')
    args = parser.parse_args()
    try:
        video = pathlib.Path(args.video)
        assert video.is_file() and video.stat().st_size > 0, 'Final MP4 missing'
        sha = hashlib.sha256(video.read_bytes()).hexdigest()
        technical = json.loads(pathlib.Path(args.validation).read_text())
        visual = json.loads(pathlib.Path(args.visual).read_text())
        approval = json.loads(pathlib.Path(args.approval).read_text())
        assert technical.get('status') == 'TECHNICAL_PASS', 'Technical QA missing'
        assert technical.get('video_sha256') == sha, 'Technical QA references different video'
        probe = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)
        ], stderr=subprocess.STDOUT, timeout=20))
        streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'video']
        assert streams, 'Video stream missing'
        stream = streams[0]
        assert (stream.get('width'), stream.get('height')) == (1080, 1920), 'Invalid vertical dimensions'
        assert stream.get('r_frame_rate') == '30/1', 'Invalid video fps'
        duration = float(probe['format']['duration'])
        assert 9.9 < duration < 10.1, 'Invalid duration'
        assert abs(float(technical.get('duration', -100)) - duration) < 0.1, 'Technical duration mismatch'
        assert visual.get('status') == 'PASS', 'Independent Commercial QA missing'
        score = visual.get('score')
        assert type(score) in (int, float) and score >= 90, 'Commercial QA score below 90'
        assert visual.get('reviewed_actual_video') is True, 'Actual video not reviewed'
        assert visual.get('video_sha256') == sha, 'Visual QA references different video'
        assert visual.get('reviewer') and visual.get('evidence'), 'Visual QA evidence missing'
        assert approval.get('status') == 'APPROVED', 'Video-specific publish approval missing'
        assert approval.get('scope') == 'THIS_VIDEO', 'Only exact-version approval allowed'
        assert approval.get('channel') == 'oddfactory', 'Target channel mismatch'
        assert approval.get('video_sha256') == sha, 'Approval references different video'
        assert approval.get('approved_by') and approval.get('evidence'), 'Approval proof missing'
    except (OSError, ValueError, KeyError, AssertionError, subprocess.SubprocessError) as exc:
        print('RELEASE_BLOCKED:', str(exc))
        return 1
    print('RELEASE_GATE_PASS_NOT_PUBLISHED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
