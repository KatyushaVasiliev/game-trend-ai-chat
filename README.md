# Game Pulse AI

게임/인디게임 관심도 시계열을 관리하고, 요약 정보를 GPT 시스템 프롬프트에 주입해 데이터 근거형 답변을 제공하는 서비스입니다. 처음 실행할 때 2016~2025년의 120개 데모 관측치를 제공합니다. Firebase 환경변수를 설정하면 동일한 `data`, `conversations` 컬렉션을 Firestore로 사용합니다.

## 기술 스택

- Backend: Python 3.10+, FastAPI, Pydantic, Uvicorn, Firebase Admin SDK, OpenAI Responses API
- Frontend: Vanilla HTML/CSS/JavaScript
- Deploy: Render (API), Vercel (static frontend)

## 배포 URL

배포 완료 후 실제 주소로 교체하세요.

- Frontend: `https://YOUR-PROJECT.vercel.app`
- Backend API: `https://YOUR-SERVICE.onrender.com`
- Swagger: `https://YOUR-SERVICE.onrender.com/docs`

Render 무료 인스턴스는 비활성 상태 뒤 첫 요청에 콜드 스타트 지연이 있을 수 있습니다. 화면에 안내 문구를 포함했습니다.

## 로컬 실행

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd game-trend-ai-chat
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
uvicorn app.main:app --app-dir backend --reload
```

다른 터미널에서 정적 프론트엔드를 실행합니다.

```powershell
cd frontend
py -m http.server 5500
```

브라우저에서 `http://127.0.0.1:5500` 및 `http://127.0.0.1:8000/docs`를 확인합니다.

## 환경 변수

| 변수 | 설명 |
| --- | --- |
| `OPENAI_API_KEY` | GPT 응답 생성을 위한 OpenAI API 키 |
| `OPENAI_MODEL` | 선택값, 기본 `gpt-4.1-mini` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | 서비스 계정 JSON 한 줄 또는 JSON 키 파일의 절대 경로 |
| `ALLOWED_ORIGINS` | 쉼표로 나눈 허용 프론트엔드 URL |
| `API_BASE_URL` | 프론트가 호출할 Render API 주소. 현재 `frontend/config.js`에서 설정 |

키는 `.env`와 Render/Vercel 환경 변수에만 넣고 커밋하지 않습니다. API 키가 없을 땐 시연을 위한 로컬 메모리 모드와 안내형 답변으로 동작하며, 배포/실서비스에서는 Firebase와 OpenAI 키를 반드시 설정합니다.

## Firestore 설계

```
data/{id}             { date, value, memo }
conversations/{id}    { title, messages: [{role, content, created_at}], created_at, updated_at }
```

`POST/PUT` 요청은 Pydantic이 날짜, 음수 값, 메모 길이를 검증합니다. 라우터는 HTTP 입출력만 담당하고, `services/store.py`는 저장소, `services/summary.py`는 통계와 추세 계산을 분리합니다.

## 핵심 흐름

`POST /api/chat`은 data 컬렉션을 읽어 기간·개수·평균·최소/최대·최근 추세를 계산하고, 그 요약을 시스템 프롬프트에 넣어 GPT에 전달합니다. 답변과 사용자 질문은 conversations에 자동 저장되므로, `GET /api/conversations/{id}`로 다시 불러올 수 있습니다.

## API

- `POST`, `GET /api/data`; `PUT`, `DELETE /api/data/{id}`; `GET /api/data/summary`
- `POST`, `GET /api/conversations`; `GET`, `DELETE /api/conversations/{id}`
- `POST /api/chat`

## 배포

1. GitHub에 푸시한 뒤 Render에서 **Blueprint** 또는 Web Service를 만들고 `render.yaml`을 선택합니다. `OPENAI_API_KEY`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `ALLOWED_ORIGINS=https://<vercel-domain>`을 설정합니다.
2. Vercel에서 `frontend` 폴더를 프로젝트 루트로 지정하여 배포하고, Vercel 환경 변수 `API_BASE_URL=https://<render-service>.onrender.com`을 등록합니다. `frontend/api/config.js`가 런타임에 이 값을 브라우저로 제공합니다. 로컬은 `frontend/config.js`를 사용합니다.
3. Render URL의 `/docs`에서 API를 시험하고, Vercel URL에서 채팅·CRUD·대화 불러오기를 확인합니다.

## 제출 스크린샷 체크

- 채팅: 데이터 요약과 질문/답변이 함께 보이도록 캡처
- 데이터 관리: 새 항목 추가 또는 수정/삭제 결과가 목록에 보이도록 캡처
- 대화 기록: 목록에서 대화를 선택한 뒤 메시지가 다시 표시된 화면 캡처
