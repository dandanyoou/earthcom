"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { Button, Chip } from "@/components/ui";
import { api, type ProfileDetail } from "@/lib/api";

import { LoadingBlock, ScreenHeader, useApiData, useRequireAuth } from "./shared";

type SkillRow = { name: string; years: string };
type LanguageRow = { code: string; proficiency: string };
type AvailabilityRow = { weekday: number; start: string; end: string };

export function MeScreen() {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const { data, error, loading, reload } = useApiData<ProfileDetail>(() => api.myProfile(), ready);
  const [name, setName] = useState("");
  const [bio, setBio] = useState("");
  const [city, setCity] = useState("");
  const [skills, setSkills] = useState<SkillRow[]>([]);
  const [languages, setLanguages] = useState<LanguageRow[]>([]);
  const [availability, setAvailability] = useState<AvailabilityRow[]>([]);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!data) return;
    setName(data.display_name);
    setBio(data.bio);
    setCity(data.city_code ?? "");
    setSkills(data.skills.map((skill) => ({ name: skill.name, years: String(skill.years ?? "") })));
    setLanguages(data.languages.map((l) => ({ code: l.code, proficiency: l.proficiency })));
    setAvailability(
      data.availability.map((rule) => ({
        weekday: rule.weekday,
        start: rule.start,
        end: rule.end,
      })),
    );
  }, [data]);

  if (!ready || loading || !data) return <LoadingBlock error={error} reload={reload} />;

  async function save() {
    setBusy(true);
    setSaved(false);
    try {
      await api.patchProfile({
        display_name: name,
        bio,
        ...(city ? { city_code: city } : {}),
      });
      await api.putSkills(
        skills
          .filter((skill) => skill.name.trim())
          .map((skill) => ({
            name: skill.name.trim(),
            years: skill.years === "" ? null : Number(skill.years),
          })),
      );
      await api.putLanguages(
        languages
          .filter((l) => /^[a-z]{2}$/.test(l.code.trim().toLowerCase()))
          .map((l) => ({
            code: l.code.trim().toLowerCase(),
            proficiency: l.proficiency,
          })),
      );
      await api.putAvailability(availability.filter((rule) => rule.start < rule.end));
      setSaved(true);
      reload();
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    await api.logout();
    router.replace("/login");
  }

  return (
    <div style={{ paddingBottom: 28 }}>
      <ScreenHeader
        title={t("meScreen.title")}
        trailing={
          <button
            className="button button--ghost button--small"
            onClick={logout}
            style={{ width: "auto" }}
            type="button"
          >
            {t("common.logout")}
          </button>
        }
      />
      <div className="px">
        <div className="field">
          <label htmlFor="me-name">{t("meScreen.name")}</label>
          <input id="me-name" onChange={(e) => setName(e.target.value)} value={name} />
        </div>
        <div className="field">
          <label htmlFor="me-bio">{t("meScreen.bio")}</label>
          <textarea id="me-bio" onChange={(e) => setBio(e.target.value)} rows={2} value={bio} />
        </div>
        <div className="field">
          <label htmlFor="me-city">{t("meScreen.city")}</label>
          <select id="me-city" onChange={(e) => setCity(e.target.value)} value={city}>
            <option value="">—</option>
            {["SEOUL", "BERLIN", "TOKYO", "LISBON", "NEW_YORK", "KABUL", "HANOI"].map((code) => (
              <option key={code} value={code}>
                {t(`cities.${code}`)}
              </option>
            ))}
          </select>
        </div>

        <div className="section-heading">{t("meScreen.skillsTitle")}</div>
        {skills.map((skill, index) => (
          <div key={index} className="pair" style={{ marginBottom: 8 }}>
            <input
              aria-label={t("meScreen.skillName")}
              className="field-input"
              onChange={(e) =>
                setSkills(
                  skills.map((row, i) => (i === index ? { ...row, name: e.target.value } : row)),
                )
              }
              placeholder={t("meScreen.skillName")}
              style={{
                border: "1px solid var(--line2)",
                borderRadius: 10,
                padding: "11px 13px",
              }}
              value={skill.name}
            />
            <input
              aria-label={t("meScreen.skillYears")}
              min={0}
              onChange={(e) =>
                setSkills(
                  skills.map((row, i) => (i === index ? { ...row, years: e.target.value } : row)),
                )
              }
              placeholder={t("meScreen.skillYears")}
              style={{
                border: "1px solid var(--line2)",
                borderRadius: 10,
                maxWidth: 110,
                padding: "11px 13px",
              }}
              type="number"
              value={skill.years}
            />
            <button
              aria-label={t("common.close")}
              className="rl__remove"
              onClick={() => setSkills(skills.filter((_, i) => i !== index))}
              style={{ flex: "0 0 auto" }}
              type="button"
            >
              ✕
            </button>
          </div>
        ))}
        <button
          className="add-role"
          onClick={() => setSkills([...skills, { name: "", years: "" }])}
          type="button"
        >
          {t("meScreen.addSkill")}
        </button>

        <div className="section-heading">{t("meScreen.languagesTitle")}</div>
        {languages.map((language, index) => (
          <div key={index} className="pair" style={{ marginBottom: 8 }}>
            <input
              aria-label={t("meScreen.languageCode")}
              maxLength={2}
              onChange={(e) =>
                setLanguages(
                  languages.map((row, i) => (i === index ? { ...row, code: e.target.value } : row)),
                )
              }
              placeholder={t("meScreen.languageCode")}
              style={{
                border: "1px solid var(--line2)",
                borderRadius: 10,
                maxWidth: 120,
                padding: "11px 13px",
              }}
              value={language.code}
            />
            <select
              aria-label={t("profile.languages")}
              onChange={(e) =>
                setLanguages(
                  languages.map((row, i) =>
                    i === index ? { ...row, proficiency: e.target.value } : row,
                  ),
                )
              }
              style={{
                border: "1px solid var(--line2)",
                borderRadius: 10,
                padding: "11px 13px",
              }}
              value={language.proficiency}
            >
              {(["BASIC", "CONVERSATIONAL", "PROFESSIONAL", "NATIVE"] as const).map((level) => (
                <option key={level} value={level}>
                  {t(`profile.proficiency.${level}`)}
                </option>
              ))}
            </select>
            <button
              aria-label={t("common.close")}
              className="rl__remove"
              onClick={() => setLanguages(languages.filter((_, i) => i !== index))}
              style={{ flex: "0 0 auto" }}
              type="button"
            >
              ✕
            </button>
          </div>
        ))}
        <button
          className="add-role"
          onClick={() => setLanguages([...languages, { code: "", proficiency: "CONVERSATIONAL" }])}
          type="button"
        >
          {t("meScreen.addLanguage")}
        </button>

        <div className="section-heading">{t("meScreen.availabilityTitle")}</div>
        {availability.map((rule, index) => (
          <div key={index} className="pair" style={{ marginBottom: 8 }}>
            <select
              aria-label={t("meScreen.weekday")}
              onChange={(e) =>
                setAvailability(
                  availability.map((row, i) =>
                    i === index ? { ...row, weekday: Number(e.target.value) } : row,
                  ),
                )
              }
              style={{
                border: "1px solid var(--line2)",
                borderRadius: 10,
                padding: "11px 13px",
              }}
              value={rule.weekday}
            >
              {[0, 1, 2, 3, 4, 5, 6].map((day) => (
                <option key={day} value={day}>
                  {t(`profile.weekdays.${day}`)}
                </option>
              ))}
            </select>
            <input
              aria-label={t("meScreen.start")}
              onChange={(e) =>
                setAvailability(
                  availability.map((row, i) =>
                    i === index ? { ...row, start: e.target.value } : row,
                  ),
                )
              }
              style={{
                border: "1px solid var(--line2)",
                borderRadius: 10,
                padding: "11px 13px",
              }}
              type="time"
              value={rule.start}
            />
            <input
              aria-label={t("meScreen.end")}
              onChange={(e) =>
                setAvailability(
                  availability.map((row, i) =>
                    i === index ? { ...row, end: e.target.value } : row,
                  ),
                )
              }
              style={{
                border: "1px solid var(--line2)",
                borderRadius: 10,
                padding: "11px 13px",
              }}
              type="time"
              value={rule.end}
            />
            <button
              aria-label={t("common.close")}
              className="rl__remove"
              onClick={() => setAvailability(availability.filter((_, i) => i !== index))}
              style={{ flex: "0 0 auto" }}
              type="button"
            >
              ✕
            </button>
          </div>
        ))}
        <button
          className="add-role"
          onClick={() =>
            setAvailability([...availability, { weekday: 0, start: "20:00", end: "23:00" }])
          }
          type="button"
        >
          {t("meScreen.addAvailability")}
        </button>

        {saved ? (
          <div className="inline-chips">
            <Chip tone="verified">{t("meScreen.saved")}</Chip>
          </div>
        ) : null}
        <div style={{ marginTop: 16 }}>
          <Button disabled={busy} onClick={save} type="button">
            {t("meScreen.save")}
          </Button>
        </div>
      </div>
    </div>
  );
}
