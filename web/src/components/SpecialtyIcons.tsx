type Props = { size?: number; className?: string };

const baseProps = {
  fill: "none" as const,
  stroke: "currentColor" as const,
  strokeWidth: 1.4,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function RadiologyIcon({ size = 36, className }: Props) {
  // Stylized chest scan: ribcage curves inside a frame.
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      className={className}
      aria-hidden
      {...baseProps}
    >
      <rect x="6" y="6" width="36" height="36" rx="3" />
      <path d="M14 14c4 4 6 9 10 9s6-5 10-9" />
      <path d="M14 22c4 4 6 9 10 9s6-5 10-9" />
      <path d="M14 30c4 4 6 9 10 9s6-5 10-9" />
      <circle cx="24" cy="14" r="1" fill="currentColor" />
    </svg>
  );
}

export function PhysiotherapyIcon({ size = 36, className }: Props) {
  // Stylized figure mid-stretch.
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      className={className}
      aria-hidden
      {...baseProps}
    >
      <circle cx="24" cy="11" r="3.5" />
      <path d="M24 15v9" />
      <path d="M16 21l8 3 8-3" />
      <path d="M24 24l-5 9" />
      <path d="M24 24l5 9" />
      <path d="M19 33l-2 6" />
      <path d="M29 33l2 6" />
    </svg>
  );
}

export function CardiovascularIcon({ size = 36, className }: Props) {
  // Heart silhouette with ECG line.
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      className={className}
      aria-hidden
      {...baseProps}
    >
      <path d="M24 38c-9-5.5-15-11.5-15-19a7 7 0 0 1 12-5l3 3 3-3a7 7 0 0 1 12 5c0 7.5-6 13.5-15 19z" />
      <path d="M9 26h6l2-4 3 8 3-6 2 2h9" />
    </svg>
  );
}

const MAP = {
  radiology: RadiologyIcon,
  physiotherapy: PhysiotherapyIcon,
  cardiovascular: CardiovascularIcon,
} as const;

export function SpecialtyIcon({
  slug,
  ...props
}: Props & { slug: string }) {
  const Cmp = MAP[slug as keyof typeof MAP] || RadiologyIcon;
  return <Cmp {...props} />;
}
