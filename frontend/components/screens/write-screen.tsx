"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { Button, Card, Chip } from "@/components/ui";
import { api, formatKrw, type ParseData } from "@/lib/api";

import { LoadingBlock, ScreenHeader, Sheet, useRequireAuth } from "./shared";

type RoleForm = { label: string; headcount: number | null; form_position: number };
type Edits = {
  duration_weeks?: number | null;
  compensation_is_paid?: boolean;
  compensation_amount_krw?: number | null;
};

const ROLE_ICONS = [
  <svg key="c" viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="8.5" />
    <path d="m15.2 8.8-2 5.4-5.4 2 2-5.4z" />
  </svg>,
  <svg key="d" viewBox="0 0 24 24">
    <path d="m9 8-4 4 4 4" />
    <path d="m15 8 4 4-4 4" />
  </svg>,
  <svg key="a" viewBox="0 0 24 24">
    <path d="M15.5 4.5 19.5 8.5 9.5 18.5l-5 1.5 1.5-5z" />
    <path d="m13.5 6.5 4 4" />
  </svg>,
];

export function WriteScreen({ signalId }: { signalId?: string } = {}) {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const [text, setText] = useState("");
  const [roles, setRoles] = useState<RoleForm[]>([]);
  const [parse, setParse] = useState<ParseData | null>(null);
  const [edits, setEdits] = useState<Edits>({});
  const [licenseAck, setLicenseAck] = useState(false);
  const [highRiskAck, setHighRiskAck] = useState(false);
  const [editSheet, setEditSheet] = useState(false);
  const [roleSheet, setRoleSheet] = useState(false);
  const [roleName, setRoleName] = useState("");
  const [roleHeadcount, setRoleHeadcount] = useState<string>("1");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [degraded, setDegraded] = useState(false);
  const [crisis, setCrisis] = useState<string | null>(null);
  const [initializing, setInitializing] = useState(Boolean(signalId));
  const [initialError, setInitialError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!ready || !signalId) return;
    let active = true;
    api
      .signal(signalId)
      .then((signal) => {
        if (!active) return;
        if (signal.status !== "DRAFT" && signal.status !== "OPEN") {
          throw new Error(t("write.editLocked"));
        }
        setText(signal.raw_text);
        setRoles(
          signal.roles.map((role, index) => ({
            label: role.label,
            headcount: role.headcount,
            form_position: index,
          })),
        );
        setEdits({
          duration_weeks: signal.duration_weeks,
          compensation_is_paid: signal.compensation.is_paid,
          compensation_amount_krw: signal.compensation.amount_minor,
        });
        setInitialError(null);
      })
      .catch((err: Error) => {
        if (active) setInitialError(err.message);
      })
      .finally(() => {
        if (active) setInitializing(false);
      });
    return () => {
      active = false;
    };
  }, [ready, signalId, t]);

  // Debounced parse preview — "이렇게 이해했어요" updates as the user types.
  useEffect(() => {
    if (!ready) return;
    if (timer.current) clearTimeout(timer.current);
    if (text.trim().length < 4) {
      setParse(null);
      return;
    }
    timer.current = setTimeout(async () => {
      try {
        const envelope = await api.parse(text, roles);
        setDegraded(envelope.degraded);
        if (envelope.degrade_reason === "MODERATION") {
          setCrisis(envelope.data.crisis_notice ?? null);
          setParse(null);
        } else {
          setCrisis(null);
          setParse(envelope.data);
        }
      } catch {
        setParse(null);
      }
    }, 450);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [text, roles, ready]);

  if (!ready) return null;
  if (initializing || initialError) return <LoadingBlock error={initialError} />;

  const duration = parse
    ? edits.duration_weeks !== undefined
      ? { weeks: edits.duration_weeks, origin: "EXPLICIT" }
      : parse.duration
    : null;
  const compensation = parse
    ? {
        is_paid: edits.compensation_is_paid ?? parse.compensation.is_paid,
        amount_krw:
          edits.compensation_amount_krw !== undefined
            ? edits.compensation_amount_krw
            : parse.compensation.amount_krw,
        origin:
          edits.compensation_is_paid !== undefined || edits.compensation_amount_krw !== undefined
            ? "EXPLICIT"
            : parse.compensation.origin,
      }
    : null;
  const hasGuess =
    (duration?.origin === "INFERRED" && duration.weeks !== null) ||
    compensation?.origin === "INFERRED";
  const needsHighRisk = Boolean(
    parse &&
    parse.required_credentials.some((c) => c === "MEDICAL_LICENSE" || c === "LEGAL_LICENSE"),
  );

  function addRole() {
    const label = roleName.trim();
    if (!label || roles.length >= 8) return;
    setRoles([
      ...roles,
      {
        label,
        headcount: roleHeadcount === "" ? null : Math.max(1, Number(roleHeadcount)),
        form_position: roles.length,
      },
    ]);
    setRoleName("");
    setRoleHeadcount("1");
    setRoleSheet(false);
  }

  function removeRole(position: number) {
    setRoles(
      roles
        .filter((role) => role.form_position !== position)
        .map((role, index) => ({ ...role, form_position: index })),
    );
  }

  async function submit() {
    if (!text.trim()) {
      setError(t("write.needText"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      if (signalId) {
        const signal = await api.updateSignal(signalId, {
          raw_text: text,
          roles_form: roles,
          edits: edits as Record<string, unknown>,
          inferred_confirmed: true,
          license_acknowledged: licenseAck,
          high_risk_acknowledged: highRiskAck,
        });
        router.replace(`/signals/${signal.id}`);
        return;
      }
      const signal = await api.createSignal({
        raw_text: text,
        roles_form: roles,
        edits: edits as Record<string, unknown>,
      });
      await api.publishSignal(signal.id, {
        inferred_confirmed: true,
        license_acknowledged: licenseAck,
        high_risk_acknowledged: highRiskAck,
      });
      router.push(`/who/${signal.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const canSubmit =
    text.trim().length >= 4 &&
    !busy &&
    !crisis &&
    (!parse?.license_risk.flagged || licenseAck) &&
    (!needsHighRisk || highRiskAck);

  return (
    <div style={{ paddingBottom: 28 }}>
      <ScreenHeader
        onBack={() => router.push(signalId ? `/signals/${signalId}` : "/home")}
        subtitle={t(signalId ? "write.editSubtitle" : "write.subtitle")}
        title={t(signalId ? "write.editTitle" : "write.title")}
      />
      <div className="px" style={{ marginTop: 14 }}>
        <textarea
          className="ta"
          onChange={(event) => setText(event.target.value)}
          placeholder={t("write.placeholder")}
          value={text}
        />

        {crisis ? (
          <div className="warn-note" role="alert">
            <span>♥</span>
            <span>
              <b>{t("write.crisisTitle")}</b> — {crisis}
            </span>
          </div>
        ) : null}

        {parse ? (
          <Card style={{ marginTop: 12 }}>
            <div style={{ alignItems: "center", display: "flex", gap: 8, marginBottom: 12 }}>
              <b style={{ fontSize: 14, letterSpacing: "-0.02em" }}>{t("write.understood")}</b>
              <Chip tone="ai">{t("write.aiChip")}</Chip>
              {degraded ? <Chip tone="warning">{t("common.simpleMode")}</Chip> : null}
            </div>
            <div className="tags">
              {parse.skills.map((skill) => (
                <span key={skill.name} className="tag">
                  <small>{t("write.skillTag")}</small>
                  {skill.name}
                </span>
              ))}
              <span className="tag">
                <small>{t("write.wayTag")}</small>
                {parse.team_shape.cardinality === "1:1" ? t("write.oneOnOne") : t("write.together")}
              </span>
              {duration && duration.weeks !== null ? (
                duration.origin === "INFERRED" ? (
                  <button
                    className="tag tag--guess"
                    onClick={() => setEditSheet(true)}
                    type="button"
                  >
                    <small>
                      {t("write.durationTag")} · {t("write.estimated")}
                    </small>
                    {t("write.weeks", { weeks: duration.weeks })}
                  </button>
                ) : (
                  <span className="tag">
                    <small>{t("write.durationTag")}</small>
                    {t("write.weeks", { weeks: duration.weeks })}
                  </span>
                )
              ) : null}
              {compensation ? (
                compensation.origin === "INFERRED" ? (
                  <button
                    className="tag tag--guess"
                    onClick={() => setEditSheet(true)}
                    type="button"
                  >
                    <small>
                      {t("write.payTag")} · {t("write.estimated")}
                    </small>
                    {compensation.amount_krw
                      ? formatKrw(compensation.amount_krw)
                      : t("write.negotiable")}
                  </button>
                ) : (
                  <span className="tag">
                    <small>{t("write.payTag")}</small>
                    {!compensation.is_paid
                      ? t("write.unpaid")
                      : compensation.amount_krw
                        ? formatKrw(compensation.amount_krw)
                        : t("write.negotiable")}
                  </span>
                )
              ) : null}
            </div>
            {hasGuess ? <div className="tag-note">{t("write.guessNote")}</div> : null}
          </Card>
        ) : null}

        <Card style={{ marginTop: 12 }}>
          <div style={{ alignItems: "center", display: "flex", gap: 8, marginBottom: 12 }}>
            <b style={{ fontSize: 14, letterSpacing: "-0.02em" }}>{t("write.rolesTitle")}</b>
            <Chip tone="verified">{t("write.rolesChip")}</Chip>
          </div>
          {roles.map((role, index) => (
            <div key={role.form_position} className="rl">
              <span className="rl__icon">{ROLE_ICONS[index % ROLE_ICONS.length]}</span>
              <span className="rl__content">
                <span className="rl__title">{role.label}</span>
                <span className="rl__desc">
                  {role.headcount === null
                    ? t("write.headcountUndecided")
                    : `${role.headcount} · ${t("write.roleSearching")}`}
                </span>
              </span>
              <button
                aria-label={t("common.close")}
                className="rl__remove"
                onClick={() => removeRole(role.form_position)}
                type="button"
              >
                ✕
              </button>
            </div>
          ))}
          <button className="add-role" onClick={() => setRoleSheet(true)} type="button">
            {t("write.addRole")}
          </button>
        </Card>

        {parse?.license_risk.flagged ? (
          <div className="warn-note">
            <span>⚠</span>
            <label>
              <input
                checked={licenseAck}
                onChange={(event) => setLicenseAck(event.target.checked)}
                type="checkbox"
              />
              <span>
                <b>{t("write.licenseTitle")}</b> — {t("write.licenseBody")}{" "}
                <b>{t("write.acknowledge")}</b>
              </span>
            </label>
          </div>
        ) : null}
        {needsHighRisk && parse ? (
          <div className="warn-note">
            <span>⚠</span>
            <label>
              <input
                checked={highRiskAck}
                onChange={(event) => setHighRiskAck(event.target.checked)}
                type="checkbox"
              />
              <span>
                <b>{t("write.highRiskTitle")}</b> — {parse.disclaimers.join(" ")}{" "}
                <b>{t("write.acknowledge")}</b>
              </span>
            </label>
          </div>
        ) : null}

        {error ? <div className="form-error">{error}</div> : null}
        <div style={{ marginTop: 14 }}>
          <Button disabled={!canSubmit} onClick={submit} type="button">
            {busy
              ? t(signalId ? "write.saving" : "write.submitting")
              : t(signalId ? "write.save" : "write.submit")}
          </Button>
        </div>
      </div>

      <Sheet
        onClose={() => setEditSheet(false)}
        open={editSheet}
        subtitle={t("write.editSheetSubtitle")}
        title={t("write.editSheetTitle")}
      >
        <div className="field">
          <label htmlFor="edit-duration">{t("write.editDuration")}</label>
          <input
            id="edit-duration"
            min={1}
            max={104}
            onChange={(event) =>
              setEdits({
                ...edits,
                duration_weeks: event.target.value === "" ? null : Number(event.target.value),
              })
            }
            type="number"
            value={
              edits.duration_weeks !== undefined
                ? (edits.duration_weeks ?? "")
                : (parse?.duration.weeks ?? "")
            }
          />
        </div>
        <div className="field">
          <label>{t("write.editPaid")}</label>
          <div className="rating-row">
            <button
              data-active={(edits.compensation_is_paid ?? parse?.compensation.is_paid) === true}
              onClick={() => setEdits({ ...edits, compensation_is_paid: true })}
              type="button"
            >
              {t("write.paid")}
            </button>
            <button
              data-active={(edits.compensation_is_paid ?? parse?.compensation.is_paid) === false}
              onClick={() => setEdits({ ...edits, compensation_is_paid: false })}
              type="button"
            >
              {t("write.editUnpaid")}
            </button>
          </div>
        </div>
        <div className="field">
          <label htmlFor="edit-amount">{t("write.editAmount")}</label>
          <input
            id="edit-amount"
            min={0}
            onChange={(event) =>
              setEdits({
                ...edits,
                compensation_amount_krw:
                  event.target.value === "" ? null : Number(event.target.value),
              })
            }
            type="number"
            value={
              edits.compensation_amount_krw !== undefined
                ? (edits.compensation_amount_krw ?? "")
                : (parse?.compensation.amount_krw ?? "")
            }
          />
        </div>
        <div style={{ marginTop: 18 }}>
          <Button onClick={() => setEditSheet(false)} type="button">
            {t("write.confirmValues")}
          </Button>
        </div>
      </Sheet>

      <Sheet
        onClose={() => setRoleSheet(false)}
        open={roleSheet}
        subtitle={t("write.roleSheetSubtitle")}
        title={t("write.roleSheetTitle")}
      >
        <div className="field">
          <label htmlFor="role-name">{t("write.roleLabel")}</label>
          <input
            id="role-name"
            maxLength={40}
            onChange={(event) => setRoleName(event.target.value)}
            value={roleName}
          />
        </div>
        <div className="field">
          <label htmlFor="role-headcount">
            {t("write.roleHeadcount")} ({t("write.headcountUndecided")}: 0)
          </label>
          <input
            id="role-headcount"
            min={0}
            max={50}
            onChange={(event) =>
              setRoleHeadcount(event.target.value === "0" ? "" : event.target.value)
            }
            type="number"
            value={roleHeadcount}
          />
        </div>
        {roles.length >= 8 ? <div className="form-error">{t("write.roleLimit")}</div> : null}
        <div style={{ marginTop: 18 }}>
          <Button disabled={!roleName.trim() || roles.length >= 8} onClick={addRole} type="button">
            {t("write.roleAddAction")}
          </Button>
        </div>
      </Sheet>
    </div>
  );
}
