// Demo posts for each city. Every country supports the same five PANGAEA
// categories, and each holds the posts its users created. Rendered with the
// same .post / .chip design as /ko/home. Deterministic (no randomness) so SSR
// and client hydrate identically. Swap for the real API later.

import type { CityKey, Locale } from "./world-cities";
import type { ChipTone } from "@/components/ui/chip";

export type CategoryKey = "meet" | "work" | "cast" | "learn" | "connect";

export interface Category {
  key: CategoryKey;
  label: Record<Locale, string>;
  tone: ChipTone;
}

export const CATEGORIES: Category[] = [
  { key: "meet", label: { ko: "모임", en: "Circles" }, tone: "ai" },
  { key: "work", label: { ko: "구인구직", en: "Work" }, tone: "outline" },
  { key: "cast", label: { ko: "섭외", en: "Casting" }, tone: "warning" },
  { key: "learn", label: { ko: "교육·교류", en: "Learning" }, tone: "verified" },
  { key: "connect", label: { ko: "연결", en: "Connect" }, tone: "neutral" },
];

export const FILTER: Array<CategoryKey | "ALL"> = [
  "ALL",
  "meet",
  "work",
  "cast",
  "learn",
  "connect",
];

// Each category maps to a real neighbourhood per city (the village themes).
export const NEIGHBORHOODS: Record<CityKey, Record<CategoryKey, Record<Locale, string>>> = {
  seoul: {
    meet: { ko: "홍대", en: "Hongdae" },
    work: { ko: "강남", en: "Gangnam" },
    cast: { ko: "을지로", en: "Euljiro" },
    learn: { ko: "잠실", en: "Jamsil" },
    connect: { ko: "광화문", en: "Gwanghwamun" },
  },
  berlin: {
    meet: { ko: "크로이츠베르크", en: "Kreuzberg" },
    work: { ko: "미테", en: "Mitte" },
    cast: { ko: "프리드리히스하인", en: "Friedrichshain" },
    learn: { ko: "프렌츠라우어베르크", en: "Prenzlauer Berg" },
    connect: { ko: "브란덴부르크", en: "Brandenburg" },
  },
  tokyo: {
    meet: { ko: "시부야", en: "Shibuya" },
    work: { ko: "신주쿠", en: "Shinjuku" },
    cast: { ko: "아키하바라", en: "Akihabara" },
    learn: { ko: "진보초", en: "Jimbocho" },
    connect: { ko: "도쿄역", en: "Tokyo Station" },
  },
  lisbon: {
    meet: { ko: "바이루알투", en: "Bairro Alto" },
    work: { ko: "파르크", en: "Parque" },
    cast: { ko: "알파마", en: "Alfama" },
    learn: { ko: "벨렝", en: "Belém" },
    connect: { ko: "코메르시우", en: "Comércio" },
  },
  newyork: {
    meet: { ko: "윌리엄스버그", en: "Williamsburg" },
    work: { ko: "미드타운", en: "Midtown" },
    cast: { ko: "소호", en: "SoHo" },
    learn: { ko: "모닝사이드", en: "Morningside" },
    connect: { ko: "타임스스퀘어", en: "Times Square" },
  },
};

export interface Face {
  initials: string;
  palette: number;
}
export interface Post {
  id: string;
  cat: CategoryKey;
  online: boolean;
  when: Record<Locale, string>;
  title: Record<Locale, string>;
  meta: Record<Locale, string>;
  faces: Face[];
}

type Topic = { ko: string; en: string };

