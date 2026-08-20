import type { Metadata } from "next";
import { hasLocale, NextIntlClientProvider } from "next-intl";
import { getMessages, getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";

import { LocaleSwitcher } from "@/components/shell/locale-switcher";
import { routing } from "@/i18n/routing";

import "../globals.css";

type LocaleLayoutProps = Readonly<{
  children: ReactNode;
  params: Promise<{ locale: string }>;
}>;

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: LocaleLayoutProps): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "metadata" });

  return {
    description: t("description"),
    title: "PANGAEA",
    manifest: "/manifest.webmanifest",
    icons: {
      icon: [{ url: "/icons/icon.svg", type: "image/svg+xml" }],
      apple: [{ url: "/icons/icon-192.png" }],
    },
    appleWebApp: { capable: true, statusBarStyle: "default", title: "PANGAEA" },
  };
}

export const viewport = {
  themeColor: "#17223a",
  width: "device-width",
  initialScale: 1,
};

export default async function LocaleLayout({ children, params }: LocaleLayoutProps) {
  const { locale } = await params;

  if (!hasLocale(routing.locales, locale)) notFound();

  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body>
        {/* React 19 hoists these into <head>; fallback stacks cover offline.
            The no-page-custom-font rule targets pages/_document and misfires
            on app-router root layouts. */}
        <link href="https://fonts.googleapis.com" rel="preconnect" />
        <link crossOrigin="anonymous" href="https://fonts.gstatic.com" rel="preconnect" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
        <link
          crossOrigin="anonymous"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.css"
          rel="stylesheet"
        />
        <NextIntlClientProvider messages={messages}>
          <div className="locale-toolbar">
            <LocaleSwitcher />
          </div>
          <div className="locale-content">{children}</div>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
