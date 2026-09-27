import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { AxiosError } from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { requestAnalysis } from "./api";

vi.mock("./api", () => ({
  requestAnalysis: vi.fn(),
}));

const mockedRequestAnalysis = vi.mocked(requestAnalysis);

function selectImage() {
  const imageInput = screen.getByLabelText("명판 이미지");
  const file = new File(["nameplate"], "nameplate.png", { type: "image/png" });
  const files = {
    0: file,
    length: 1,
    item: (index: number) => (index === 0 ? file : null),
  };
  fireEvent.change(imageInput, { target: { files } });
}

describe("Nameplate Image analysis form", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    mockedRequestAnalysis.mockReset();
  });

  it("does not submit an incorrectly sized Shared API Key", async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText("API 키"), { target: { value: "short" } });
    selectImage();
    fireEvent.submit(screen.getByRole("button", { name: "분석하기" }));

    expect((await screen.findByRole("alert")).textContent).toBe("API 키는 6글자여야 합니다.");
    expect(mockedRequestAnalysis).not.toHaveBeenCalled();
  });

  it.each(["Shared API Key", "Nameplate Image"])("shows an input error when the %s is missing", async (missing) => {
    render(<App />);

    if (missing === "Shared API Key") {
      selectImage();
    } else {
      fireEvent.change(screen.getByLabelText("API 키"), { target: { value: "A1b2C3" } });
    }
    fireEvent.submit(screen.getByRole("button", { name: "분석하기" }));

    expect((await screen.findByRole("alert")).textContent).toBe("API 키와 이미지 파일을 모두 입력해 주세요.");
    expect(mockedRequestAnalysis).not.toHaveBeenCalled();
  });

  it("shows a confirmed Refrigerant Type and Analysis Time", async () => {
    mockedRequestAnalysis.mockResolvedValue({
      status: "success",
      refrigerant_type: "R-410A",
      analysis_time_seconds: 2.31,
    });
    render(<App />);

    fireEvent.change(screen.getByLabelText("API 키"), { target: { value: "A1b2C3" } });
    selectImage();
    fireEvent.submit(screen.getByRole("button", { name: "분석하기" }));

    expect(await screen.findByText("냉매 종류:")).toBeTruthy();
    expect(screen.getByText("R-410A")).toBeTruthy();
    expect(screen.getByText("분석 소요 시간: 2.310초")).toBeTruthy();
  });

  it("shows Analysis Failure and Analysis Time without a guessed Refrigerant Type", async () => {
    mockedRequestAnalysis.mockResolvedValue({
      status: "failure",
      message: "분석 실패",
      analysis_time_seconds: 1.2,
    });
    render(<App />);

    fireEvent.change(screen.getByLabelText("API 키"), { target: { value: "A1b2C3" } });
    selectImage();
    fireEvent.submit(screen.getByRole("button", { name: "분석하기" }));

    expect(await screen.findByText("분석 실패")).toBeTruthy();
    expect(screen.getByText("분석 소요 시간: 1.200초")).toBeTruthy();
    expect(screen.queryByText("냉매 종류:")).toBeNull();
  });

  it.each([
    [401, "API 키가 올바르지 않습니다."],
    [400, "지원되는 이미지와 파일 크기를 확인해 주세요."],
  ])("shows the right request feedback for HTTP %s", async (status, message) => {
    const error = new AxiosError("request failed");
    Object.defineProperty(error, "response", { value: { status } });
    mockedRequestAnalysis.mockRejectedValue(error);
    render(<App />);

    fireEvent.change(screen.getByLabelText("API 키"), { target: { value: "A1b2C3" } });
    selectImage();
    fireEvent.submit(screen.getByRole("button", { name: "분석하기" }));

    expect((await screen.findByRole("alert")).textContent).toBe(message);
  });
});