const TOPICS: Record<CityKey, Topic[]> = {
  seoul: [
    { ko: "케이팝 댄스", en: "K-pop dance" },
    { ko: "코딩", en: "Coding" },
    { ko: "인디 게임", en: "Indie games" },
    { ko: "한식 쿠킹", en: "Korean cooking" },
    { ko: "한국어 교환", en: "Korean exchange" },
  ],
  berlin: [
    { ko: "테크노 뮤직", en: "Techno music" },
    { ko: "디자인 시스템", en: "Design systems" },
    { ko: "스타트업", en: "Startups" },
    { ko: "사진", en: "Photography" },
    { ko: "독일어 교환", en: "German exchange" },
  ],
  tokyo: [
    { ko: "애니 작화", en: "Anime art" },
    { ko: "게임 개발", en: "Game dev" },
    { ko: "스트리트 사진", en: "Street photo" },
    { ko: "라멘 투어", en: "Ramen tour" },
    { ko: "일본어 교환", en: "Japanese exchange" },
  ],
  lisbon: [
    { ko: "서핑", en: "Surfing" },
    { ko: "타일아트", en: "Tile art" },
    { ko: "리모트워크", en: "Remote work" },
    { ko: "와인 테이스팅", en: "Wine tasting" },
    { ko: "포르투갈어 교환", en: "Portuguese exchange" },
  ],
  newyork: [
    { ko: "브랜딩", en: "Branding" },
    { ko: "인디 필름", en: "Indie film" },
    { ko: "재즈 세션", en: "Jazz session" },
    { ko: "스타트업", en: "Startups" },
    { ko: "영어 회화", en: "English convo" },
  ],
};

const INITIALS: Record<CityKey, string[]> = {
  seoul: ["JM", "HN", "SY", "DY", "MR"],
  berlin: ["LE", "MX", "JO", "MI", "TL"],
  tokyo: ["YK", "HR", "AO", "RN", "SO"],
  lisbon: ["JO", "MA", "TG", "AN", "RU"],
  newyork: ["MA", "ET", "NO", "LE", "IV"],
};

const WHEN: Array<Record<Locale, string>> = [
  { ko: "방금 전", en: "just now" },
  { ko: "2시간 전", en: "2h ago" },
  { ko: "어제", en: "yesterday" },
  { ko: "2일 전", en: "2d ago" },
];

// 2 posts per category → 10 posts per city.
const PLAN: CategoryKey[] = [
  "meet",
  "meet",
  "work",
  "work",
  "cast",
  "cast",
  "learn",
  "learn",
  "connect",
  "connect",
];

function faces(city: CityKey, seed: number, count: number): Face[] {
  const pool = INITIALS[city];
  return Array.from({ length: count }, (_, k) => ({
    initials: pool[(seed + k) % pool.length],
    palette: ((seed + k) % 6) + 1,
  }));
}

export function postsFor(city: CityKey): Post[] {
  const topics = TOPICS[city];
  return PLAN.map((cat, i) => {
    const t = topics[i % topics.length];
    const n = 5 + ((t.ko.length + i * 3) % 14);
    const budget = 40 + ((i + t.en.length) % 8) * 10;
    const online = cat === "cast" ? false : i % 3 !== 0;
    const title: Record<CategoryKey, Record<Locale, string>> = {
      meet: { ko: `${t.ko} 같이 즐길 사람 모여요`, en: `${t.en} circle — join us` },
      work: { ko: `${t.ko} 함께할 팀원 구해요`, en: `Looking for a ${t.en} teammate` },
      cast: { ko: `${t.ko} 크리에이터 섭외합니다`, en: `Casting a ${t.en} creator` },
      learn: { ko: `${t.ko} 스터디·클래스 열어요`, en: `${t.en} class / study group` },
      connect: { ko: `${t.ko} 관심사로 새 인연 찾아요`, en: `Connect over ${t.en}` },
    };
    const meta: Record<CategoryKey, Record<Locale, string>> = {
      meet: { ko: `2~4인 · 매주`, en: `2–4 people · weekly` },
      work: { ko: `보수 협의 · 파트타임`, en: `Pay negotiable · part-time` },
      cast: {
        ko: `예산 ${budget}만원 · ${2 + (i % 4)}주`,
        en: `Budget $${budget * 8} · ${2 + (i % 4)}wks`,
      },
      learn: { ko: `입문·중급 · 주 ${1 + (i % 2)}회`, en: `Beginner–Inter · ${1 + (i % 2)}×/wk` },
      connect: { ko: `국경 없이 · 온·오프 모두`, en: `Across borders · on/offline` },
    };
    return {
      id: `${city}-${i}`,
      cat,
      online,
      when: WHEN[i % WHEN.length],
      title: title[cat],
      meta: meta[cat],
      faces: cat === "meet" || cat === "connect" ? faces(city, i, 2 + (n % 3)) : [],
    };
  });
}
