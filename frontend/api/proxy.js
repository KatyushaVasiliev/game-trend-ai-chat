// Same-origin proxy for the Render API. This keeps browser requests independent
// of the API service's CORS configuration.
export default async function handler(request, response) {
  const apiBaseUrl = process.env.API_BASE_URL;
  const path = request.query.path;

  if (!apiBaseUrl || typeof path !== "string" || !path.startsWith("/api/") && path !== "/") {
    response.status(400).json({ detail: "Invalid API proxy request." });
    return;
  }

  const method = request.method || "GET";
  const hasBody = !["GET", "HEAD"].includes(method);
  const upstream = await fetch(`${apiBaseUrl.replace(/\/$/, "")}${path}`, {
    method,
    headers: hasBody ? { "Content-Type": "application/json" } : undefined,
    body: hasBody && request.body !== undefined ? JSON.stringify(request.body) : undefined,
  });
  const body = await upstream.text();

  const contentType = upstream.headers.get("content-type");
  if (contentType) response.setHeader("Content-Type", contentType);
  response.status(upstream.status).send(body);
}
