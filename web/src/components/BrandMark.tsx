export default function BrandMark({
  size = 28,
  withText = false,
}: {
  size?: number;
  withText?: boolean;
}) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        aria-hidden
      >
        <rect
          x="1.5"
          y="1.5"
          width="29"
          height="29"
          rx="8"
          fill="#0c0a09"
        />
        <path
          d="M9 22V12l5 7 5-7v10"
          stroke="white"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="23" cy="20" r="1.6" fill="white" />
      </svg>
      {withText && (
        <span className="flex flex-col leading-none">
          <span className="font-semibold tracking-tight text-[15px] text-stone-900">
            MedFAQ
          </span>
          <span className="text-[10px] uppercase tracking-[0.18em] text-stone-500">
            Clinical Assistant
          </span>
        </span>
      )}
    </span>
  );
}
