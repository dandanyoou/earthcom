"use client";

import { useState, type FormEvent } from "react";
import { useLocale, useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/navigation";

import { Button } from "@/components/ui";
import { api } from "@/lib/api";

function AuthCard({ mode }: { mode: "login" | "signup" }) {
  const t = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") await api.login(email, password);
      else await api.register(email, password, locale);
      router.push("/world");
    } catch {
      setError(mode === "login" ? t("loginFailed") : t("signupFailed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-brand">
          PANGAEA<span>.</span>
        </div>
        <p className="auth-tagline">{t("tagline")}</p>
        <div className="field">
          <label htmlFor="auth-email">{t("email")}</label>
          <input
            id="auth-email"
            autoComplete="email"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
        </div>
        <div className="field">
          <label htmlFor="auth-password">{t("password")}</label>
          <input
            id="auth-password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            minLength={8}
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
        </div>
        {error ? <div className="form-error">{error}</div> : null}
        <div style={{ marginTop: 18 }}>
          <Button disabled={busy} type="submit">
            {mode === "login" ? t("login") : t("signup")}
          </Button>
        </div>
        <p className="auth-alt">
          {mode === "login" ? (
            <>
              {t("noAccount")} <Link href="/signup">{t("signup")}</Link>
            </>
          ) : (
            <>
              {t("haveAccount")} <Link href="/login">{t("login")}</Link>
            </>
          )}
        </p>
        {mode === "login" ? (
          <div className="demo-hint">
            {t("demoHint")}
            <br />
            <code>minseok@pangaea.dev / pangaea-demo1!</code>
          </div>
        ) : null}
      </form>
    </div>
  );
}

export function LoginScreen() {
  return <AuthCard mode="login" />;
}

export function SignupScreen() {
  return <AuthCard mode="signup" />;
}
