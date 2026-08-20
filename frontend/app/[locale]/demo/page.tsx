import { DemoSurface } from "@/components/demo/demo-surface";
import { setRequestLocale } from "next-intl/server";

export default async function DemoPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return <DemoSurface />;
}
