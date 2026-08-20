"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { Avatar, Button, Chip } from "@/components/ui";
import { api, type ApplicationItem } from "@/lib/api";

import { LoadingBlock, palette, ScreenHeader, useApiData, useRequireAuth } from "./shared";

export function ApplicationsScreen() {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const [box, setBox] = useState<"received" | "sent">("received");
  const { data, error, loading, reload } = useApiData(() => api.applications(box), ready, box);
  const [busyId, setBusyId] = useState<string | null>(null);

  if (!ready) return null;

  async function act(id: string, action: "accept" | "reject" | "withdraw") {
    setBusyId(id);
    try {
      if (action === "accept") {
        const result = await api.acceptApplication(id);
        if (result.conversation_id) {
          router.push(`/chat/${result.conversation_id}`);
          return;
        }
      } else if (action === "reject") await api.rejectApplication(id);
      else await api.withdrawApplication(id);
      reload();
    } finally {
      setBusyId(null);
    }
  }

  function statusChip(item: ApplicationItem) {
    const key = `status${item.status}` as
      "statusPENDING" | "statusACCEPTED" | "statusREJECTED" | "statusWITHDRAWN";
    return (
      <Chip tone={item.status === "ACCEPTED" ? "verified" : "neutral"}>
        {t(`applications.${key}`)}
      </Chip>
    );
  }

  return (
    <div style={{ paddingBottom: 28 }}>
      <ScreenHeader onBack={() => router.push("/home")} title={t("applications.title")} />
      <div className="px">
        <div className="tab-row">
          <button data-active={box === "received"} onClick={() => setBox("received")} type="button">
            {t("applications.received")}
          </button>
          <button data-active={box === "sent"} onClick={() => setBox("sent")} type="button">
            {t("applications.sent")}
          </button>
        </div>
        {loading || !data ? (
          <LoadingBlock error={error} reload={reload} />
        ) : data.length === 0 ? (
          <div className="list-empty">{t("applications.empty")}</div>
        ) : (
          data.map((item) => (
            <div key={item.id} className="who" style={{ marginTop: 12 }}>
              <div className="who__head">
                {item.applicant ? (
                  <Avatar palette={palette(item.applicant.palette)}>
                    {item.applicant.initials}
                  </Avatar>
                ) : null}
                <span style={{ minWidth: 0 }}>
                  <span className="who__name">{item.applicant?.display_name}</span>
                  <span className="who__role" style={{ display: "block" }}>
                    {item.signal_text}
                    {item.role_label
                      ? ` · ${t("applications.roleFor", { role: item.role_label })}`
                      : ""}
                  </span>
                </span>
              </div>
              <div className="who__chips">
                <Chip tone={item.direction === "INVITATION" ? "ai" : "neutral"}>
                  {item.direction === "INVITATION"
                    ? t("applications.invitation")
                    : t("applications.application")}
                </Chip>
                {statusChip(item)}
              </div>
              {item.message ? (
                <p style={{ color: "var(--t2)", fontSize: 12.5, lineHeight: 1.6, marginTop: 10 }}>
                  {item.message}
                </p>
              ) : null}
              {item.status === "PENDING" ? (
                <div className="pair" style={{ marginTop: 12 }}>
                  {box === "received" || item.direction === "INVITATION" ? (
                    <>
                      <Button
                        disabled={busyId === item.id}
                        onClick={() => act(item.id, "reject")}
                        size="small"
                        type="button"
                        variant="ghost"
                      >
                        {t("applications.reject")}
                      </Button>
                      <Button
                        disabled={busyId === item.id}
                        onClick={() => act(item.id, "accept")}
                        size="small"
                        type="button"
                      >
                        {t("applications.accept")}
                      </Button>
                    </>
                  ) : (
                    <Button
                      disabled={busyId === item.id}
                      onClick={() => act(item.id, "withdraw")}
                      size="small"
                      type="button"
                      variant="ghost"
                    >
                      {t("applications.withdraw")}
                    </Button>
                  )}
                </div>
              ) : null}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
