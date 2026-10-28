# 제작 지침 (로마서 1–9장 제작 경험에서 확정된 기준)

사용자가 만족을 명시한 구성: AI 해설 브리지, 'Eunji' 해설 음성, 본문 장면에 밀착한 일러스트, **단락별 맞춤 BGM(음악만 들어도 본문 흐름이 느껴지게)**.

## 1. 해설(AI 나레이션)

- 위치: 오프닝 1 + 단락 전환마다 1 + 클로징 1 (한 장 4~7회). 낭독 구간 수 + 1.
- 단락 나누기: 개역개정 소제목 우선(textinfo.json titles). 단락이 너무 길면(≈12절↑) 내용 전환점에서 더 나눈다. 너무 짧은 단락은 앞뒤에 붙인다.
- 원고: 1~2문장, **15초 이내**(넘으면 줄여서 다시 생성). 역사·문화 배경, 인물·지명, 흐름 안내, 개역개정 난외주(구약 인용 출처·사본 차이·다른 번역)만.
- 금지: 성경 구절을 해설 목소리로 다시 읽기/바꿔 인용, 설교, 적용, 감정 강요, 교파별 해석 판단. 해석이 갈리면 "해석이 갈립니다"까지만.
- 오프닝은 앞 장 흐름과 잇고, 클로징은 이 장 정리 + 다음 장 한 줄 예고.
- 숫자는 읽는 대로(TTS): "이십오 절", "시편 사십사 편". 자막(narr.json sub)은 아라비아 숫자.
- '이 장(=2장)'처럼 '이번 장'으로 들릴 표현은 피한다("앞선 이 장에서").
- narr.json 형식: `[{"id":"N0","text":"TTS 원고","sub":"자막 첫 줄|자막 둘째 줄"}, …]`
- 음성: TopView `topview_generate_voice`, voiceId `kKTntBsdDuheAZ0N6LTEVkDrAlQL7icT`('Eunji', 한국어 중년 여성), voiceSpeed 0.92, emotionName neutral. 낭독자가 여성이면 남성 음성(`topview_list_voices` gender=male, language=ko)으로 바꾼다.
- 결과 조회: `topview_query_task` taskType `text_to_speech` → `voice.demoAudioUrl` 을 `curl -sSL -o tts/N0.mp3 URL`.
- 발음이 틀리면 `pronRules: [{"oldStr":"죽으심","newStr":"주그심"}]` 로 다시 생성. tts_check.py 로 검수(인식기가 '계명→개명'처럼 표준 발음대로 적는 건 정상).
- Edge TTS 는 403으로 막혀 있음(쓰지 않음).

## 2. 일러스트

- **codex-image 로 생성**(gpt-image-2, ChatGPT 로그인, TopView 크레딧 0). TopView 이미지 생성은 쓰지 않는다.
- 작업 폴더에 `prompts.json`(`{"01_name": "프롬프트", ...}`)을 Write 로 작성 → `nohup python $S/gen_images.py > img.log 2>&1 &`. 한 장씩 차례로(장당 약 1분) `img/NN_name.png`(1536×1024)에 저장, 있는 파일은 건너뜀. 다시 만들 그림은 img/ 에서 지우고 재실행.
- Codex 실행은 반드시 `codex exec --sandbox read-only --skip-git-repo-check -`(스크립트에 들어 있음). `--dangerously-bypass-approvals-and-sandbox` 금지.
- `img.log` 에 FAIL 이 있으면 `codex login status` 확인 후 재실행. `prep_images.py` 가 가운데를 16:9 로 잘라 2400×1347 JPG 로 `imgs/` 에 만든다 → 프롬프트에 `centered composition` 을 넣어 핵심 소재가 잘리지 않게 한다.
- 한 장에 새 그림 10~16장 + 이전 장 그림 재사용 가능(빈 십자가, 빈 무덤, 해돋이, 율법 돌판 등).
- 프롬프트 공통 꼬리: `Cinematic biblical digital painting: … deep blue shadows and gold, beige palette, painterly, highly detailed, wide composition, no text, no watermark` (+ 필요하면 `no people`, `no readable text`).
- 장면 원칙: 본문이 직접 묘사한 장면 우선, 추상 개념은 상징(덫, 저울, 베틀, 사슬, 씨앗 등). 1세기 근동·그리스·로마 고증 분위기.
- **검수 후 다시 생성할 것**:
  - 하나님 / 예수님 / 천사처럼 보이는 인물(빛나는 형상, 긴 머리·흰 옷의 뒷모습) — 하나님은 빛·자연으로, 예수님은 빈 십자가·빈 무덤으로만
  - 시대에 안 맞는 것: 바위 돔·모스크·교회 첨탑(→ "Herodian Second Temple, no domes"), 로마 독수리 도장, 근대 물건
  - 정치적 상징(망치+낫 등), 선정적·폭력적 묘사
  - 에덴의 두 사람은 옷을 입힌 뒷모습으로
- 그림 속 '나'(7장처럼 일인칭)는 특정 인물(바울)로 보이지 않게 평범한 1세기 사람으로.

## 3. BGM — 단락별 맞춤, 음악만으로 흐름이 보이게

