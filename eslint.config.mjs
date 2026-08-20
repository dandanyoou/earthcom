import { FlatCompat } from "@eslint/eslintrc";
import js from "@eslint/js";
import globals from "globals";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import tseslint from "typescript-eslint";

const baseDirectory = dirname(fileURLToPath(import.meta.url));
const compat = new FlatCompat({ baseDirectory });

const config = [
  {
    ignores: [
      "**/node_modules/**",
      "**/.next/**",
      "**/playwright-report/**",
      "**/test-results/**",
      "**/next-env.d.ts",
      "docs/reference/**",
      "backend/.venv/**",
      "**/coverage/**",
      "**/public/scroll-world/**",
    ],
  },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    settings: {
      next: {
        rootDir: "frontend",
      },
      react: {
        version: "19.1",
      },
    },
    rules: {
      "@next/next/no-html-link-for-pages": "off",
    },
  },
  {
    ...js.configs.recommended,
    files: ["**/*.{js,mjs,cjs}"],
    languageOptions: {
      globals: globals.node,
    },
  },
  ...tseslint.configs.recommended.map((config) => ({
    ...config,
    files: ["**/*.{ts,tsx}"],
  })),
  {
    files: ["**/*.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "no-restricted-imports": [
        "error",
        {
          patterns: ["openai", "@anthropic-ai/*"],
        },
      ],
      "no-restricted-syntax": [
        "error",
        {
          selector: "Literal[value=/^sk-/]",
          message: "API 키를 프론트에 두지 않는다",
        },
        {
          selector: "JSXText[value=/[가-힣]/]",
          message: "화면 문구는 messages/*.json에서 가져온다 (§4.8)",
        },
      ],
    },
  },
];

export default config;
