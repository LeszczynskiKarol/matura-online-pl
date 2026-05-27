# Brief — matura-online.pl

**Mode**: Mode A (interactive) — Karol dostarczył kompletny brief strategiczny przed rozpoczęciem sesji.
**Data**: 2026-05-27

## Pomysł w jednym akapicie

Serwis z **rozwiązaniami zadań CKE krok po kroku** — z omówieniem typowych błędów i punktacji. Cel: per-zadanie URL wynikający z analizy SERP (zapytania typu „matura matematyka 2024 zadanie 28 rozwiązanie") + huby per-arkusz i per-przedmiot. Naturalna konwersja na ćwiczenia w siostrzanej aplikacji `matury-online.pl`.

## Stan danych źródłowych (z briefu Karola)

- **Surowe arkusze CKE**: `D:/matury-online.pl/arkusze/<przedmiot>/<rok>/` — 95 plików PDF, lata 2023–2026, 9 przedmiotów (matma, polski, ang, bio, chem, fiz, geo, hist, info, filozofia). Niezskonsumowane — same PDFy.
- **Baza zadań apki (Question)**: 8 884 zadań, tagowane Subject/Topic, 88% z `explanation`. NIE są powiązane z konkretnymi arkuszami CKE.
- **Wniosek**: trzeba zbudować osobną warstwę danych dla per-zadanie CKE. Bazę apki można potem zmapować jako „podobne zadania ćwiczeniowe".

## Architektura URL

```
/                                          → home, lista przedmiotów
/<przedmiot>/                              → subject hub
/<przedmiot>/<rok>-<sesja>-<poziom>/       → arkusz hub
/<przedmiot>/<rok>-<sesja>-<poziom>/zadanie-<nr>/   → strona zadania
```

Przykład: `/matematyka/2024-maj-pp/zadanie-28/`

Plus przyszłe: `/<przedmiot>/zagadnienia/<topic>/` (agregat zadań z tego topic-u).

## Stos technologiczny

- Astro 5 (static output)
- Tailwind 4 (`@tailwindcss/vite`)
- **KaTeX** (`remark-math` + `rehype-katex`) — wzory matematyczne renderowane przy build, nie przy runtime
- MDX dla treści zadań (frontmatter + body z math)
- Content collections (subjects, arkusze, zadania) — type-safe schema w `src/content.config.ts`
- Astro Icon + lucide / heroicons / tabler
- Sharp do OG image generation
- TypeScript strict

## Decyzje wizualne

- **Paleta**: edu-calm. Light: warm off-white `#f8f7f4` + deep navy text + teal `#0d9488` accent. Dark (nocna nauka — priorytet): rich navy `#0a1220` + brighter teal `#2dd4bf`.
- **Drugi akcent**: indigo `#4f46e5` (light) / `#818cf8` (dark) — dla CTA cross-link do apki.
- **Stany zadania**: zielony (`--color-correct`) dla bloku „Odpowiedź", żółty (`--color-warn`) dla bloku „Pułapka".
- **Typografia**: Inter (sans, UI) + **Fraunces** variable serif (nagłówki, charakterny ale czytelny) + JetBrains Mono (numery kroków, symbole arkuszy).
- **Layout**: max-width `max-w-3xl` (48rem) dla stron zadań (czytelność długich rozwiązań), `max-w-6xl` dla landingu.
- **Motion**: prawie zero. Scroll-in animation tylko na sekcjach landingu. `prefers-reduced-motion` wyłącza wszystko.
- **Co odrzucone**: glow / blur efekty, illustracje hero (value prop trafia tekstem), HeroIllustration component (niepotrzebny w content-heavy site).

## MVP zakres dla tej sesji

Zgodnie z rozmową z Karolem: **szkielet + 2-3 demo strony**. Pełna infrastruktura (DNS, AWS, deploy, CI/CD), content collections z 10 przedmiotami + 1 arkuszem demo + 3 demo zadaniami z autentycznymi treściami i rozwiązaniami z arkusza CKE matma 2024 maj PP.

### Wybrane zadania demo (matematyka 2024 maj PP, wersja A)

1. **Zadanie 1 (1 pkt, zamknięte ABCD)** — nierówność z wartością bezwzględną $|x-1| \geq 3$. Pokazuje konwencję rysunku + typową pułapkę (zamiana kierunku nierówności + zamknięte/otwarte końce).
2. **Zadanie 3 (2 pkt, dowód)** — wykaż, że $n^2 + (n+1)^2 + (n+2)^2$ daje resztę 2 przy dzieleniu przez 3. Dwa sposoby rozwiązania (algebraiczny + analiza reszt). Krytyczna pułapka: sprawdzanie tezy dla kilku $n$ = 0 punktów.
3. **Zadanie 9 (3 pkt, otwarte krótkie)** — rozwiąż $x^3 - 2x^2 - 3x + 6 = 0$ metodą grupowania. Pułapka: dzielenie przez $(x-2)$ bez założenia = utrata rozwiązania.

Trzy różne typy + trzy różne poziomy „search-worthy" = dobry probierz modelu treści.

## Cross-link strategy

Każda strona zadania ma na końcu CTA do `matury-online.pl` (apki Karola, jego flagowy produkt) w sekcji „Przećwicz podobne typy". Wykorzystuje accent #2 (indigo) — wizualnie wyróżniony, ale nie inwazyjny.

## Co świadomie pominięto

- **Formularz kontaktowy** — Karol explicite: brak.
- **Blog** — domyślnie OFF, Karol nie prosił.
- **Regulamin** — brak sprzedaży.
- **GA4** — `null` na start. Auto-provisioning w playbook 11 (krok 5b pipeline'u).
- **Tylko podstawowe analityki** — żadnego Hotjar/Clarity/FB Pixel.

## Do uzupełnienia (Karol — placeholdery)

W `src/config/site.ts`:
- `legal.adminAddress` — `ADMIN_ADDRESS_PLACEHOLDER`
- `legal.adminNip` — `NIP_PLACEHOLDER`

W rzeczywistości serwis nie zbiera danych użytkowników (brak formularza, brak konta) — RODO ma minimalne zastosowanie. Adres/NIP można uzupełnić luźno albo zostawić tylko email kontaktowy jako kanał. Decyzja Karola.

## Kolejne kroki po tej sesji (z briefu — fazy)

1. **Faza 2**: MVP-100 dla matematyki 2024+2025 maj PP+PR (~100 stron) — content writing.
2. **Faza 3**: 8-12 tygodni pomiarów GSC/GA4 — decyzja go/no-go.
3. **Faza 4**: skala na pozostałe przedmioty jeśli MVP rusza.

Content production pipeline (z briefu): hybryda OCR + Claude + manualna weryfikacja. Karol ma własny PDF scraper — do zbadania czy pasuje.