- 단락마다 1곡(한 장 4~5곡). `topview_generate_music` model "Topview Music", instrumental true, enhancePrompt true, 곡당 1크레딧, 길이 약 2.5~4분.
- `styles`: 악기·분위기·템포(예: `cinematic chamber strings and piano, tender then solemn, 64 bpm, no drums, no vocals`).
- `lyrics`: **그 단락의 서사를 음악 언어로**: "Part 1: … Part 2: … Part 3: …" 처럼 시간 순서의 변화(가라앉음·고조·침묵·해결)를 묘사. 예) 6장 세례 단락: 질문하는 피아노 → 물속·무덤처럼 가장 낮게 가라앉음 → 한 음에서 새 생명처럼 떠오름.
- 받은 곡은 `musan.py` 로 4초 단위 음량/밝기를 보고 '가라앉는 곳', '솟는 곳'을 찾는다.
- chapter_tl.py 의 `bgm=[[영상초, 파일, 원곡초, "설명"], …]` 로 본문 핵심 낱말 직전(-1~-3초)에 그 부분이 오게 큐를 건다. 같은 곡 안에서 앞뒤로 오가도 된다(본문이 가라앉음↔피어남을 되풀이할 때).
- 마지막 큐가 끝까지 이어질 만큼 원곡이 남았는지 확인(mix.py 가 모자라면 경고).
- mix.py 가 BGM 크기를 낭독 음량 기준으로 자동 정규화(bgm_ratio 0.58 ≈ 발화 중 낭독보다 14~15dB 낮음). 출력 줄의 간격을 확인.
- BGM 전용 파일 `bgm_only_N장.m4a` 를 함께 준다. 이용 조건 확인 안내.

## 4. 자막·본문

- 본문은 반드시 대한성서공회 개역개정 페이지에서 받은 것(setup_work.py). 자막은 본문 그대로.
- manual_split.txt: `절|줄1|줄2…` 한 줄에 34자 이하, 의미 단위(연결어미 뒤)에서 끊는다. setup_work.py 가 만든 draft 를 손본다.
- 낭독자가 본문과 다르게 읽은 듯한 곳: asr_check.py 로 두 모델이 **모두** 다르게 들으면 '낭독 확인 필요'로 transcript 에 기록(자동 수정 금지, 자막은 본문대로). 한 모델만 다르면 인식 오류.
- 낭독자가 구절을 반복해 읽었으면 원본은 자르지 않고 chapter.json extra_subs 로 반복 줄을 넣고 보고.
- 끝의 '아멘'이 인식에서 빠지면 음량 곡선으로 위치를 찾아 chapter.json amen=[시작,끝].
- 단락 분할 직후 절의 첫 자막이 앞에 붙으면 chapter.json onsets 에 그 절의 시작 시각(무음 끝)을 넣는다.

## 5. 화면 연출 (chapter_tl.py)

- 장면(shots) 전환은 해설 시작 시점과 본문 내용이 바뀌는 구절 시작(-0.4초)에. 해설 구간에는 다음 단락의 그림을 미리 보여 준다.
- 핵심 구절: hero(금빛, glow=1), 대비 구조: dual(왼쪽=옛것·죄·사망은 DULL/EMB 색, 오른쪽=금색), 열거: stack/list/sins, 반복 표현(ΜΗ ΓΕΝΟΙΤΟ 등): stamp, 구약 인용: cite(개역개정 난외주 출처).
- hero 는 하단 자막을 숨긴다(hide=1). 화면 가운데 요소는 겹치지 않게 자동 정리됨.
- 금색 강조(kw)는 장의 핵심어 8~12개.

## 6. 점검 체크리스트 (렌더 전 snap.py, 렌더 후 finalize.py 격자)

- 글자가 배경(밝은 그림)에 묻히지 않는가, 한 글자만 다음 줄로 넘어가지 않는가
- 해설 구간 장·절이 흐려지고 'NARRATION' 표시가 나오는가, 스팅어 제목이 맞는가
- 그림과 그 순간의 구절이 맞는가(전환 시점), 금지 그림이 없는가
- 엔딩 요약 칩이 화면 안에 다 들어오는가(PART 5개 이상이면 꼭 확인 — 템플릿은 줄바꿈 처리됨)
- 오디오: 발화 중 낭독-BGM 간격 14~15dB, 최종 -16 LUFS, 해설과 낭독이 겹치지 않음

## 7. 운영 팁

- 렌더는 4분할 병렬로 약 1~3fps/프로세스: 4~6분 영상에 25~50분. 같은 PC에서 다른 렌더가 돌면 더 느려진다. **남의 render.py 프로세스를 죽이지 말 것**(pgrep/pkill 금지).
- 렌더가 도는 동안 mix.py, docs.json·docs.py 를 진행한다.
- Git Bash heredoc 안에 Python 을 쓰면 `\n`·따옴표가 깨지기 쉽다 → 장별 파일(chapter_tl.py, docs.json, narr.json)은 Write 도구로 작성.
- Windows 콘솔 한글: `PYTHONIOENCODING=utf-8` 를 붙여 실행.
- 문제 구간만 고칠 때: `python render.py A 끝 fix.mp4` → `python finalize.py --splice A`.
- TopView 크레딧 한 장 대략: 음악 5곡 5 + 해설 6개 0.6 ≈ 6 (이미지는 codex-image 라 크레딧 없음, 14장 약 15분).
