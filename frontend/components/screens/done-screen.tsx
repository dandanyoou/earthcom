"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { Avatar, Button, Chip } from "@/components/ui";
import { api, formatKrw, type Collaboration } from "@/lib/api";

import {
  LoadingBlock,
  palette,
  ScreenHeader,
  Sheet,
  trustText,
  useApiData,
  useRequireAuth,
} from "./shared";

function DepositPanel({
  collaboration,
  onChanged,
}: {
  collaboration: Collaboration;
  onChanged: () => void;
}) {
  const t = useTranslations("done");
  const [amount, setAmount] = useState("100000");
  const [busy, setBusy] = useState(false);
  const deposit = collaboration.deposit;

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    try {
      await action();
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  if (!collaboration.deposit_applies) return null;

  if (!deposit) {
    return (
      <div className="who" style={{ marginTop: 12 }}>
        <b style={{ fontSize: 14 }}>{t("depositTitle")}</b>
        <div className="field">
          <label htmlFor="deposit-amount">{t("depositAmount")}</label>
          <input
            id="deposit-amount"
            min={1}
            onChange={(event) => setAmount(event.target.value)}
            type="number"
            value={amount}
          />
        </div>
        <div style={{ marginTop: 12 }}>
          <Button
            disabled={busy || !Number(amount)}
            onClick={() => run(() => api.proposeDeposit(collaboration.id, Number(amount)))}
            size="small"
            type="button"
          >
            {t("depositPropose")}
          </Button>
        </div>
        <p className="cap" style={{ marginTop: 10 }}>
          {t("depositNotice")}
        </p>
      </div>
    );
  }

  const me = deposit.parties.find((party) => party.me);
  const statusKey = `status${deposit.status}` as
    "statusPROPOSED" | "statusAGREED" | "statusFUNDING" | "statusLOCKED" | "statusREFUNDED";

  return (
    <div className="who" style={{ marginTop: 12 }}>
      <div style={{ alignItems: "center", display: "flex", gap: 8 }}>
        <b style={{ fontSize: 14 }}>{t("depositTitle")}</b>
        <Chip
          tone={
            deposit.status === "REFUNDED" || deposit.status === "LOCKED" ? "verified" : "neutral"
          }
        >
          {t(statusKey)}
        </Chip>
        <Chip tone="outline">{t("depositSandbox")}</Chip>
      </div>
      <div className="kv" style={{ marginTop: 8 }}>
        <span>{t("depositAmount")}</span>
        <span className="mono">{formatKrw(deposit.amount_minor_per_party)}</span>
      </div>
      {deposit.parties.map((party) => (
        <div key={party.profile_id} className="kv">
          <span>{party.name}</span>
          <span className="mono" style={{ color: "var(--t3)", fontSize: 11.5 }}>
            {[
              party.agreed ? t("agreedMark") : null,
              party.funded ? t("fundedMark") : null,
              party.refunded ? t("refundedMark") : null,
            ]
              .filter(Boolean)
              .join(" · ") || "—"}
          </span>
        </div>
      ))}
      {me && !me.agreed && (deposit.status === "PROPOSED" || deposit.status === "AGREED") ? (
        <div style={{ marginTop: 12 }}>
          <Button
            disabled={busy}
            onClick={() => run(() => api.agreeDeposit(deposit.id))}
            size="small"
            type="button"
          >
            {t("depositAgree")}
          </Button>
        </div>
      ) : null}
      {me && me.agreed && !me.funded && ["AGREED", "FUNDING"].includes(deposit.status) ? (
        <div style={{ marginTop: 12 }}>
          <Button
            disabled={busy}
            onClick={() => run(() => api.fundDeposit(deposit.id))}
            size="small"
            type="button"
          >
            {t("depositFund")}
          </Button>
        </div>
      ) : null}
      <p className="cap" style={{ marginTop: 10 }}>
        {t("depositNotice")}
      </p>
    </div>
  );
}

function CollaborationDetail({
  collaboration,
  onChanged,
}: {
  collaboration: Collaboration;
  onChanged: () => void;
}) {
  const t = useTranslations();
  const router = useRouter();
  const [reviewOpen, setReviewOpen] = useState(false);
  const [reviewTarget, setReviewTarget] = useState("");
  const [rating, setRating] = useState("POSITIVE");
  const [comment, setComment] = useState("");
  const [reviewDone, setReviewDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const completed = collaboration.status === "COMPLETED";
  const memberCount = collaboration.members.length;
  const refunded = collaboration.deposit?.status === "REFUNDED";

  async function confirm() {
    setBusy(true);
    try {
      await api.confirmCompletion(collaboration.id);
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  async function submitReview() {
    setBusy(true);
    try {
      await api.createReview(collaboration.id, {
        reviewee_profile_id: reviewTarget,
        rating,
        tags: [],
        comment,
      });
      setReviewDone(true);
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      {collaboration.deliverables.length > 0 ? (
        <>
          <div className="section-heading">
            {t("done.deliverables")}{" "}
            <small className="mono" style={{ color: "var(--t3)", fontSize: 11, fontWeight: 400 }}>
              {collaboration.deliverables.length}
            </small>
          </div>
          {collaboration.deliverables.map((file) => (
            <div key={file.id} className="file">
              <span className="file__ok">✓</span>
              <span>{file.file_name}</span>
              <span className="file__hash">{file.hash_prefix}</span>
            </div>
          ))}
          <div className="cap" style={{ marginTop: 10 }}>
            {t("done.hashNote")}
          </div>
        </>
      ) : null}

      {completed && refunded && collaboration.deposit ? (
        <div className="dep">
          <div className="dep__value">{formatKrw(collaboration.deposit.total_minor)}</div>
          <div className="dep__label">{t("done.depositRefund")}</div>
          <ul>
            <li>
              {t("done.depositLine1", {
                count: memberCount,
                amount: formatKrw(collaboration.deposit.amount_minor_per_party),
              })}
            </li>
            <li>{t("done.depositLine2")}</li>
            <li>
              <b>{t("done.depositLine3")}</b>
            </li>
          </ul>
        </div>
      ) : (
        <DepositPanel collaboration={collaboration} onChanged={onChanged} />
      )}

      <div className="section-heading">{completed ? t("done.trustUp") : t("done.trustNow")}</div>
      {collaboration.members.map((member) => (
        <div key={member.profile_id} className="row">
          <Avatar
            palette={palette(member.palette)}
            style={{ borderRadius: 11, fontSize: 11.5, height: 34, width: 34 }}
          >
            {member.me ? t("common.me") : member.initials}
          </Avatar>
          <span style={{ flex: 1, fontSize: 13.5, fontWeight: 600 }}>
            {member.name} · {member.role_label}
          </span>
          <span className="mono" style={{ color: "var(--temp)" }}>
            {completed && member.trust.before_completion !== null
              ? `${member.trust.before_completion.toFixed(1)} → ${trustText(member.trust.value)}`
              : trustText(member.trust.value)}
          </span>
        </div>
      ))}

      {!completed ? (
        <div style={{ marginTop: 16 }}>
          <Button
            disabled={
              busy || collaboration.my_confirmation || collaboration.status === "DEPOSIT_PENDING"
            }
            onClick={confirm}
            type="button"
          >
            {collaboration.my_confirmation ? t("done.waitingOthers") : t("done.confirmCompletion")}
          </Button>
          <p className="cap" style={{ marginTop: 8, textAlign: "center" }}>
            {t("done.confirmedCount", {
              confirmed: collaboration.confirmed_count,
              total: memberCount,
            })}
          </p>
        </div>
      ) : (
        <>
          <div className="seal">
            <b>4 / 4</b>
            <span>{t("done.sealCrossed")}</span>
          </div>
          <div style={{ padding: "0 12px", textAlign: "center" }}>
            <div className="h2">{t("done.crewDissolved")}</div>
            <p style={{ color: "var(--t3)", fontSize: 12.5, lineHeight: 1.8, marginTop: 9 }}>
              {t("done.dissolvedNote")}
            </p>
          </div>
          {collaboration.my_review_targets.length > 0 ? (
            <div style={{ marginTop: 14 }}>
              <Button
                onClick={() => {
                  setReviewTarget(collaboration.my_review_targets[0]);
                  setReviewDone(false);
                  setReviewOpen(true);
                }}
                type="button"
                variant="ghost"
              >
                {t("done.review")}
              </Button>
            </div>
          ) : null}
        </>
      )}

      {collaboration.conversation_id ? (
        <div style={{ marginTop: 10 }}>
          <Button
            onClick={() => router.push(`/chat/${collaboration.conversation_id}`)}
            type="button"
            variant="ghost"
          >
            {t("applications.goChat")}
          </Button>
        </div>
      ) : null}

      <Sheet
        onClose={() => setReviewOpen(false)}
        open={reviewOpen}
        title={t("done.reviewSheetTitle")}
      >
        {reviewDone ? (
          <>
            <p style={{ color: "var(--t2)", fontSize: 13.5, marginTop: 12 }}>
              {t("done.reviewDone")}
            </p>
            <div style={{ marginTop: 14 }}>
              <Button onClick={() => setReviewOpen(false)} type="button">
                {t("common.confirm")}
              </Button>
            </div>
          </>
        ) : (
          <>
            <div className="field">
              <label htmlFor="review-target">{t("done.reviewTarget")}</label>
              <select
                id="review-target"
                onChange={(event) => setReviewTarget(event.target.value)}
                value={reviewTarget}
              >
                {collaboration.my_review_targets.map((targetId) => {
                  const member = collaboration.members.find(
                    (candidate) => candidate.profile_id === targetId,
                  );
                  return (
                    <option key={targetId} value={targetId}>
                      {member?.name ?? targetId}
                    </option>
                  );
                })}
              </select>
            </div>
            <div className="rating-row">
              {(["POSITIVE", "NEUTRAL", "NEGATIVE"] as const).map((value) => (
                <button
                  key={value}
                  data-active={rating === value}
                  onClick={() => setRating(value)}
                  type="button"
                >
                  {t(
                    value === "POSITIVE"
                      ? "done.ratingPositive"
                      : value === "NEGATIVE"
                        ? "done.ratingNegative"
                        : "done.ratingNeutral",
                  )}
                </button>
              ))}
            </div>
            <div className="field">
              <label htmlFor="review-comment">{t("done.reviewComment")}</label>
              <textarea
                id="review-comment"
                maxLength={500}
                onChange={(event) => setComment(event.target.value)}
                rows={3}
                value={comment}
              />
            </div>
            <div style={{ marginTop: 14 }}>
              <Button disabled={busy || !reviewTarget} onClick={submitReview} type="button">
                {t("done.reviewSubmit")}
              </Button>
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}

export function DoneScreen() {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data, error, loading, reload } = useApiData(() => api.collaborations(), ready);

  if (!ready || loading || !data) return <LoadingBlock error={error} reload={reload} />;

  const selected = data.find((collaboration) => collaboration.id === selectedId) ?? data[0] ?? null;

  return (
    <div style={{ paddingBottom: 28 }}>
      <ScreenHeader
        subtitle={
          selected?.duration_weeks
            ? t("done.weeksLater", { weeks: selected.duration_weeks })
            : t("done.subtitle")
        }
        title={t("done.title")}
      />
      <div className="px">
        {data.length === 0 ? (
          <div className="list-empty">
            {t("done.noCrew")}
            <div style={{ marginTop: 12 }}>
              <Button onClick={() => router.push("/write")} size="small" type="button">
                {t("write.title")}
              </Button>
            </div>
          </div>
        ) : (
          <>
            {data.length > 1 ? (
              <div className="tab-row">
                {data.map((collaboration) => (
                  <button
                    key={collaboration.id}
                    data-active={collaboration.id === selected?.id}
                    onClick={() => setSelectedId(collaboration.id)}
                    type="button"
                  >
                    {collaboration.title}
                  </button>
                ))}
              </div>
            ) : null}
            {selected ? (
              <div style={{ marginTop: 6 }}>
                <div className="post__top" style={{ marginTop: 10 }}>
                  <Chip tone={selected.status === "COMPLETED" ? "verified" : "neutral"}>
                    {t(`done.statusChip.${selected.status}` as never)}
                  </Chip>
                  <span className="post__when">{selected.title}</span>
                </div>
                <CollaborationDetail collaboration={selected} onChanged={reload} />
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
