"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { Chip } from "@/components/ui";
import { api, type Signal } from "@/lib/api";

import {
  LoadingBlock,
  trustFillPercent,
  trustText,
  useApiData,
  useRequireAuth,
  useTimeAgo,
} from "./shared";

const KINDS = ["ALL", "HELP", "WORK", "CIRCLE", "BOOKING"] as const;

function SignalCard({ signal }: { signal: Signal }) {
  const t = useTranslations();
  const router = useRouter();
  const timeAgo = useTimeAgo();
  const title = signal.raw_text.length > 64 ? `${signal.raw_text.slice(0, 64)}…` : signal.raw_text;
  const metaParts: string[] = [signal.team_cardinality];
  if (!signal.compensation.is_paid) metaParts.push(t("home.noPay"));
  else if (signal.compensation.amount_minor === null) metaParts.push(t("home.payNegotiable"));
  if (signal.signal_type === "CIRCLE" && signal.accepted_count > 0) {
    metaParts.push(t("home.participants", { count: signal.accepted_count }));
  }
  return (
    <button className="post" onClick={() => router.push(`/signals/${signal.id}`)} type="button">
      <div className="post__top">
        {signal.urgency === "CRITICAL" ? (
          <Chip tone="danger">
            {t(`types.${signal.signal_type}`)} · {t("urgency.CRITICAL")}
          </Chip>
        ) : (
          <Chip tone="ai">{t(`types.${signal.signal_type}`)}</Chip>
        )}
        {signal.requires_physical_presence ? (
          <Chip tone="neutral">{t("home.onsite")}</Chip>
        ) : (
          <Chip tone="neutral">{t("home.online")}</Chip>
        )}
        <span className="post__when">{timeAgo(signal.published_at)}</span>
      </div>
      <div className="post__title">{title}</div>
      <div className="post__meta">
        {metaParts.join(" · ")}
        {signal.accept_latency_seconds !== null &&
        signal.accept_latency_seconds < 600 &&
        signal.signal_type === "HELP" ? (
          <>
            {" · "}
            <b>{t("home.acceptedIn", { seconds: signal.accept_latency_seconds })}</b>
          </>
        ) : null}
      </div>
      {signal.member_faces.length > 0 ? (
        <div className="faces">
          {signal.member_faces.map((face, index) => (
            <span key={index} className={`avatar-face`} data-palette={face.palette}>
              {face.initials}
            </span>
          ))}
          {signal.accepted_count > signal.member_faces.length ? (
            <span data-palette="6">+{signal.accepted_count - signal.member_faces.length}</span>
          ) : null}
        </div>
      ) : null}
    </button>
  );
}

export function HomeScreen() {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const [kind, setKind] = useState<(typeof KINDS)[number]>("ALL");
  const { data, error, loading, reload } = useApiData(() => api.home(), ready);

  if (!ready || loading || !data) return <LoadingBlock error={error} reload={reload} />;

  const trust = data.profile?.trust;
  const filtered =
    kind === "ALL" ? data.signals : data.signals.filter((signal) => signal.signal_type === kind);

  return (
    <div className="px" style={{ paddingBottom: 24 }}>
      <div className="cap" style={{ marginTop: 12 }}>
        {data.profile?.city_code ? t(`cities.${data.profile.city_code}`) : "PANGAEA"}
      </div>
      <h1 className="h1" style={{ marginTop: 6 }}>
        {t("home.title")}
      </h1>

      <button className="temp" onClick={() => router.push("/done")} type="button">
        <span className="temp__value">
          {trust?.status === "AVAILABLE" ? trustText(trust.value) : "—"}
        </span>
        <span className="temp__meta">
          <span className="temp__label">
            {trust?.status === "AVAILABLE" ? t("home.trustLabel") : t("home.trustPending")}
          </span>
          <span className="tbar">
            <span className="tfill" style={{ width: `${trustFillPercent(trust?.value)}%` }} />
          </span>
        </span>
        <span className="temp__go">{t("home.trustHistory")}</span>
      </button>

      <button className="ask" onClick={() => router.push("/write")} type="button">
        <div className="ask__question">{t("home.askQuestion")}</div>
        <div className="ask__hint">{t("home.askHint")}</div>
        <div className="ask__footer">
          <span className="ask__spark">✦</span>
          <b>{t("home.askBadge")}</b>
        </div>
      </button>

      <button className="findbar" onClick={() => router.push("/find")} type="button">
        <span>⌕</span>
        <span>{t("home.findDirect")}</span>
      </button>

      <div className="kinds">
        {KINDS.map((value) => (
          <button
            key={value}
            data-active={kind === value}
            onClick={() => setKind(value)}
            type="button"
          >
            {value === "ALL" ? t("home.kindAll") : t(`types.${value}`)}
          </button>
        ))}
      </div>

      <div className="section-heading">{t("home.awakeTitle")}</div>
      <div className="strip">
        {data.cities.map((city) => (
          <div key={city.code} className="city" data-state={city.state}>
            <div className="city__name">
              <span className="dot" data-state={city.state} />
              {t(`cities.${city.code}`)}
            </div>
            <div className="city__time">{city.local_time}</div>
            <div className="city__status">
              {city.member_count > 0
                ? t("home.membersCount", { count: city.member_count })
                : city.state === "SLEEP"
                  ? t("home.stateSleep")
                  : city.state === "SLOW"
                    ? t("home.stateSlow")
                    : t("home.stateAwake")}
            </div>
          </div>
        ))}
      </div>

      <div className="screen-gap" />
      <div className="section-heading">
        {t("home.feedTitle")}{" "}
        <small className="mono" style={{ color: "var(--t3)", fontSize: 11, fontWeight: 400 }}>
          {filtered.length}
        </small>
      </div>
      {filtered.length === 0 ? (
        <div className="list-empty">{t("home.feedEmpty")}</div>
      ) : (
        filtered.map((signal) => <SignalCard key={signal.id} signal={signal} />)
      )}
    </div>
  );
}
