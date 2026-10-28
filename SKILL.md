---
name: bible-reading-motion-video
description: This skill should be used when the user provides a Korean Bible reading audio file (예 "롬8장.m4a", "창1장.mp3", 낭독 음성) and asks to make a YouTube motion-graphics video from it ("같은 방식으로 만들어줘", "성경 낭독 영상", "말씀 영상 만들어줘"). It keeps the original reader's voice, transcribes and aligns it to the 개역개정 text, inserts short AI narration bridges between paragraphs (TopView TTS 'Eunji'), generates biblical illustrations with codex-image (Codex CLI, gpt-image-2) and paragraph-specific narrative BGM with TopView, and renders a 1920×1080 30fps MP4 with Korean subtitles, kinetic typography, plus SRT/transcript/storyboard/narration-script documents.
---

# 성경 낭독 모션그래픽 영상 (로마서 시리즈 확정 방식)

낭독 음성 한 장(章)을 받아 다음을 만든다. 사용자가 만족을 확정한 구성이므로 그대로 따른다.
- 원본 낭독 목소리 유지(속도·음높이·내용 변경 금지). 단락 경계 무음에서 나눠 사이에 **AI 해설**(오프닝·전환·클로징)
- 장면별 시네마틱 일러스트 + 2.5D 카메라·빛·안개 + 키네틱 타이포(금빛 핵심 구절, 대비 도식, 도장, 구약 인용 칩)
- **단락별 맞춤 BGM**(음악만 들어도 본문 흐름이 느껴지게, 곡 안의 가라앉음·솟음을 핵심 구절에 맞춰 큐)
- 산출물(`{장}/`): `bible_motion_graphics.mp4`, `bible_subtitles.srt`, `bible_transcript.txt`, `bible_storyboard.md`, `bible_narration_script.md`, `bgm_only_N장.m4a`, `project/`

세부 기준(해설 원고 규칙, 그림 금지 항목, BGM 프롬프트 쓰는 법, 점검표)은 **`references/guidelines.md` 를 먼저 읽는다.** 실제 사례: `references/*_example.*` (로마서 8장).

## 준비물 확인
python(faster_whisper, playwright+chromium, numpy, PIL), ffmpeg/ffprobe, Codex CLI 0.123+ ChatGPT 로그인(`codex login status`, 이미지), TopView MCP(음악·음성). 질문으로 멈추지 말고 바로 시작한다. 진행 중 짧게 상황을 알린다.

`S=~/.claude/skills/bible-reading-motion-video/scripts` 로 두고, **모든 스크립트는 작업 폴더 안에서** `PYTHONIOENCODING=utf-8 python $S/xxx.py` 로 실행한다.

## 절차

### 1. 작업 폴더 준비 + 받아쓰기 (병렬로 시작)
```bash
python $S/setup_work.py --work work10 --audio 롬10장.m4a --book-ko 로마서 --book-en ROMANS --code rom --ch 10 --out 10장
cd work10 && (PYTHONIOENCODING=utf-8 nohup python $S/asr.py > asr.log 2>&1 &)
```
- 책 코드는 `references/book_codes.md`(요나서 jnh, 시편은 `--unit 편`). 이전 장 작업이 있으면 같은 시리즈로 이어 간다.
- setup_work.py 출력: 절·소제목·병합 절·난외주·무음 구간. 이것으로 **단락(낭독 구간)을 정한다**.

### 2. 에셋 제출 (받아쓰기를 기다리는 동안)
- 단락 구성에 맞춰 **BGM 4~5곡**을 TopView 에 제출(동시 한도 ~12). task id 를 `tasks.txt` 에 적어 둔다.
- **일러스트 10~16장**은 `prompts.json` 작성 → `(PYTHONIOENCODING=utf-8 nohup python $S/gen_images.py > img.log 2>&1 &)` (codex-image, 크레딧 없음, 장당 약 1분 → `img/NN_name.png`).
- 해설 원고 `narr.json` 작성 → 해설 음성 생성(voiceId·속도는 config.json). 결과 URL 을 curl 로 `bgm1.mp3…`, `tts/N0.mp3…` 에 받는다.
- `python $S/prep_images.py` → `img.log` 에 FAIL 없는지 확인 후 `img_grid.jpg` 를 Read 로 검수(금지 그림은 img/ 에서 지우고 gen_images.py 재실행). `python $S/musan.py bgm*.mp3` 로 곡 흐름 파악. `python $S/tts_check.py` 로 해설 길이·발음·문장 끝 확인.

### 3. 정렬과 자막
- `asr.log` 완료 확인 → 본문과 다르게 들린 곳은 `python $S/asr_check.py 시작-끝 …`(두 모델 모두 다르면 '낭독 확인 필요').
- `python $S/align.py` → 절별 시각 출력. `manual_split_draft.txt` 를 손봐 `manual_split.txt` 로 저장.
- `chapter.json` 작성(cuts·onsets·nsplit·parts·kw; `references/chapter_json_example.json`) → `python $S/subs.py`.

### 4. 연출과 점검
- `chapter_tl.py` 작성(장면 shots, 키네틱 이벤트 E(...), BGM 큐 bgm; `references/chapter_tl_example.py` 의 머리 주석 참고) → `python $S/build_tl.py` (index.html 까지 생성).
- `python $S/snap.py g1.jpg 시각…` 으로 전반·후반 각 6장 이상 캡처해 Read 로 점검(guidelines 6절). 고치고 다시 build.

### 5. 렌더·믹스·문서·마무리
```bash
python $S/render.py all          # 4분할 백그라운드. 진행: tail -qn1 r*.log (DONE 4개)
python $S/mix.py                 # 렌더 중에 실행: BGM 큐·더킹·-16 LUFS 자동 → mix.m4a, bgm_only
python $S/docs.py                # docs.json 작성 후 (references/docs_json_example.json)
python $S/finalize.py            # 합치기·디코딩 검증·final_grid.jpg·project 복사
```
- 렌더 대기는 Bash `timeout 590 bash -c 'while [ $(cat r*.log|grep -c DONE) -lt 4 ]; do sleep 15; done'` 를 반복. pgrep/pkill 금지.
- `final_grid.jpg` 를 Read 로 확인. 문제 구간만 `python $S/render.py A 끝 fix.mp4`(A·끝은 **프레임 번호** = 초×30, 끝은 전체 프레임 수) → `python $S/finalize.py --splice A`.

### 6. 보고 (한국어, 간결)
길이·해상도·용량·검증 결과, 단락별 연출과 BGM 흐름 표, TopView 크레딧(음악·음성), codex-image 생성 장수, **확인할 것**(낭독 확인 필요 구절, 다시 만든 그림과 이유, 해설 중 해석이 갈릴 수 있는 표현, 개역개정 소제목이 아닌 PART 제목), 다음 장 제안. 파일은 markdown 링크로.
