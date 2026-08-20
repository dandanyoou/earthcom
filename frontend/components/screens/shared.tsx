"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { getToken } from "@/lib/api";

export function useRequireAuth() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!getToken()) router.replace("/login");
    else setReady(true);
  }, [router]);
  return ready;
}

export function useApiData<T>(fetcher: () => Promise<T>, enabled = true, key: unknown = null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const reload = useCallback(() => {
    if (!enabled) return;
    fetcher()
      .then((result) => {
        setData(result);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, key]);
  useEffect(() => {
    reload();
  }, [reload]);
  return { data, error, loading, reload, setData };
}

export function ScreenHeader({
  title,
  subtitle,
  onBack,
  trailing,
}: {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  trailing?: ReactNode;
}) {
  const t = useTranslations("common");
  return (
    <div className="appbar">
      {onBack ? (
        <button className="appbar__back" onClick={onBack} aria-label={t("back")} type="button">
          ‹
        </button>
      ) : null}
      <div>
        <div className="appbar__title">{title}</div>
        {subtitle ? <div className="appbar__subtitle">{subtitle}</div> : null}
      </div>
      {trailing ? <div className="appbar__trailing">{trailing}</div> : null}
    </div>
  );
}

export function Sheet({
  open,
  onClose,
  title,
  subtitle,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div
      className="sheet-backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      role="presentation"
    >
      <div className="sheet" role="dialog" aria-modal="true" aria-label={title}>
        <div className="sheet__title">{title}</div>
        {subtitle ? <div className="sheet__subtitle">{subtitle}</div> : null}
        {children}
      </div>
    </div>
  );
}

export function useTimeAgo() {
  const t = useTranslations("time");
  return useCallback(
    (iso: string | null) => {
      if (!iso) return "";
      const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
      if (seconds < 90) return t("justNow");
      if (seconds < 3600) return t("minutesAgo", { count: Math.floor(seconds / 60) });
      if (seconds < 86400) return t("hoursAgo", { count: Math.floor(seconds / 3600) });
      return t("daysAgo", { count: Math.floor(seconds / 86400) });
    },
    [t],
  );
}

export function palette(value: number): 1 | 2 | 3 | 4 | 5 | 6 {
  const normalized = ((Math.trunc(value) - 1) % 6) + 1;
  return (normalized >= 1 && normalized <= 6 ? normalized : 1) as 1 | 2 | 3 | 4 | 5 | 6;
}

export function trustText(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${value.toFixed(1)}°`;
}

export function trustFillPercent(value: number | null | undefined): number {
  if (value === null || value === undefined) return 0;
  return Math.min(100, Math.max(0, ((value - 30) / 20) * 100));
}

export function LoadingBlock({ error, reload }: { error?: string | null; reload?: () => void }) {
  const t = useTranslations("common");
  if (error) {
    return (
      <div className="screen-loading">
        {t("error")}
        {reload ? (
          <div style={{ marginTop: 10 }}>
            <button className="button button--ghost button--small" onClick={reload} type="button">
              {t("retry")}
            </button>
          </div>
        ) : null}
      </div>
    );
  }
  return <div className="screen-loading">{t("loading")}</div>;
}
