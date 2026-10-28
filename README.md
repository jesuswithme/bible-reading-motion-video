# bible-reading-motion-video

한국어 성경 낭독 음성(예: `롬8장.m4a`)을 유튜브용 모션그래픽 영상(1920×1080, 30fps)으로 만드는 Claude Code 스킬입니다.

- 낭독자의 원래 목소리를 그대로 두고, 개역개정 본문에 맞춰 자막을 정렬합니다.
- 단락 사이에 짧은 AI 해설(배경·흐름 안내)을 넣습니다.
- 장면별 성경 일러스트와 단락별 맞춤 BGM을 만듭니다. 하나님·예수님을 인물로 그리지 않습니다.
- 산출물: 영상(MP4), SRT 자막, 낭독 대조본, 스토리보드, 해설 원고, BGM 전용 파일.

## 설치

```bash
git clone https://github.com/jesuswithme/bible-reading-motion-video ~/.claude/skills/bible-reading-motion-video
```

업데이트: `git -C ~/.claude/skills/bible-reading-motion-video pull`

## 필요한 것

- Python 패키지: `pip install faster-whisper playwright numpy pillow` 후 `python -m playwright install chromium`
- ffmpeg / ffprobe (PATH에 등록)
- Codex CLI 0.123 이상 + ChatGPT 로그인(그림 생성, TopView 크레딧 없음)
- TopView MCP 연결(음악·해설 음성 생성, 크레딧 사용)

## 사용

음성 파일이 있는 폴더에서 Claude Code를 열고 말합니다.

> 창1장.mp3 올렸어. 성경 낭독 영상으로 만들어줘

자세한 절차는 [SKILL.md](SKILL.md), 제작 기준은 [references/guidelines.md](references/guidelines.md)를 보세요.

## 참고

- 성경 본문은 대한성서공회 개역개정(bskorea.or.kr)에서 가져옵니다. 본문과 생성된 그림·음악의 이용 조건은 각 제공처의 규정을 확인하세요.
