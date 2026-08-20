"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { api, type NotificationItem } from "@/lib/api";

import { LoadingBlock, ScreenHeader, useApiData, useRequireAuth, useTimeAgo } from "./shared";

export function NotificationsScreen() {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const timeAgo = useTimeAgo();
  const { data, error, loading, reload } = useApiData(() => api.notifications(), ready);

  if (!ready || loading || !data) return <LoadingBlock error={error} reload={reload} />;

  function titleOf(item: NotificationItem): string {
    const values = {
      from: item.payload.from ?? "",
      title: item.payload.title ?? "",
    };
    try {
      return t(`notifications.${item.kind}` as never, values as never);
    } catch {
      return item.kind;
    }
  }

  async function open(item: NotificationItem) {
    if (!item.read) {
      await api.readNotification(item.id).catch(() => null);
      reload();
    }
    if (item.resource_type === "collaboration") router.push("/done");
    else if (item.resource_type === "application") router.push("/applications");
  }

  return (
    <div style={{ paddingBottom: 28 }}>
      <ScreenHeader onBack={() => router.push("/home")} title={t("notifications.title")} />
      <div className="px">
        {data.length === 0 ? (
          <div className="list-empty">{t("notifications.empty")}</div>
        ) : (
          data.map((item) => (
            <button
              key={item.id}
              className="notif"
              data-read={item.read}
              onClick={() => open(item)}
              type="button"
            >
              <span className="notif__dot" />
              <span>
                <span className="notif__title" style={{ display: "block" }}>
                  {titleOf(item)}
                </span>
                <span className="notif__meta">{timeAgo(item.created_at)}</span>
              </span>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
