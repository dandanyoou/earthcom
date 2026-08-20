import { setRequestLocale } from "next-intl/server";

import { LoginScreen } from "@/components/screens/auth-screens";

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return <LoginScreen />;
}
