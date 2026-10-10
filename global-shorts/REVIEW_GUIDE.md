# Odd Factory V6 실제 영상 검수

실제 MP4를 재생하고 다음 항목을 검사한다.

- 기어 9쌍이 화면 안에 완전히 보이는가
- 톱니의 맞물림과 회전 방향이 설득력 있는가
- 가운데 한 쌍의 오류가 다른 정상 쌍과 구별되는가
- 10초 동안 화면이 읽히며 집중을 유지하는가
- 1080×1920 영상의 금속 질감과 조명이 충분한가
- 글자, 색상, 정답 공개 등 게시 기준을 충족하는가

검수자가 실제 파일을 확인한 뒤 `output/visual_qa.json`에 아래 구조로 기록한다.

```json
{
  "status": "PASS",
  "score": 90,
  "reviewed_actual_video": true,
  "reviewer": "검수자 식별자",
  "evidence": "실제 확인한 영상 및 검수 기록 위치"
}
```

위 예시는 형식 안내일 뿐 실제 합격 기록이 아니다. 미검증이면 파일을 만들지 않거나 status를 FAIL로 둔다. 게시 전 `python3 global-shorts/validate_release.py`를 실행한다.
