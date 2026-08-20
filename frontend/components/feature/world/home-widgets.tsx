"use client";

// Floating widgets over the globe home: the visitor's trust temperature (if
// signed in) and a one-line "who do you need?" composer that opens the AI
// write flow. Kept glassy/dark so it sits naturally on the globe.

import { useEffect, useState } from "react";
import { useRouter } from "@/i18n/navigation";

import { api, getToken } from "@/lib/api";
import { trustFillPercent, trustText } from "@/components/screens/shared";
import styles from "./home-widgets.module.css";

export function HomeWidgets({ locale }: { locale: "ko" | "en" }) {
  const router = useRouter();
  const [trust, setTrust] = useState<{ value: number | null; status: string } | null>(null);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    if (!getToken()) return;
    setAuthed(true);
    api
      .home()
      .then((d) => setTrust(d.profile?.trust ?? null))
      .catch(() => {});
  }, []);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    router.push("/write");
  };

  return (
    <div className={styles.widgets}>
      {authed && trust?.status === "AVAILABLE" ? (
        <button className={styles.trust} type="button" onClick={() => router.push("/done")}>
          <span className={styles.trustVal}>{trustText(trust.value)}</span>
          <span className={styles.trustMeta}>
            <span className={styles.trustLabel}>
              {locale === "ko" ? "내 신뢰 온도" : "My trust"}
            </span>
            <span className={styles.trustBar}>
              <span style={{ width: `${trustFillPercent(trust.value)}%` }} />
            </span>
          </span>
        </button>
      ) : (
        <button className={styles.login} type="button" onClick={() => router.push("/login")}>
          {locale === "ko" ? "로그인하고 신뢰 온도 보기 →" : "Log in to see your trust →"}
        </button>
      )}

      <form className={styles.ask} onSubmit={submit}>
        <input
          className={styles.askInput}
          placeholder={
            locale === "ko" ? "무슨 일에 어떤 사람이 필요한가요?" : "Who do you need, and for what?"
          }
          aria-label={locale === "ko" ? "글 작성" : "Write a post"}
        />
        <button
          className={styles.askBtn}
          type="submit"
          aria-label={locale === "ko" ? "작성" : "Write"}
        >
          →
        </button>
      </form>
    </div>
  );
}
