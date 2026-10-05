function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/**
 * Read the human-readable reason out of whatever the HTTP layer threw.
 *
 * The backend wraps errors as `{code, message, detail}`, and a validation failure nests the reason
 * one level deeper, so the extraction is deliberately explicit — instead of
 * `err?.response?.data?.detail?.detail ?? err?.message ?? "..."` repeated at every call site with
 * `catch (err: any)`, which is what this replaced.
 */
export function apiErrorMessage(error: unknown, fallback: string): string {
  if (isRecord(error)) {
    const response = error.response;
    if (isRecord(response)) {
      const data = response.data;
      if (isRecord(data)) {
        const detail = data.detail;
        if (typeof detail === "string" && detail) return detail;
        if (isRecord(detail) && typeof detail.detail === "string" && detail.detail) {
          return detail.detail;
        }
        if (typeof data.message === "string" && data.message) return data.message;
      }
    }
    if (typeof error.message === "string" && error.message) return error.message;
  }
  return fallback;
}
