/**
 * Sparkle — the 4-point star accent from the reference illustration set.
 * Sprinkle these near CTAs, headings, and selected states for energy.
 */
export default function Sparkle({ className = '', size = 24, color = 'currentColor', twinkle = false }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      className={`${twinkle ? 'animate-twinkle' : ''} ${className}`}
    >
      <path
        d="M12 0c.6 5.6 5.8 10.8 11.4 11.4v.5C17.8 12.5 12.6 17.7 12 23.3c-.6-5.6-5.8-10.8-11.4-11.4v-.5C6.2 10.8 11.4 5.6 12 0Z"
        fill={color}
      />
    </svg>
  )
}
