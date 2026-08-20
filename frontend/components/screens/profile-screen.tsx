"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { Avatar, Chip } from "@/components/ui";
import { api, type ProfileDetail } from "@/lib/api";

import {
  LoadingBlock,
  palette,
  ScreenHeader,
  trustText,
  useApiData,
  useRequireAuth,
} from "./shared";

export function ProfileScreen({ profileId }: { profileId: string }) {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const { data, error, loading, reload } = useApiData<ProfileDetail>(
    () => api.profile(profileId),
    ready,
  );

  if (!ready || loading || !data) return <LoadingBlock error={error} reload={reload} />;

  return (
    <div style={{ paddingBottom: 28 }}>
      <ScreenHeader onBack={() => router.back()} title={data.display_name} />
      <div className="px">
        <div className="who" style={{ marginTop: 14 }}>
          <div className="who__head">
            <Avatar palette={palette(data.palette)}>{data.initials}</Avatar>
            <span>
              <span className="who__name">
                {data.display_name}
                <span className="cc">{data.locale.toUpperCase()}</span>
              </span>
              <span className="who__role" style={{ display: "block" }}>
                {[
                  data.city_code ? t(`cities.${data.city_code}`) : null,
                  data.local_time,
                  data.headline,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </span>
            </span>
            <span className="who__value">
              <b>{data.trust?.status === "AVAILABLE" ? trustText(data.trust.value) : "—"}</b>
              <small>{t("profile.trustLabel")}</small>
            </span>
          </div>
          <div className="who__chips">
            {data.verified_count > 0 ? (
              <Chip tone="verified">{t("who.verifiedChip", { count: data.verified_count })}</Chip>
            ) : null}
            {data.overlap_hours_per_day > 0 ? (
              <Chip tone="neutral">
                {t("who.overlapChip", { hours: data.overlap_hours_per_day })}
              </Chip>
            ) : null}
          </div>
          {data.bio ? (
            <p style={{ color: "var(--t2)", fontSize: 13, lineHeight: 1.7, marginTop: 12 }}>
              {data.bio}
            </p>
          ) : null}
        </div>

        <div className="section-heading">{t("profile.skills")}</div>
        <div className="inline-chips" style={{ marginTop: 0 }}>
          {data.skills.map((skill) => (
            <Chip key={skill.normalized} tone={skill.verified ? "verified" : "neutral"}>
              {skill.name}
              {skill.years ? ` · ${t("profile.years", { years: skill.years })}` : ""}
              {skill.verified ? ` · ${t("profile.verified")}` : ""}
            </Chip>
          ))}
        </div>

        <div className="section-heading">{t("profile.languages")}</div>
        <div className="inline-chips" style={{ marginTop: 0 }}>
          {data.languages.map((language) => (
            <Chip key={language.code} tone="neutral">
              {language.code.toUpperCase()} · {t(`profile.proficiency.${language.proficiency}`)}
            </Chip>
          ))}
        </div>

        {data.availability.length > 0 ? (
          <>
            <div className="section-heading">{t("profile.availability")}</div>
            {data.availability.slice(0, 5).map((rule, index) => (
              <div key={index} className="kv">
                <span>{t(`profile.weekdays.${rule.weekday}`)}</span>
                <span className="mono">
                  {rule.start}–{rule.end} · {rule.timezone}
                </span>
              </div>
            ))}
          </>
        ) : null}

        <div className="section-heading">{t("profile.reviews")}</div>
        {data.reviews.length === 0 ? (
          <div className="list-empty">{t("profile.reviewEmpty")}</div>
        ) : (
          data.reviews.map((review) => (
            <div key={review.id} className="row">
              <Chip
                tone={
                  review.rating === "POSITIVE"
                    ? "verified"
                    : review.rating === "NEGATIVE"
                      ? "danger"
                      : "neutral"
                }
              >
                {t(
                  review.rating === "POSITIVE"
                    ? "done.ratingPositive"
                    : review.rating === "NEGATIVE"
                      ? "done.ratingNegative"
                      : "done.ratingNeutral",
                )}
              </Chip>
              <span style={{ flex: 1 }}>
                <span className="result-name">{review.reviewer_name}</span>
                {review.comment ? <span className="result-desc">{review.comment}</span> : null}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
