import axios from "axios";

export type AnalysisResponse =
  | {
      status: "success";
      refrigerant_type: string;
      is_verified: boolean;
      analysis_time_seconds: number;
    }
  | { status: "failure"; message: "분석 실패"; analysis_time_seconds: number };

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
});

export async function requestAnalysis(apiKey: string, image: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append("image", image);
  const response = await api.post<AnalysisResponse>("/analyze", formData, {
    headers: { "X-API-Key": apiKey },
  });
  return response.data;
}
