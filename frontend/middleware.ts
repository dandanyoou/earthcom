import createMiddleware from "next-intl/middleware";
import { type NextRequest, NextResponse } from "next/server";

import { locales } from "./i18n/config";
import { routing } from "./i18n/routing";

const handleI18nRouting = createMiddleware(routing);
const localeLikeSegment = /^[a-z]{2}$/i;

export default function middleware(request: NextRequest) {
  const firstSegment = request.nextUrl.pathname.split("/")[1];

  if (
    firstSegment &&
    localeLikeSegment.test(firstSegment) &&
    !locales.includes(firstSegment as (typeof locales)[number])
  ) {
    return NextResponse.next();
  }

  return handleI18nRouting(request);
}

export const config = {
  matcher: "/((?!api|trpc|_next|_vercel|.*\\..*).*)",
};
