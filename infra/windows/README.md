# Windows 자체 실행기 준비와 로컬 대체 경로

상태: 로컬 Python 검증 실행 가능. 자체 실행기는 설치·등록·기동하지 않았으며 Online(온라인) 상태는 확인하지 못했다. 상시 서비스·예약작업을 만들지 않았다. 기존 Excel 실행기를 수정하지 않았다. 추가 비용을 발생시키는 서비스를 신청하지 않았다.

## 먼저 로컬 테스트

전체 원본을 받을 수 있는 인증된 환경에서 저장소를 복제한다. Vault 정본은 hwangje-vault다.

```powershell
git clone --branch codex/windows-qa-recovery-20261016 https://github.com/gsh4124-cyber/hwangje-vault.git hwangje-vault
Set-Location hwangje-vault
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pillow==11.3.0 pytest==8.4.2 PyYAML==6.0.3 matplotlib==3.10.7
.\.venv\Scripts\python.exe -c "import matplotlib,pathlib,shutil; [shutil.copyfile(pathlib.Path(matplotlib.get_data_path())/'fonts/ttf'/name,name) for name in ('DejaVuSans.ttf','DejaVuSans-Bold.ttf')]"
```

FFmpeg/FFprobe는 [FFmpeg 공식 Windows 안내](https://ffmpeg.org/download.html#build-windows)가 연결하는 빌드를 사용한다. 이번 실행은 Gyan `ffmpeg-release-essentials.zip`과 함께 배포된 SHA256을 대조한 9.0.2로 수행했다. 두 실행파일의 디렉터리를 현재 셸 PATH에 추가한다. 이 검사는 도구를 설치해 시스템 PATH를 영구 변경하지 않는다.

```powershell
$env:PATH='C:\전용환경\ffmpeg\bin;'+$env:PATH
.\.venv\Scripts\python.exe scripts/local_regression.py --root . --output ..\vault-qa-results
.\.venv\Scripts\python.exe scripts/harness_regression.py
.\.venv\Scripts\python.exe scripts/harness_audit.py --mutation-test --changed scripts/skill_bootstrap.py .github/workflows/harness-regression.yml
.\.venv\Scripts\python.exe scripts/shopping_asset_guard.py --root .
```

결과 폴더는 저장소 밖에 둔다. 심볼릭 링크 생성 권한이 없으면 관련 검사 1건이 BLOCKED(환경 차단)이며 종료코드는 0이 아니다. 검사 통과를 위해 관리자 계정으로 실행하거나 권한 경계를 약화하지 않는다. 완전한 원본 PNG를 받지 못하면 실제 자산 검사를 PASS(통과)로 보고하지 않는다. 이 테스트들은 코드·계약·파일 검증이며 LLM(언어 모델)의 판단능력이나 실제 마케팅 성과를 자동 인증하지 않는다.

## 자체 실행기가 필요한 경우에만

로컬 수동 검증에는 자체 실행기가 필요하지 않다. GitHub에서 반복 실행을 받아야 한다면 개인 파일·브라우저 세션·고객정보·기존 인증정보가 없는 **별도 일회용 Windows x64 환경과 일반 계정**을 먼저 확보한다. 현재 PC의 별도 폴더만으로는 보안 격리가 성립하지 않는다. 격리가 없으면 등록과 기동을 진행하지 않는다.

준비 스크립트는 공식 Runner(실행기) 2.338.0을 다운로드하고 공식 릴리스의 SHA256을 확인한 뒤 압축만 푼다. GitHub CLI의 비공개 저장소 읽기 확인이 필요하다. PAT·토큰을 스크립트나 명령 기록에 넣지 않는다.

```powershell
.\prepare_windows_runner.ps1 -RunnerDirectory "$env:LOCALAPPDATA\HwangjeQaRunner" -DedicatedEnvironmentConfirmed
```

스크립트 출력의 등록 명령을 해당 전용 환경에서만 따른다. 등록용 1시간 토큰은 [Vault 실행기 설정](https://github.com/gsh4124-cyber/hwangje-vault/settings/actions/runners/new)에서 발급하고 `Read-Host -AsSecureString`으로 입력한다. `--ephemeral`은 작업 한 건 후 등록을 해제한다. 실행 환경 자체를 청소하는 보안 격리는 아니므로 종료 후 환경을 폐기한다. 서비스 설치·자동 시작은 사용하지 않는다. 진단 로그는 민감정보를 확인·제거한 뒤 보존한다.

제공한 `vault-windows-qa.yml`은 **설치하지 않은 수동 실행용 템플릿**이다. 전용 환경 준비 후 Vault의 `.github/workflows/`에 검토·통합할 수 있다. 라벨은 `[self-hosted, Windows, X64, hwangje-vault-qa]`이고 비공개 Vault의 main에 대한 수동 실행만 허용한다. 외부 PR·pull_request_target·push·예약 트리거가 없고 토큰 권한은 저장소 읽기뿐이다. 기존 Linux 워크플로의 게시·상태 커밋·운영 DB 단계는 실행하지 않는다. 따라서 이 경로가 기존 전체 Linux CI와 현장 검증을 완전히 대체했다고 주장하지 않는다.

공식 근거: [자체 실행기 추가](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners), [보안 경계](https://docs.github.com/en/enterprise-cloud@latest/actions/reference/security/secure-use), [일회용 실행기](https://docs.github.com/en/actions/reference/runners/self-hosted-runners), [사용한 공식 릴리스](https://github.com/actions/runner/releases/tag/v2.338.0).
