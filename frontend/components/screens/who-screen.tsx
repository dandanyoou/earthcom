"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { Avatar, Button, Chip, Fold } from "@/components/ui";
import { api, type Candidate, type Signal } from "@/lib/api";

import {
  LoadingBlock,
  palette,
  ScreenHeader,
  Sheet,
  trustText,
  useApiData,
  useRequireAuth,
} from "./shared";

function CandidateCard({
  candidate,
  onInvite,
}: {
  candidate: Candidate;
  onInvite: (candidate: Candidate) => void;
}) {
  const t = useTranslations();
  const router = useRouter();
  const profile = candidate.profile;
  const roleLine = [
    profile.city_code ? t(`cities.${profile.city_code}`) : null,
    profile.local_time,
    profile.headline,
  ]
    .filter(Boolean)
    .join(" · ");
  return (
    <div className={candidate.rank === 1 ? "who who--top" : "who"}>
      <div className="who__head">
        <Avatar palette={palette(profile.palette)}>{profile.initials}</Avatar>
        <span>
          <span className="who__name">
            {profile.display_name}
            {profile.city_code ? <span className="cc">{profile.locale.toUpperCase()}</span> : null}
          </span>
          <span className="who__role" style={{ display: "block" }}>
            {roleLine}
          </span>
        </span>
        <span className="who__value">
          <b>{profile.trust?.status === "AVAILABLE" ? trustText(profile.trust.value) : "—"}</b>
          <small>{t("who.rankLabel", { rank: candidate.rank })}</small>
        </span>
      </div>
      <div className="who__chips">
        {candidate.role_fit === "DIFFERENT" ? (
          <Chip tone="outline">{t("who.differentChip")}</Chip>
        ) : (
          <>
            {candidate.verified_relevant_count > 0 ? (
              <Chip tone="verified">
                {t("who.verifiedChip", { count: candidate.verified_relevant_count })}
              </Chip>
            ) : null}
            {candidate.overlap_hours_per_day > 0 ? (
              <Chip tone="neutral">
                {t("who.overlapChip", { hours: candidate.overlap_hours_per_day })}
              </Chip>
            ) : null}
          </>
        )}
      </div>
      {candidate.why ? (
        <div className="why">
          <b>{t("who.whyTitle")}</b>
          <ul>
            <li>{candidate.why}</li>
          </ul>
        </div>
      ) : null}
      {candidate.role_fit === "DIFFERENT" ? (
        <div style={{ color: "var(--t3)", fontSize: 11.5, lineHeight: 1.65, marginTop: 10 }}>
          {t("who.differentNote")}
        </div>
      ) : null}
      <div className="pair" style={{ marginTop: 13 }}>
        <Button onClick={() => router.push(`/profiles/${profile.id}`)} size="small" variant="ghost">
          {t("common.viewProfile")}
        </Button>
        {candidate.role_fit === "DIFFERENT" ? (
          <Button size="small" variant="ghost">
            {t("common.later")}
          </Button>
        ) : (
          <Button onClick={() => onInvite(candidate)} size="small">
            {t("who.invite")}
          </Button>
        )}
      </div>
    </div>
  );
}

export function WhoScreen({ signalId }: { signalId: string }) {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const [inviteTarget, setInviteTarget] = useState<Candidate | null>(null);
  const [inviteRole, setInviteRole] = useState<string>("");
  const [inviteMessage, setInviteMessage] = useState("");
  const [inviteState, setInviteState] = useState<"idle" | "busy" | "done" | "dup">("idle");
  const signalQuery = useApiData<Signal>(() => api.signal(signalId), ready);
  const { data, error, loading, reload } = useApiData(() => api.recommendations(signalId), ready);

  if (!ready || loading || !data) return <LoadingBlock error={error} reload={reload} />;

  async function sendInvite() {
    if (!inviteTarget) return;
    setInviteState("busy");
    try {
      await api.apply(signalId, {
        direction: "INVITATION",
        invitee_profile_id: inviteTarget.profile.id,
        role_id: inviteRole || null,
        message: inviteMessage,
      });
      setInviteState("done");
    } catch (err) {
      setInviteState((err as { code?: string }).code === "APPLICATION_DUPLICATE" ? "dup" : "idle");
    }
  }

  const criteriaKeys = data.explain.criteria;

  return (
    <div style={{ paddingBottom: 28 }}>
      <ScreenHeader
        onBack={() => router.back()}
        subtitle={t("who.foundCount", { count: data.candidates.length })}
        title={t("who.title")}
      />
      <div className="px">
        <Fold className="rank-fold" style={{ marginTop: 12 }} summary={t("who.rankFoldTitle")}>
          {criteriaKeys.map((key, index) => (
            <div key={key} className="fold__row">
              <i>{index + 1}</i>
              <span>{t(`who.criteria.${key}`)}</span>
            </div>
          ))}
          <div className="fold__note">
            <b>{t("who.cultureExcluded")}</b>
            <br />
            {t("who.trustExcluded")}
          </div>
        </Fold>

        {data.candidates.length === 0 ? (
          <div className="list-empty">{t("who.empty")}</div>
        ) : (
          data.candidates.map((candidate) => (
            <CandidateCard
              key={candidate.profile.id}
              candidate={candidate}
              onInvite={(target) => {
                setInviteTarget(target);
                setInviteRole("");
                setInviteMessage("");
                setInviteState("idle");
              }}
            />
          ))
        )}
      </div>

      <Sheet
        onClose={() => setInviteTarget(null)}
        open={inviteTarget !== null}
        subtitle={inviteTarget?.profile.display_name}
        title={t("who.inviteSheetTitle")}
      >
        {inviteState === "done" ? (
          <>
            <p style={{ color: "var(--t2)", fontSize: 13.5, lineHeight: 1.7, marginTop: 12 }}>
              {t("who.inviteDone")}
            </p>
            <div style={{ marginTop: 16 }}>
              <Button onClick={() => setInviteTarget(null)} type="button">
                {t("common.confirm")}
              </Button>
            </div>
          </>
        ) : (
          <>
            <div className="field">
              <label htmlFor="invite-role">{t("who.inviteRole")}</label>
              <select
                id="invite-role"
                onChange={(event) => setInviteRole(event.target.value)}
                value={inviteRole}
              >
                <option value="">{t("who.roleNone")}</option>
                {(signalQuery.data?.roles ?? []).map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="invite-message">{t("who.inviteMessage")}</label>
              <textarea
                id="invite-message"
                onChange={(event) => setInviteMessage(event.target.value)}
                placeholder={t("who.inviteMessagePlaceholder")}
                rows={3}
                value={inviteMessage}
              />
            </div>
            {inviteState === "dup" ? (
              <div className="form-error">{t("who.alreadyInvited")}</div>
            ) : null}
            <div style={{ marginTop: 16 }}>
              <Button disabled={inviteState === "busy"} onClick={sendInvite} type="button">
                {t("who.inviteSend")}
              </Button>
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}
