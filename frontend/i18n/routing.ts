import { defineRouting } from "next-intl/routing";

import { defaultLocale, locales } from "./config";

export const routing = defineRouting({
  defaultLocale,
  localeCookie: {
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax",
  },
  localePrefix: "always",
  locales,
});
