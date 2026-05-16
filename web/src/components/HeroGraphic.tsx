/**
 * Decorative line-art panel that pairs with the hero text.
 * No external assets, pure SVG. Drawn in stone-700 so it sits quietly
 * beside the bold headline.
 */
export default function HeroGraphic() {
  return (
    <svg
      viewBox="0 0 360 280"
      fill="none"
      className="w-full h-auto max-w-[360px] text-stone-700"
      aria-hidden
    >
      {/* Soft grid wash */}
      <defs>
        <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M20 0H0V20" stroke="currentColor" strokeOpacity="0.08" />
        </pattern>
      </defs>
      <rect x="0" y="0" width="360" height="280" fill="url(#grid)" />

      {/* Outer card */}
      <rect
        x="20" y="40" width="320" height="200" rx="14"
        fill="white" stroke="currentColor" strokeOpacity="0.25"
      />

      {/* Card header strip */}
      <line x1="20" y1="72" x2="340" y2="72" stroke="currentColor" strokeOpacity="0.18" />
      <circle cx="36" cy="56" r="3" fill="currentColor" opacity="0.4" />
      <circle cx="48" cy="56" r="3" fill="currentColor" opacity="0.4" />
      <circle cx="60" cy="56" r="3" fill="currentColor" opacity="0.4" />

      {/* User bubble */}
      <rect
        x="170" y="90" width="150" height="34" rx="10"
        fill="#0c0a09"
      />
      <line x1="184" y1="105" x2="304" y2="105" stroke="white" strokeOpacity="0.6" />
      <line x1="184" y1="113" x2="270" y2="113" stroke="white" strokeOpacity="0.4" />

      {/* Bot bubble */}
      <rect
        x="40" y="138" width="180" height="50" rx="10"
        fill="#f5f5f4" stroke="currentColor" strokeOpacity="0.18"
      />
      <line x1="54" y1="154" x2="200" y2="154" stroke="currentColor" strokeOpacity="0.45" />
      <line x1="54" y1="162" x2="186" y2="162" stroke="currentColor" strokeOpacity="0.32" />
      <line x1="54" y1="170" x2="160" y2="170" stroke="currentColor" strokeOpacity="0.22" />

      {/* ECG line at bottom */}
      <path
        d="M20 218 L80 218 L92 198 L104 232 L116 218 L160 218 L172 204 L184 228 L196 218 L340 218"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {/* Small dot annotations */}
      <circle cx="92" cy="56" r="2.5" stroke="currentColor" strokeOpacity="0.45" />
      <text
        x="100" y="60"
        fontSize="9"
        fill="currentColor"
        fillOpacity="0.55"
        fontFamily="ui-sans-serif"
      >
        Patient chat / radiology
      </text>
    </svg>
  );
}
