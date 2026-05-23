import { designTokens } from "../../theme/design-tokens";
import { typography } from "../../theme/typography";
import { CardSkeleton } from "./card-skeleton";

export function PageLoading({ label = "加载中…" }: { label?: string }) {
  return (
    <div className="space-y-4">
      <p className={typography.body} style={{ color: designTokens.colors.text.muted }}>
        {label}
      </p>
      <CardSkeleton count={6} />
    </div>
  );
}
