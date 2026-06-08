/** Chunky filled paw — used as logo mark and footprint connectors. */
export default function PawIcon({ className = '', size = 24, color = 'currentColor' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      className={className}
    >
      <ellipse cx="12" cy="16" rx="5.2" ry="4.4" fill={color} />
      <ellipse cx="5.6" cy="11.4" rx="2.3" ry="3" fill={color} />
      <ellipse cx="18.4" cy="11.4" rx="2.3" ry="3" fill={color} />
      <ellipse cx="9" cy="6.4" rx="2.1" ry="2.7" fill={color} />
      <ellipse cx="15" cy="6.4" rx="2.1" ry="2.7" fill={color} />
    </svg>
  )
}
