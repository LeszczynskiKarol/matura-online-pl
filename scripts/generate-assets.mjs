// Generuje brand-assety w public/ bez wymagania zewnętrznego zdjęcia.
// Wszystko renderowane z inline SVG → sharp. Uruchom raz na nową domenę:
//
//   node scripts/generate-assets.mjs
//
// Wymaga: sharp (już w deps przez Astro).
//
// Outputy:
//   public/favicon.svg              vector logo (musi istnieć PRZED skryptem)
//   public/favicon-32.png           32×32  PNG fallback dla starszych przeglądarek
//   public/apple-touch-icon.png    180×180 PNG (iOS home screen)
//   public/og-image.jpg           1200×630 progresywny JPEG (Facebook/Twitter/Slack preview)
//
// Konfiguracja per-projekt — dostosuj BRAND_* na początku. Tło/akcent najlepiej spójne
// z `siteConfig` i `design.md`. Tekst headline'u krótki — 1-2 linie max.
//
// Re-uruchom kiedykolwiek zmienisz branding (kolor accent, nazwa).

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import sharp from "sharp";

// ───────────────────────────────────────────────────────────────────────
// EDYTUJ per-projekt:

const BRAND = {
  // Główny kolor + ciemniejszy (gradient na og-image). Najlepiej kolor accent
  // z `src/styles/global.css` (np. #2563eb → #1d4ed8 dla niebieskiego).
  accent: "#2563eb",
  accentDark: "#1d4ed8",
  accentDeep: "#1e3a8a",     // najciemniejszy dla tła og-image (top-left)
  textOnDark: "#ffffff",
  textOnDarkMuted: "#bfdbfe", // jasny accent na ciemnym tle

  // Nazwa wyświetlana w og-image. Tu domyślnie z `src/config/site.ts`,
  // możesz wpisać hardcode jak nie chcesz importować TS:
  siteName: "site.example",
  shortName: "site",          // 1-2 litery do badge'a (np. "m" dla maturalnie)

  // Główny headline + sub na og-image. 1-2 linie. Krótko.
  ogHeadline: "Twoja firma. Twoja oferta.",
  ogSubline: "Jednolinijkowy USP — co dostaje klient",
  ogChips: ["oferta", "realizacje", "kontakt"], // 2-4 chips w stopce

  // Tagline pod nazwą w og-image (uppercase). Najlepiej z briefu.
  tagline: "TAGLINE DOMENY",
};

// ───────────────────────────────────────────────────────────────────────

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PUBLIC = resolve(ROOT, "public");

let faviconSvg;
try {
  faviconSvg = readFileSync(resolve(PUBLIC, "favicon.svg"));
} catch (e) {
  console.error("✗ Brakuje public/favicon.svg — najpierw stwórz vector logo (template w generatorze).");
  process.exit(1);
}

// ── apple-touch-icon.png 180×180 ────────────────────────────────────────
await sharp(faviconSvg, { density: 720 })
  .resize(180, 180)
  .png({ compressionLevel: 9 })
  .toFile(resolve(PUBLIC, "apple-touch-icon.png"));
console.log("✓ public/apple-touch-icon.png");

// ── favicon-32.png ──────────────────────────────────────────────────────
await sharp(faviconSvg, { density: 720 })
  .resize(32, 32)
  .png({ compressionLevel: 9 })
  .toFile(resolve(PUBLIC, "favicon-32.png"));
console.log("✓ public/favicon-32.png");

// ── og-image.jpg 1200×630 ───────────────────────────────────────────────
// 3-warstwowy gradient ciemnego tła + plaster badge w lewym górnym rogu
// + duży headline + sub + stopka chipsami.
const ogChipsSvg = (() => {
  if (!BRAND.ogChips.length) return "";
  let x = 96;
  const parts = [];
  BRAND.ogChips.forEach((chip, i) => {
    if (i > 0) {
      parts.push(`<text x="${x}" y="540">·</text>`);
      x += 22;
    }
    parts.push(`<text x="${x}" y="540">${chip}</text>`);
    x += chip.length * 11 + 22; // crude width estimate
  });
  return parts.join("");
})();

const ogSvg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="${BRAND.accentDeep}"/>
      <stop offset="60%" stop-color="${BRAND.accent}"/>
      <stop offset="100%" stop-color="${BRAND.accentDark}"/>
    </linearGradient>
    <linearGradient id="badge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#e0e7ff" stop-opacity="0.85"/>
    </linearGradient>
  </defs>

  <rect width="1200" height="630" fill="url(#bg)"/>

  <g fill="${BRAND.textOnDark}" fill-opacity="0.05">
    <circle cx="200" cy="120" r="3"/>
    <circle cx="980" cy="80" r="2"/>
    <circle cx="1100" cy="500" r="4"/>
    <circle cx="120" cy="540" r="3"/>
    <circle cx="900" cy="280" r="2"/>
  </g>

  <g transform="translate(96, 96)">
    <rect width="96" height="96" rx="22" ry="22" fill="url(#badge)"/>
    <text x="48" y="69" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="60" font-weight="500" fill="${BRAND.accentDeep}">${BRAND.shortName}</text>
  </g>

  <text x="220" y="142" font-family="Inter, -apple-system, 'Segoe UI', Helvetica, sans-serif" font-size="34" font-weight="600" fill="${BRAND.textOnDark}">${BRAND.siteName}</text>
  <text x="220" y="174" font-family="Inter, -apple-system, 'Segoe UI', Helvetica, sans-serif" font-size="15" font-weight="500" fill="${BRAND.textOnDarkMuted}" letter-spacing="2">${BRAND.tagline}</text>

  <text x="96" y="340" font-family="Georgia, 'Times New Roman', serif" font-size="68" font-weight="500" fill="${BRAND.textOnDark}">${BRAND.ogHeadline}</text>
  <text x="96" y="420" font-family="Georgia, 'Times New Roman', serif" font-size="40" font-weight="500" fill="${BRAND.textOnDarkMuted}">${BRAND.ogSubline}</text>

  <g font-family="Inter, -apple-system, sans-serif" font-size="20" font-weight="500" fill="#dbeafe">
    ${ogChipsSvg}
  </g>
</svg>`);

await sharp(ogSvg)
  .jpeg({ quality: 82, progressive: true, mozjpeg: true })
  .toFile(resolve(PUBLIC, "og-image.jpg"));
console.log("✓ public/og-image.jpg");

console.log("\nWygenerowane assety:");
console.log("  - public/favicon.svg          (już istniał)");
console.log("  - public/favicon-32.png       (32×32 PNG)");
console.log("  - public/apple-touch-icon.png (180×180 PNG)");
console.log("  - public/og-image.jpg         (1200×630 JPEG)");
console.log("\nPo zmianach: ./deploy.sh");
