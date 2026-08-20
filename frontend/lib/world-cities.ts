// The five Earth(us) cities shown on the globe home, each with its own
// three-scene scroll-world. Copy is kept bilingual here (not in the next-intl
// catalog) because it is passed as config into the vanilla scroll engine, not
// rendered as JSX. Select by locale in the component.

export type CityKey = "seoul" | "berlin" | "tokyo" | "lisbon" | "newyork";
export type Locale = "ko" | "en";

export interface SceneCopy {
  eyebrow: string;
  title: string;
  body: string;
}
export interface City {
  key: CityKey;
  lat: number;
  lng: number;
  accent: string;
  name: Record<Locale, string>;
  role: Record<Locale, string>;
  scenes: Record<Locale, SceneCopy[]>; // exactly 3, in scroll order
}

export const CITIES: City[] = [
  {
    key: "seoul",
    lat: 37.5665,
    lng: 126.978,
    accent: "#FFC978",
    name: { ko: "서울", en: "Seoul" },
    role: { ko: "모임", en: "Circles" },
    scenes: {
      ko: [
        {
          eyebrow: "서울 · 모임",
          title: "세계가 이웃이 되는 곳",
          body: "한강이 흐르는 밤, 낯선 사람들이 같은 관심사로 모입니다.",
        },
        {
          eyebrow: "골목 · 포차",
          title: "밤거리에서 만나는 사람들",
          body: "네온 골목 포차에서 대화가 시작됩니다.",
        },
        {
          eyebrow: "남산 · 전망",
          title: "도시를 내려다보며",
          body: "남산타워 전망 광장, 오늘의 모임이 도시를 잇습니다.",
        },
      ],
      en: [
        {
          eyebrow: "Seoul · Circles",
          title: "Where the world becomes a neighbour",
          body: "By the Han River at night, strangers gather around a shared interest.",
        },
        {
          eyebrow: "Alleys · Street food",
          title: "People you meet after dark",
          body: "Conversations start at the neon-lit night market.",
        },
        {
          eyebrow: "Namsan · View",
          title: "Looking down over the city",
          body: "From the Namsan viewpoint, tonight's circle connects the city.",
        },
      ],
    },
  },
  {
    key: "berlin",
    lat: 52.52,
    lng: 13.405,
    accent: "#8FE0FF",
    name: { ko: "베를린", en: "Berlin" },
    role: { ko: "구인·구직", en: "Work" },
    scenes: {
      ko: [
        {
          eyebrow: "베를린 · 구인·구직",
          title: "베를린에서 팀을 만든다",
          body: "벽돌 창고 코워킹 마당에서 필요한 사람을 찾습니다.",
        },
        {
          eyebrow: "메이커 · 스튜디오",
          title: "손으로 만드는 사람들",
          body: "작업대 위에서 아이디어가 물성이 됩니다.",
        },
        {
          eyebrow: "강변 · 캠퍼스",
          title: "국경 너머의 동료",
          body: "강변 스타트업 캠퍼스에서 협업이 이어집니다.",
        },
      ],
      en: [
        {
          eyebrow: "Berlin · Work",
          title: "Build your team in Berlin",
          body: "Find the person you need in a brick-warehouse co-working yard.",
        },
        {
          eyebrow: "Maker · Studio",
          title: "People who build with their hands",
          body: "On the workbench, an idea becomes something physical.",
        },
        {
          eyebrow: "Riverside · Campus",
          title: "Colleagues across borders",
          body: "Collaboration flows through the riverside startup campus.",
        },
      ],
    },
  },
  {
    key: "tokyo",
    lat: 35.6762,
    lng: 139.6503,
    accent: "#FF9EC4",
    name: { ko: "도쿄", en: "Tokyo" },
    role: { ko: "섭외", en: "Casting" },
    scenes: {
      ko: [
        {
          eyebrow: "도쿄 · 섭외",
          title: "도쿄에서 크리에이터를 섭외한다",
          body: "프로젝트에 딱 맞는 창작자를 바로 연결합니다.",
        },
        {
          eyebrow: "크리에이터 · 스튜디오",
          title: "카메라가 도는 곳",
          body: "소프트박스 아래에서 오늘의 촬영이 시작됩니다.",
        },
        {
          eyebrow: "이자카야 · 골목",
          title: "밤이 깊어질수록",
          body: "등불 골목에서 다음 작업 이야기가 오갑니다.",
        },
      ],
      en: [
        {
          eyebrow: "Tokyo · Casting",
          title: "Cast a creator in Tokyo",
          body: "Connect instantly with the maker who fits your project.",
        },
        {
          eyebrow: "Creator · Studio",
          title: "Where the camera rolls",
          body: "Under the softboxes, today's shoot begins.",
        },
        {
          eyebrow: "Izakaya · Alley",
          title: "As the night deepens",
          body: "In the lantern-lit lane, the next project takes shape.",
        },
      ],
    },
  },
  {
    key: "lisbon",
    lat: 38.7223,
    lng: -9.1393,
    accent: "#F2B366",
    name: { ko: "리스본", en: "Lisbon" },
    role: { ko: "교육·교류", en: "Learning" },
    scenes: {
      ko: [
        {
          eyebrow: "리스본 · 교육·교류",
          title: "리스본에서 배우고 가르친다",
          body: "언덕 위 노란 트램 곁, 배움의 광장이 열립니다.",
        },
        {
          eyebrow: "아줄레주 · 교실",
          title: "타일 골목의 작은 교실",
          body: "언어와 지식을 국경 없이 주고받습니다.",
        },
        {
          eyebrow: "전망 · 카페",
          title: "도시를 마주한 자리에서",
          body: "언덕 카페 테라스에서 오늘의 수업이 이어집니다.",
        },
      ],
      en: [
        {
          eyebrow: "Lisbon · Learning",
          title: "Learn and teach in Lisbon",
          body: "Beside the yellow tram on the hill, a plaza of learning opens.",
        },
        {
          eyebrow: "Azulejo · Classroom",
          title: "A small class in the tiled lane",
          body: "Language and knowledge, exchanged without borders.",
        },
        {
          eyebrow: "Viewpoint · Café",
          title: "Facing the city",
          body: "On the hilltop terrace, today's lesson continues.",
        },
      ],
    },
  },
  {
    key: "newyork",
    lat: 40.7128,
    lng: -74.006,
    accent: "#A0E8FF",
    name: { ko: "뉴욕", en: "New York" },
    role: { ko: "연결", en: "Connection" },
    scenes: {
      ko: [
        {
          eyebrow: "뉴욕 · 연결",
          title: "그리고, 세계가 연결된다",
          body: "모든 길이 하나의 허브 광장으로 모입니다.",
        },
        {
          eyebrow: "브루클린 · 다리",
          title: "강을 건너 이어지는 사람들",
          body: "다리 너머에서 새로운 만남이 시작됩니다.",
        },
        {
          eyebrow: "타임스퀘어 · 교차로",
          title: "세계가 만나는 한복판",
          body: "네온 교차로에서 다섯 도시가 하나의 판게아로 이어집니다.",
        },
      ],
      en: [
        {
          eyebrow: "New York · Connection",
          title: "And the world connects",
          body: "Every road converges on one hub plaza.",
        },
        {
          eyebrow: "Brooklyn · Bridge",
          title: "People joined across the river",
          body: "Beyond the bridge, a new encounter begins.",
        },
        {
          eyebrow: "Times Square · Crossroads",
          title: "The center where the world meets",
          body: "At the neon crossroads, five cities meet in Earth(us).",
        },
      ],
    },
  },
];

export function findCity(key: string): City | undefined {
  return CITIES.find((c) => c.key === key);
}
