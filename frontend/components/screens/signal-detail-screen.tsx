"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { Avatar, Button, Chip } from "@/components/ui";
import { api, formatKrw, type Signal } from "@/lib/api";

import {
  LoadingBlock,
  palette,
  ScreenHeader,
  Sheet,
  trustText,
  useApiData,
  useRequireAuth,
} from "./shared";

export function SignalDetailScreen({ signalId }: { signalId: string }) {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const [applySheet, setApplySheet] = useState(false);
  const [applyRole, setApplyRole] = useState("");
  const [applyMessage, setApplyMessage] = useState("");
  const [applyState, setApplyState] = useState<"idle" | "busy" | "done" | "dup">("idle");
  const [deleteSheet, setDeleteSheet] = useState(false);
  const [deleteState, setDeleteState] = useState<"idle" | "busy" | "error">("idle");
  const meQuery = useApiData(() => api.me(), ready);
  const { data, error, loading, reload } = useApiData<Signal>(() => api.signal(signalId), ready);

  if (!ready || loading || !data) return <LoadingBlock error={error} reload={reload} />;

  const mine = meQuery.data?.profile?.id === data.requester?.id;
  const canManage = mine && (data.status === "DRAFT" || data.status === "OPEN");

  async function submitApply() {
    setApplyState("busy");
    try {
      await api.apply(signalId, {
        direction: "APPLICATION",
        role_id: applyRole || null,
        message: applyMessage,
      });
      setApplyState("done");
    } catch (err) {
      setApplyState((err as { code?: string }).code === "APPLICATION_DUPLICATE" ? "dup" : "idle");
    }
  }

  async function deleteSignal() {
    setDeleteState("busy");
    try {
      await api.deleteSignal(signalId);
      router.replace("/home");
    } catch {
      setDeleteState("error");
    }
  }

  return (
    <div style={{ paddingBottom: 28 }}>
      <ScreenHeader
        onBack={() => router.back()}
        subtitle={t(`types.${data.signal_type}`)}
        title={t("signalDetail.title")}
      />
      <div className="px">
        <div className="post__top" style={{ marginTop: 14 }}>
          {data.urgency === "CRITICAL" ? (
            <Chip tone="danger">
              {t(`types.${data.signal_type}`)} · {t("urgency.CRITICAL")}
            </Chip>
          ) : (
            <Chip tone="ai">{t(`types.${data.signal_type}`)}</Chip>
          )}
          {data.area_hint ? <Chip tone="neutral">{data.area_hint}</Chip> : null}
        </div>
        <h1 className="h1" style={{ marginTop: 10 }}>
          {data.raw_text}
        </h1>

        {data.disclaimers.length > 0 ? (
          <div className="warn-note">
            <span>⚠</span>
            <span>{data.disclaimers.join(" ")}</span>
          </div>
        ) : null}

        <div className="section-heading">{t("signalDetail.conditions")}</div>
        <div className="kv">
          <span>{t("signalDetail.type")}</span>
          <span>
            {t(`types.${data.signal_type}`)} · {data.team_cardinality}
          </span>
        </div>
        <div className="kv">
          <span>{t("signalDetail.duration")}</span>
          <span>
            {data.duration_weeks !== null
              ? t("write.weeks", { weeks: data.duration_weeks })
              : t("signalDetail.undecided")}
          </span>
        </div>
        <div className="kv">
          <span>{t("signalDetail.pay")}</span>
          <span>
            {!data.compensation.is_paid
              ? t("home.noPay")
              : data.compensation.amount_minor !== null
                ? formatKrw(data.compensation.amount_minor)
                : t("home.payNegotiable")}
          </span>
        </div>

        {data.roles.length > 0 ? (
          <>
            <div className="section-heading">{t("signalDetail.rolesTitle")}</div>
            {data.roles.map((role) => (
              <div key={role.id} className="kv">
                <span>{role.label}</span>
                <span className="mono">
                  {role.filled_count}/{role.headcount ?? "?"}
                </span>
              </div>
            ))}
          </>
        ) : null}

        {data.requester ? (
          <>
            <div className="section-heading">{t("signalDetail.requester")}</div>
            <button
              className="row"
              onClick={() => router.push(`/profiles/${data.requester?.id}`)}
              style={{
                background: "none",
                border: 0,
                cursor: "pointer",
                textAlign: "left",
                width: "100%",
              }}
              type="button"
            >
              <Avatar palette={palette(data.requester.palette)}>{data.requester.initials}</Avatar>
              <span style={{ flex: 1 }}>
                <span className="result-name">{data.requester.display_name}</span>
                <span className="result-desc">{data.requester.headline}</span>
              </span>
              <span className="result-temp">
                {data.requester.trust?.status === "AVAILABLE"
                  ? trustText(data.requester.trust.value)
                  : "—"}
              </span>
            </button>
          </>
        ) : null}

        <div style={{ marginTop: 18 }}>
          {mine ? (
            <Button onClick={() => router.push(`/who/${data.id}`)} type="button">
              {t("signalDetail.recommendations")}
            </Button>
          ) : (
            <Button onClick={() => setApplySheet(true)} type="button">
              {t("signalDetail.apply")}
            </Button>
          )}
        </div>
        {canManage ? (
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <Button
              onClick={() => router.push(`/signals/${data.id}/edit`)}
              type="button"
              variant="ghost"
            >
              {t("signalDetail.edit")}
            </Button>
            <Button onClick={() => setDeleteSheet(true)} type="button" variant="danger">
              {t("signalDetail.delete")}
            </Button>
          </div>
        ) : null}
        {mine ? (
          <p className="cap" style={{ marginTop: 8, textAlign: "center" }}>
            {t("signalDetail.mine")}
          </p>
        ) : null}
      </div>

      <Sheet
        onClose={() => setApplySheet(false)}
        open={applySheet}
        title={t("signalDetail.applySheetTitle")}
      >
        {applyState === "done" ? (
          <>
            <p style={{ color: "var(--t2)", fontSize: 13.5, lineHeight: 1.7, marginTop: 12 }}>
              {t("signalDetail.applyDone")}
            </p>
            <div style={{ marginTop: 16 }}>
              <Button onClick={() => setApplySheet(false)} type="button">
                {t("common.confirm")}
              </Button>
            </div>
          </>
        ) : (
          <>
            {data.roles.length > 0 ? (
              <div className="field">
                <label htmlFor="apply-role">{t("who.inviteRole")}</label>
                <select
                  id="apply-role"
                  onChange={(event) => setApplyRole(event.target.value)}
                  value={applyRole}
                >
                  <option value="">{t("who.roleNone")}</option>
                  {data.roles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.label}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}
            <div className="field">
              <label htmlFor="apply-message">{t("who.inviteMessage")}</label>
              <textarea
                id="apply-message"
                onChange={(event) => setApplyMessage(event.target.value)}
                placeholder={t("signalDetail.applyMessagePlaceholder")}
                rows={3}
                value={applyMessage}
              />
            </div>
            {applyState === "dup" ? (
              <div className="form-error">{t("who.alreadyInvited")}</div>
            ) : null}
            <div style={{ marginTop: 16 }}>
              <Button disabled={applyState === "busy"} onClick={submitApply} type="button">
                {t("signalDetail.apply")}
              </Button>
            </div>
          </>
        )}
      </Sheet>

      <Sheet
        onClose={() => {
          if (deleteState !== "busy") {
            setDeleteSheet(false);
            setDeleteState("idle");
          }
        }}
        open={deleteSheet}
        subtitle={t("signalDetail.deleteDescription")}
        title={t("signalDetail.deleteTitle")}
      >
        {deleteState === "error" ? (
          <div className="form-error">{t("signalDetail.deleteFailed")}</div>
        ) : null}
        <div style={{ display: "flex", gap: 8, marginTop: 18 }}>
          <Button
            disabled={deleteState === "busy"}
            onClick={() => setDeleteSheet(false)}
            type="button"
            variant="ghost"
          >
            {t("common.cancel")}
          </Button>
          <Button
            disabled={deleteState === "busy"}
            onClick={deleteSignal}
            type="button"
            variant="danger"
          >
            {deleteState === "busy" ? t("signalDetail.deleting") : t("signalDetail.deleteConfirm")}
          </Button>
        </div>
      </Sheet>
    </div>
  );
}
