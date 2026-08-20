import { hasLocale } from "next-intl";
import { getRequestConfig } from "next-intl/server";

import { defaultLocale, locales } from "./config";
import enMessages from "../messages/en.json";
import koMessages from "../messages/ko.json";

const messagesByLocale = {
  en: enMessages,
  ko: koMessages,
} as const;

export default getRequestConfig(async ({ requestLocale }) => {
  const requestedLocale = await requestLocale;
  const locale = hasLocale(locales, requestedLocale) ? requestedLocale : defaultLocale;

  return {
    locale,
    messages: messagesByLocale[locale],
  };
});
