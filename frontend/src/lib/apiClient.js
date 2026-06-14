import { DJANGO_BASE_URL, FASTAPI_BASE_URL } from "../constants/api";

const DEFAULT_TIMEOUT = 5000;

function buildUrl(baseUrl, path) {
  return `${baseUrl}${path}`;
}

async function request(baseUrl, path, options = {}) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), options.timeout || DEFAULT_TIMEOUT);

  try {
    const response = await fetch(buildUrl(baseUrl, path), {
      ...options,
      signal: controller.signal,
      headers: {
        ...(options.headers || {})
      }
    });

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json") ? await response.json() : await response.text();

    if (!response.ok) {
      const message = typeof data === "string" ? data : data?.message || data?.detail || "Request failed";
      throw new Error(message);
    }

    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Request timed out");
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export function getDjango(path, options) {
  return request(DJANGO_BASE_URL, path, options);
}

export function getFastApi(path, options) {
  return request(FASTAPI_BASE_URL, path, options);
}

export function postForm(baseUrl, path, formData, options = {}) {
  return request(baseUrl, path, {
    method: "POST",
    body: formData,
    ...options
  });
}

export function postUrlEncoded(path, payload, options = {}) {
  const body = new URLSearchParams(payload);
  return request(DJANGO_BASE_URL, path, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      ...(options.headers || {})
    },
    body,
    ...options
  });
}

export { DEFAULT_TIMEOUT };
