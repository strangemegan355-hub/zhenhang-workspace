import { ErrorBanner } from "./error-banner";

/** @deprecated Prefer ErrorBanner — kept for existing imports */
export function ErrorState({
  message = "加载失败",
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return <ErrorBanner message={message} onRetry={onRetry} />;
}
