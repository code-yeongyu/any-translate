# Any-Translate

OpenAI API를 사용한 자막 및 텍스트 번역 도구

## 사용법

```bash
uvx --from git+https://github.com/code-yeongyu/any-translate.git any-translate translate --help
```


### 옵션

- `--output`, `-o`: 출력 파일 경로 (기본값: 입력 파일명_target_lang.확장자)
- `--source-lang`, `-s`: 원본 언어 (기본값: auto)
- `--target-lang`, `-t`: 목표 언어 (기본값: ko)
- `--openai-api-key`: OpenAI API 키 (환경 변수 OPENAI_API_KEY로도 설정 가능)
- `--base-url`: OpenAI API base URL (기본 base URL을 오버라이드하는 경우 사용)
- `--model`, `-m`: 사용할 OpenAI 모델 (기본값: gpt-4o-mini)
- `--sessions`, `-n`: 동시에 처리할 세션 수 (기본값: 1)
- `--temperature`, `-T`: 모델의 temperature 값 (기본값: 1.0)
- `--tone`: 번역 톤 (formal, informal, auto-contextual) (기본값: auto-contextual)
- `--system-prompt-file`, `-p`: 번역을 위한 시스템 프롬프트 파일
- `--custom-prompt`: 추가 프롬프트

## 예제

### 영어 자막을 한국어로 번역

```bash
any-translate translate english.srt --target-lang ko
```

### 일본어 자막을 한국어로 번역 (공식적인 톤)

```bash
any-translate translate japanese.srt --source-lang ja --target-lang ko --tone formal
```

### 텍스트 파일을 한국어로 번역 (여러 세션 사용)

```bash
any-translate translate-text document.txt --target-lang ko --sessions 3
```

### 커스텀 OpenAI API 엔드포인트 사용

```bash
any-translate translate input.srt --target-lang ko --base-url "https://custom-openai-endpoint.com/v1"
```

## 라이선스

MIT
