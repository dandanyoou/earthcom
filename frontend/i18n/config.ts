export const locales = ["ko", "en"] as const;
export const defaultLocale = "ko";

export type AppLocale = (typeof locales)[number];
