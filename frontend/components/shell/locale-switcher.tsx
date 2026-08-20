"use client";

import { useLocale, useTranslations } from "next-intl";
import { useTransition } from "react";

import type { AppLocale } from "@/i18n/config";
import { usePathname, useRouter } from "@/i18n/navigation";

const options: ReadonlyArray<AppLocale> = ["ko", "en"];

export function LocaleSwitcher() {
  const locale = useLocale() as AppLocale;
  const pathname = usePathname();
  const router = useRouter();
  const t = useTranslations("locale");
  const [isPending, startTransition] = useTransition();

  const changeLocale = (nextLocale: AppLocale) => {
    if (nextLocale === locale) return;

    startTransition(() => {
      router.replace(pathname, { locale: nextLocale });
    });
  };

  return (
    <div
      aria-label={t("label")}
      className="locale-switcher"
      data-testid="locale-switcher"
      role="group"
    >
      {options.map((option) => (
        <button
          aria-pressed={option === locale}
          disabled={isPending}
          key={option}
          onClick={() => changeLocale(option)}
          type="button"
        >
          {t(option)}
        </button>
      ))}
    </div>
  );
}
