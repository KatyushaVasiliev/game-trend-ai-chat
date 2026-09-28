// Vercel Serverless Function: API_BASE_URL 환경 변수를 브라우저에 안전하게 전달한다.
export default function handler(request, response) {
  response.setHeader("Cache-Control", "no-store");
  const apiBaseUrl = process.env.API_BASE_URL || "";
  response.status(200).json({
    apiBaseUrl: apiBaseUrl ? "/api/proxy" : "",
    proxy: Boolean(apiBaseUrl),
  });
}
