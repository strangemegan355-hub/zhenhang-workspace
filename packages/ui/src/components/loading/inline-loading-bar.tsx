"use client";

import { designTokens } from "../../theme/design-tokens";
import { interactionTokens } from "../../theme/interaction-tokens";

export function InlineLoadingBar({ active = true }: { active?: boolean }) {
  if (!active) return null;
  return (
    <div
      className="absolute left-0 right-0 top-0 z-[25] h-0.5 overflow-hidden"
      role="progressbar"
      aria-valuetext="加载中"
    >
      <div
        className="h-full w-1/3"
        style={{
          backgroundColor: designTokens.colors.primary.default,
          animation: "industrial-bar 1.2s ease-in-out infinite",
        }}
      />
      <style>{`
        @keyframes industrial-bar {
          0% { transform: translateX(-100%); }
          50% { transform: translateX(200%); }
          100% { transform: translateX(400%); }
        }
      `}</style>
    </div>
  );
}
