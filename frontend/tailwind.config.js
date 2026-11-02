/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Restrained warm amber / muted gold accent (10–20% of UI)
        brand: {
          50:  '#FDF8F0',
          100: '#FAF0DE',
          200: '#F4DEBB',
          300: '#ECC58E',
          400: '#E2A961',
          500: '#D39A4A',
          600: '#C88A3D',
          700: '#A66E2E',
          800: '#845424',
          900: '#673F1C',
        },
        // Premium charcoal neutral foundation (80–90% of UI)
        surface: {
          950: '#0B0C0E',
          900: '#111215',
          850: '#16171B',
          800: '#1C1D22',
          750: '#23252B',
          700: '#2B2D35',
          600: '#383A44',
          500: '#4B4E5A',
          400: '#686C7C',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '8px',
        sm: '6px',
        md: '8px',
        lg: '10px',
        xl: '12px',
        '2xl': '14px',
      },
      boxShadow: {
        subtle: '0 1px 2px 0 rgba(0, 0, 0, 0.4)',
        card: '0 2px 8px -2px rgba(0, 0, 0, 0.5), 0 1px 2px -1px rgba(0, 0, 0, 0.4)',
        elevated: '0 8px 24px -4px rgba(0, 0, 0, 0.6), 0 2px 6px -1px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [],
}
