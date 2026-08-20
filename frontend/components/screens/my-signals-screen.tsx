"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { Button, Card, Chip, type ChipTone } from "@/components/ui";
import { api, type Signal } from "@/lib/api";

import {
  LoadingBlock,
  ScreenHeader,
  Sheet,
  useApiData,
  useRequireAuth,
  useTimeAgo,
} from "./shared";

type Filter = "all" | "editable" | "locked";

function isEditable(signal: Signal) {
  return signal.status === "DRAFT" || signal.status === "OPEN";
}

function statusTone(status: string): ChipTone {
  if (status === "OPEN") return "verified";
  if (status === "IN_PROGRESS") return "ai";
  if (status === "DRAFT") return "outline";
  if (status === "CANCELLED" || status === "EXPIRED") return "danger";
  return "neutral";
}

export function MySignalsScreen() {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const timeAgo = useTimeAgo();
  const [filter, setFilter] = useState<Filter>("all");
  const [deleteTarget, setDeleteTarget] = useState<Signal | null>(null);
  const [deleteState, setDeleteState] = useState<"idle" | "busy" | "error">("idle");
  const { data, error, loading, reload, setData } = useApiData(
    () => api.signals({ mine: true }),
    ready,
  );

  const filtered = useMemo(() => {
    if (!data) return [];
    if (filter === "editable") return data.filter(isEditable);
    if (filter === "locked") return data.filter((signal) => !isEditable(signal));
    return data;
  }, [data, filter]);

  if (!ready || loading || !data) return <LoadingBlock error={error} reload={reload} />;

  async function confirmDelete() {
    if (!deleteTarget) return;
    setDeleteState("busy");
    try {
      await api.deleteSignal(deleteTarget.id);
      setData((current) => current?.filter((signal) => signal.id !== deleteTarget.id) ?? null);
      setDeleteTarget(null);
      setDeleteState("idle");
    } catch {
      setDeleteState("error");
    }
  }

  function closeDeleteSheet() {
    if (deleteState === "busy") return;
    setDeleteTarget(null);
    setDeleteState("idle");
  }

  return (
    <div style={{ paddingBottom: 28 }}>
      <ScreenHeader
        title={t("mySignals.title")}
        subtitle={t("mySignals.subtitle")}
        trailing={
          <Button
            onClick={() => router.push("/write")}
            size="small"
            style={{ minHeight: 34, padding: "7px 11px", width: "auto" }}
            type="button"
          >
            {t("mySignals.create")}
          </Button>
        }
      />

      <div className="px">
        <Card style={{ marginTop: 14 }}>
          <div className="signal-manage-summary">
            <span>
              <b>{data.filter(isEditable).length}</b>
              <small>{t("mySignals.editableCount")}</small>
            </span>
            <span>
              <b>{data.filter((signal) => !isEditable(signal)).length}</b>
              <small>{t("mySignals.lockedCount")}</small>
            </span>
            <span>
              <b>{data.length}</b>
              <small>{t("mySignals.totalCount")}</small>
            </span>
          </div>
        </Card>

        <div className="tab-row" style={{ marginTop: 12 }}>
          {(["all", "editable", "locked"] as const).map((value) => (
            <button
              data-active={filter === value}
              key={value}
              onClick={() => setFilter(value)}
              type="button"
            >
              {t(`mySignals.filter.${value}`)}
            </button>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className="list-empty">
            <p>{t(filter === "all" ? "mySignals.empty" : "mySignals.filterEmpty")}</p>
            {filter === "all" ? (
              <Button onClick={() => router.push("/write")} size="small" type="button">
                {t("mySignals.createFirst")}
              </Button>
            ) : null}
          </div>
        ) : (
          filtered.map((signal) => (
            <Card className="signal-manage-card" key={signal.id}>
              <div className="post__top">
                <Chip tone="ai">{t(`types.${signal.signal_type}`)}</Chip>
                <Chip tone={statusTone(signal.status)}>
                  {t(`mySignals.status.${signal.status}` as never)}
                </Chip>
                <span className="post__when">
                  {timeAgo(signal.published_at ?? signal.created_at)}
                </span>
              </div>

              <button
                className="signal-manage-title"
                onClick={() => router.push(`/signals/${signal.id}`)}
                type="button"
              >
                {signal.raw_text}
              </button>

              <div className="post__meta">
                {signal.roles.length > 0
                  ? signal.roles.map((role) => role.label).join(" · ")
                  : t("mySignals.noRoles")}
                {` · ${signal.team_cardinality}`}
              </div>

              <div className="signal-manage-actions">
                <Button
                  onClick={() => router.push(`/signals/${signal.id}`)}
                  size="small"
                  type="button"
                  variant="ghost"
                >
                  {t("mySignals.view")}
                </Button>
                {isEditable(signal) ? (
                  <>
                    <Button
                      onClick={() => router.push(`/signals/${signal.id}/edit`)}
                      size="small"
                      type="button"
                      variant="ghost"
                    >
                      {t("signalDetail.edit")}
                    </Button>
                    <Button
                      onClick={() => setDeleteTarget(signal)}
                      size="small"
                      type="button"
                      variant="danger"
                    >
                      {t("signalDetail.delete")}
                    </Button>
                  </>
                ) : null}
              </div>
              {!isEditable(signal) ? (
                <p className="cap signal-manage-lock-note">{t("mySignals.lockedNotice")}</p>
              ) : null}
            </Card>
          ))
        )}
      </div>

      <Sheet
        onClose={closeDeleteSheet}
        open={deleteTarget !== null}
        subtitle={t("signalDetail.deleteDescription")}
        title={t("signalDetail.deleteTitle")}
      >
        {deleteTarget ? <p className="signal-delete-preview">{deleteTarget.raw_text}</p> : null}
        {deleteState === "error" ? (
          <div className="form-error">{t("signalDetail.deleteFailed")}</div>
        ) : null}
        <div className="signal-manage-actions" style={{ marginTop: 18 }}>
          <Button
            disabled={deleteState === "busy"}
            onClick={closeDeleteSheet}
            type="button"
            variant="ghost"
          >
            {t("common.cancel")}
          </Button>
          <Button
            disabled={deleteState === "busy"}
            onClick={confirmDelete}
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
