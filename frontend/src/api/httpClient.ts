const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:5000";

function resolveUrl(path: string) {
  return new URL(path, API_BASE_URL).toString();
}

async function readError(response: Response) {
  const text = await response.text();
  try {
    const json = JSON.parse(text) as { error?: string; message?: string; status?: string };
    return json.error || text || response.statusText;
  } catch {
    return text || response.statusText;
  }
}

function friendlyErrorMessage(message: string) {
  const normalized = message.trim();
  if (!normalized) {
    return "Request failed. Please try again.";
  }
  if (/failed to fetch|networkerror|network error/i.test(normalized)) {
    return "Cannot reach backend API. Check if the backend is running and CORS/API URL settings are correct.";
  }
  if (/timeout/i.test(normalized)) {
    return "Request timed out. Check device connectivity and try again.";
  }
  return normalized;
}

export async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { headers: customHeaders, ...rest } = options;
  const response = await fetch(resolveUrl(path), {
    ...rest,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(customHeaders ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(friendlyErrorMessage(await readError(response)));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function parseFilename(contentDisposition: string | null, fallback: string) {
  if (!contentDisposition) {
    return fallback;
  }

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }

  const quotedMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
  if (quotedMatch?.[1]) {
    return quotedMatch[1];
  }

  return fallback;
}

function triggerDownload(blob: Blob, filename: string) {
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.style.display = "none";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

export async function requestReportDownload<T>(path: string, body: unknown, fallbackFilename: string): Promise<T> {
  const response = await fetch(resolveUrl(path), {
    method: "POST",
    headers: {
      Accept: "*/*",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(friendlyErrorMessage(await readError(response)));
  }

  const blob = await response.blob();
  const filename = parseFilename(response.headers.get("Content-Disposition"), fallbackFilename);
  triggerDownload(blob, filename);

  return {
    filename,
    rows: Number(response.headers.get("X-Row-Count") ?? "0"),
    generatedAt: response.headers.get("X-Generated-At") ?? new Date().toISOString(),
    meterName: response.headers.get("X-Meter-Name") ?? "",
    format: fallbackFilename.endsWith(".docx") ? "docx" : "xlsx",
  } as T;
}
