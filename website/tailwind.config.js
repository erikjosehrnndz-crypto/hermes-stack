// tailwind.config.js
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  darkMode: 'class', // enable class strategy for dark mode toggle
  theme: {
    extend: {
      colors: {
        primary: '#0ea5e9', // sky-500
        secondary: '#64748b', // slate-500
      },
    },
  },
  plugins: [],
};
