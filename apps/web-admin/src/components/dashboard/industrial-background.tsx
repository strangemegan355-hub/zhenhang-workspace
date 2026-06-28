"use client";

export function IndustrialBackground() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-x-0 top-0 z-0 h-[420px] overflow-hidden"
    >
      <svg
        className="absolute inset-0 h-full w-full opacity-[0.04] dark:opacity-[0.06]"
        viewBox="0 0 1440 420"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="dash-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M40 0H0V40" stroke="var(--color-primary)" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="1440" height="420" fill="url(#dash-grid)" />
        <path
          d="M0 320 L180 280 L320 300 L480 240 L640 260 L820 200 L980 220 L1140 180 L1300 200 L1440 160"
          stroke="var(--color-primary)"
          strokeWidth="1.5"
          strokeDasharray="8 6"
        />
        <path
          d="M120 380 L120 260 L220 260 L220 220 L340 220 L340 180 L460 180 L460 140 L580 140"
          stroke="var(--color-primary)"
          strokeWidth="1.2"
        />
        <rect x="900" y="120" width="180" height="100" rx="8" stroke="var(--color-primary)" strokeWidth="1.2" />
        <circle cx="990" cy="170" r="28" stroke="var(--color-primary)" strokeWidth="1.2" />
        <path d="M1050 80 L1120 80 L1120 150 L1050 150 Z" stroke="var(--color-primary)" strokeWidth="1" />
        <path
          d="M60 80 H200 V180 H60 Z M80 100 H120 V160 H80 Z M140 100 H180 V160 H140 Z"
          stroke="var(--color-primary)"
          strokeWidth="1"
        />
      </svg>
      <div className="absolute inset-0 bg-gradient-to-b from-[#f4f8ff] via-[#f4f8ff]/80 to-transparent dark:from-[#071a2f] dark:via-[#071a2f]/80" />
    </div>
  );
}
