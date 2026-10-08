import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // shadcn/ui CSS variable-mapped colors (Charter palette via globals.css)
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        success: {
          DEFAULT: "var(--success)",
          foreground: "var(--success-foreground)",
          muted: "var(--success-muted)",
        },
        warning: {
          DEFAULT: "var(--warning)",
          foreground: "var(--warning-foreground)",
          muted: "var(--warning-muted)",
        },
        info: {
          DEFAULT: "var(--info)",
          foreground: "var(--info-foreground)",
          muted: "var(--info-muted)",
        },
        "status-proposal": {
          DEFAULT: "var(--status-proposal)",
          muted: "var(--status-proposal-muted)",
        },
        "status-qualified": {
          DEFAULT: "var(--status-qualified)",
          muted: "var(--status-qualified-muted)",
        },
        "stage-new": "var(--stage-new)",
        "stage-contacted": "var(--stage-contacted)",
        "stage-qualified": "var(--stage-qualified)",
        "stage-proposal": "var(--stage-proposal)",
        "stage-negotiation": "var(--stage-negotiation)",
        "stage-won": "var(--stage-won)",
        "stage-lost": "var(--stage-lost)",
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        chart: {
          "1": "var(--chart-1)",
          "2": "var(--chart-2)",
          "3": "var(--chart-3)",
          "4": "var(--chart-4)",
          "5": "var(--chart-5)",
        },
        sidebar: {
          DEFAULT: "var(--sidebar)",
          foreground: "var(--sidebar-foreground)",
          primary: "var(--sidebar-primary)",
          "primary-foreground": "var(--sidebar-primary-foreground)",
          accent: "var(--sidebar-accent)",
          "accent-foreground": "var(--sidebar-accent-foreground)",
          border: "var(--sidebar-border)",
          ring: "var(--sidebar-ring)",
        },
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        sm: "0.375rem",
        md: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
        full: "9999px",
      },
      spacing: {
        sidebar_width: "240px",
        base: "4px",
        container_padding: "32px",
        topbar_height: "56px",
        input_height: "36px",
        stack_gap: "16px",
      },
      fontFamily: {
        mono: ["GeistMono", "monospace"],
        sans: ["GeistSans", "sans-serif"],
        display: ["GeistSans", "sans-serif"],
      },
      fontSize: {
        mono: ["13px", { lineHeight: "18px", fontWeight: "400" }],
        "small-medium": ["12px", { lineHeight: "16px", fontWeight: "500" }],
        "body-medium": ["14px", { lineHeight: "20px", fontWeight: "500" }],
        display: ["28px", { lineHeight: "36px", letterSpacing: "-0.02em", fontWeight: "700" }],
        body: ["14px", { lineHeight: "20px", fontWeight: "400" }],
        h3: ["15px", { lineHeight: "20px", fontWeight: "600" }],
        h2: ["18px", { lineHeight: "24px", fontWeight: "600" }],
        h1: ["22px", { lineHeight: "28px", letterSpacing: "-0.01em", fontWeight: "600" }],
        small: ["12px", { lineHeight: "16px", fontWeight: "400" }],
      },
    },
  },
  plugins: [],
};
export default config;
