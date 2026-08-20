import { getTranslations, setRequestLocale } from "next-intl/server";

import {
  Avatar,
  Button,
  Card,
  Chip,
  Fold,
  Note,
  Row,
  SectionGap,
  SectionHeading,
} from "@/components/ui";

export default async function ComponentsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("components");

  return (
    <main className="component-catalog" data-testid="component-catalog">
      <h1>{t("title")}</h1>

      <section data-testid="component-buttons">
        <SectionHeading>{t("buttons")}</SectionHeading>
        <div className="component-catalog__pair" data-testid="component-button-pair">
          <Button>{t("primary")}</Button>
          <Button variant="ghost">{t("ghost")}</Button>
        </div>
      </section>

      <section data-testid="component-chips">
        <SectionHeading>{t("chips")}</SectionHeading>
        <div className="component-catalog__chips">
          <Chip tone="verified">{t("verified")}</Chip>
          <Chip tone="ai">{t("ai")}</Chip>
          <Chip tone="warning">{t("warning")}</Chip>
          <Chip tone="danger">{t("check")}</Chip>
          <Chip tone="neutral">{t("neutral")}</Chip>
          <Chip tone="outline">{t("inferred")}</Chip>
        </div>
      </section>

      <SectionGap />

      <section data-testid="component-rows">
        <SectionHeading count={t("rowCount")}>{t("rows")}</SectionHeading>
        <Card>
          <Row>
            <Avatar palette={1}>{t("avatarInitials")}</Avatar>
            <span className="component-catalog__row-copy">
              <strong>{t("rowTitle")}</strong>
              <span>{t("rowDescription")}</span>
            </span>
          </Row>
          <div className="component-catalog__avatars">
            <Avatar palette={1}>{t("avatar1")}</Avatar>
            <Avatar palette={2}>{t("avatar2")}</Avatar>
            <Avatar palette={3}>{t("avatar3")}</Avatar>
            <Avatar palette={4}>{t("avatar4")}</Avatar>
            <Avatar palette={5}>{t("avatar5")}</Avatar>
            <Avatar palette={6}>{t("avatar6")}</Avatar>
          </div>
        </Card>
      </section>

      <section data-testid="component-fold">
        <SectionHeading>{t("foldHeading")}</SectionHeading>
        <Fold summary={t("fold")}>{t("foldBody")}</Fold>
      </section>

      <section data-testid="component-note">
        <SectionHeading>{t("noteHeading")}</SectionHeading>
        <Note title={t("noteTitle")}>{t("noteBody")}</Note>
      </section>
    </main>
  );
}
