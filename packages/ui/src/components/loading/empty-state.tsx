import { designTokens } from "../../theme/design-tokens";
import { interactionTokens } from "../../theme/interaction-tokens";
import { typography } from "../../theme/typography";

export function EmptyState({
  message = "暂无数据",
  hint,
}: {
  message?: string;
  hint?: string;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded py-8 text-center"
      style={{
        border: `1px dashed ${designTokens.colors.border.default}`,
        backgroundColor: designTokens.colors.background.subtle,
        padding: interactionTokens.layout.panelPadding,
      }}
    >
      <p className={typography.body} style={{ color: designTokens.colors.text.muted }}>
        {message}
      </p>
      {hint ? (
        <p className={`${typography.caption} mt-1`} style={{ color: designTokens.colors.text.muted }}>
          {hint}
        </p>
      ) : null}
    </div>
  );
}
