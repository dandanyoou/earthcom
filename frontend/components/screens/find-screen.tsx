"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { Avatar, Chip } from "@/components/ui";
import { api, type SearchResult } from "@/lib/api";

import { palette, ScreenHeader, trustText, useRequireAuth } from "./shared";

export function FindScreen() {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResult | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!ready) return;
    if (timer.current) clearTimeout(timer.current);
    if (!query.trim()) {
      setResult(null);
      return;
    }
    timer.current = setTimeout(async () => {
      try {
        setResult(await api.searchProfiles(query));
      } catch {
        setResult(null);
      }
    }, 350);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [query, ready]);

  if (!ready) return null;

  return (
    <div style={{ paddingBottom: 28 }}>
      <ScreenHeader subtitle={t("find.subtitle")} title={t("find.title")} />
      <div className="px">
        <div className="findbar findbar--input" style={{ marginTop: 14 }}>
          <span aria-hidden>⌕</span>
          <input
            aria-label={t("find.title")}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={t("find.placeholder")}
            value={query}
          />
        </div>
        {result && result.terms.length > 0 ? (
          <div className="inline-chips">
            {result.terms.map((term) => (
              <Chip key={term} tone="verified">
                {term}
              </Chip>
            ))}
          </div>
        ) : null}

        {result === null ? (
          <div className="list-empty">{t("find.hint")}</div>
        ) : (
          <>
            <div className="section-heading">
              {t("find.foundTitle")}{" "}
              <small className="mono" style={{ color: "var(--t3)", fontSize: 11, fontWeight: 400 }}>
                {result.total}
              </small>
            </div>
            {result.results.length === 0 ? (
              <div className="list-empty">{t("find.empty")}</div>
            ) : (
              result.results.map((profile) => (
                <button
                  key={profile.id}
                  className="row"
                  onClick={() => router.push(`/profiles/${profile.id}`)}
                  style={{
                    background: "none",
                    border: 0,
                    cursor: "pointer",
                    textAlign: "left",
                    width: "100%",
                  }}
                  type="button"
                >
                  <Avatar palette={palette(profile.palette)}>{profile.initials}</Avatar>
                  <span style={{ flex: 1, minWidth: 0 }}>
                    <span className="result-name">
                      {profile.display_name}{" "}
                      <span className="cc">{profile.locale.toUpperCase()}</span>
                    </span>
                    <span className="result-desc">
                      {[
                        profile.headline,
                        profile.city_code ? t(`cities.${profile.city_code}`) : null,
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  </span>
                  <span className="result-temp">
                    {profile.trust?.status === "AVAILABLE" ? trustText(profile.trust.value) : "—"}
                  </span>
                </button>
              ))
            )}
          </>
        )}
      </div>
    </div>
  );
}
