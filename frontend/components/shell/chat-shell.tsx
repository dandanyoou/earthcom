import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import styles from "./shell.module.css";

export function ChatShell({
  assistant,
  list,
  messages,
}: {
  assistant: ReactNode;
  list: ReactNode;
  messages: ReactNode;
}) {
  const t = useTranslations("chat");

  return (
    <div className={styles.chatShell} data-testid="chat-shell">
      <section className={styles.chatList} data-testid="chat-list">
        {list}
      </section>
      <section className={styles.chatMessages} data-testid="chat-messages">
        {messages}
      </section>
      <aside className={styles.chatGuard} data-testid="chat-guard">
        <strong>{t("guardTitle")}</strong>
        <span>{t("guardBody")}</span>
      </aside>
      <form className={styles.chatComposer} data-testid="chat-composer">
        <label>
          <span className={styles.srOnly}>{t("composerLabel")}</span>
          <input placeholder={t("composerPlaceholder")} type="text" />
        </label>
        <button type="button">{t("send")}</button>
      </form>
      <aside className={styles.chatAssistant} data-testid="chat-assistant">
        {assistant}
      </aside>
    </div>
  );
}
