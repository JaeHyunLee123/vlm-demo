import { AxiosError } from "axios";
import { FormEvent, useState } from "react";

import { AnalysisResponse, requestAnalysis } from "./api";

type ViewState =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "result"; result: AnalysisResponse }
  | { kind: "error"; message: string };

function Result({ result }: { result: AnalysisResponse }) {
  if (result.status === "success") {
    return (
      <section aria-live="polite">
        <h2>분석 결과</h2>
        <p>
          냉매 종류: <strong>{result.refrigerant_type}</strong>
        </p>
        {!result.is_verified ? <p>검증 목록에 없는 냉매 표기입니다.</p> : null}
        <p>분석 소요 시간: {result.analysis_time_seconds.toFixed(3)}초</p>
      </section>
    );
  }

  return (
    <section aria-live="polite">
      <h2>분석 결과</h2>
      <p>{result.message}</p>
      <p>분석 소요 시간: {result.analysis_time_seconds.toFixed(3)}초</p>
    </section>
  );
}

function requestErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    if (error.response?.status === 401) return "API 키가 올바르지 않습니다.";
    if (error.response?.status === 400)
      return "지원되는 이미지와 파일 크기를 확인해 주세요.";
  }
  return "분석 요청에 실패했습니다. 잠시 후 다시 시도해 주세요.";
}

export function App() {
  const [apiKey, setApiKey] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [viewState, setViewState] = useState<ViewState>({ kind: "idle" });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (apiKey.length === 0 || image === null) {
      setViewState({
        kind: "error",
        message: "API 키와 이미지 파일을 모두 입력해 주세요.",
      });
      return;
    }
    if (apiKey.length !== 6) {
      setViewState({ kind: "error", message: "API 키는 6글자여야 합니다." });
      return;
    }

    setViewState({ kind: "submitting" });
    try {
      const result = await requestAnalysis(apiKey, image);
      setViewState({ kind: "result", result });
    } catch (error) {
      setViewState({ kind: "error", message: requestErrorMessage(error) });
    }
  }

  return (
    <>
      <h1>에어컨 명판 냉매 분석</h1>
      <p>실외기 명판 사진에서 명확하게 읽힌 냉매 종류만 안내합니다.</p>
      <p>테스트용 화면입니다.</p>

      <form onSubmit={submit}>
        <label htmlFor="api-key">API 키</label>
        <input
          id="api-key"
          type="password"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          autoComplete="off"
          required
        />

        <label htmlFor="image">명판 이미지</label>
        <input
          id="image"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={(event) => setImage(event.target.files?.item(0) ?? null)}
          required
        />

        <button type="submit" disabled={viewState.kind === "submitting"}>
          {viewState.kind === "submitting" ? "분석 중…" : "분석하기"}
        </button>
      </form>

      {viewState.kind === "result" ? (
        <Result result={viewState.result} />
      ) : null}
      {viewState.kind === "error" ? (
        <p role="alert">{viewState.message}</p>
      ) : null}
    </>
  );
}
