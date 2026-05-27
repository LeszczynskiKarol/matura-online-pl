# Design system — matura-online.pl

**Mood:** edukacyjny, spokojny, czytelny. Strona jest content-heavy — uczeń spędza tu po 5-15 minut na zadaniu, czyta długie rozwiązania krok po kroku z wzorami matematycznymi. Czytelność > efekty wizualne.

**Tone:** rzeczowy, pomocny, partnerski. Nie infantylny ("hej maturzysto"), nie korpomowy ("wspieramy proces nauki"). Tonacja jak dobry korepetytor — wiesz że zdasz, ale pokażę ci błąd, którego nie widzisz.

## Paleta

### Light theme (dzień, nauka popołudniem)
| Token | Wartość | Użycie |
|---|---|---|
| `--color-bg` | `#f8f7f4` | warm off-white, mniej męczy oczy niż czysta biel |
| `--color-bg-elevated` | `#ffffff` | karty, treść zadań |
| `--color-bg-subtle` | `#f1efe9` | naprzemienne sekcje, code blocks |
| `--color-text` | `#0f172a` | slate-900 |
| `--color-text-muted` | `#475569` | slate-600 |
| `--color-accent` | `#0d9488` | teal-600 — primary CTA, linki, krok-counter |
| `--color-accent-2` | `#4f46e5` | indigo-600 — CTA do apki matury-online.pl |

### Dark theme (nocna nauka — Karol's priority)
| Token | Wartość | Użycie |
|---|---|---|
| `--color-bg` | `#0a1220` | rich navy, nie czarny |
| `--color-bg-elevated` | `#111c30` | karty |
| `--color-text` | `#f1f5f9` | slate-100 |
| `--color-accent` | `#2dd4bf` | teal-400, lepszy kontrast na ciemnym |
| `--color-accent-2` | `#818cf8` | indigo-400 |

### Stany zadania
- `--color-correct` (zielony) → blok "Odpowiedź"
- `--color-warn` (żółty) → blok "Pułapka / typowy błąd"

## Typografia

| Rola | Font | Powód |
|---|---|---|
| UI / treść | **Inter** | klasyczna czytelna sans, najlepiej testowana na ekranach edu |
| Nagłówki | **Fraunces** (variable serif) | osobowość bez bycia "fancy", świetny w dużych rozmiarach, polskie ogonki OK |
| Mono / numery kroków | **JetBrains Mono** | dla numeracji kroków i symboli arkuszy (MMAP-P0-100) |
| Math | **KaTeX** (Computer Modern) | standard typograficzny matematyki, lepszy niż MathJax |

Skala typograficzna: minor third (1.2). Display max ~4.5rem.

## Layout

- **Max-width zawartości**: `max-w-6xl` (72rem) dla landingu, `max-w-3xl` (48rem) dla stron zadań (lepsza czytelność długich rozwiązań).
- **Spacing**: dużo whitespace pionowego (`py-20` sekcje), zwarty horyzontalny.
- **Karty (subjects, arkusze, zadania)**: 1px border + lekki hover (translate + accent border). Bez shadow, bez glow.

## Motion

- Scroll-in animation tylko na sekcjach landingu (IntersectionObserver, 600ms). 
- `prefers-reduced-motion` → wszystko wyłączone.
- Brak hover-effects na linkach poza color transition.

## Komponenty wizualne — które używamy

| Komponent | Gdzie | Notatka |
|---|---|---|
| `<Logo>` | nav, footer | monogram "M.o" w teal |
| `<IconBadge>` | sekcje hub, eyebrow nad H2 | accent / muted tone |
| `<FeatureCard>` | "co tu znajdziesz" sekcja na home | grid 3 kolumny |
| `<StatBlock>` | stat row pod hero | 4× liczba+label |
| `<BackgroundDecor>` | hero only — variant="mesh" subtle | NIE w każdej sekcji |
| `<ThemeToggle>` | nav | dark/light switch |

**Czego NIE używamy** (specyficzne dla matura-online):
- `<HeroIllustration>` — niepotrzebny, value prop trafia tekstem
- `<ContactForm>` — brak formularza
- glow / blur efekty — Karol's hard rule

## Specyficzne dla content typu "zadanie"

CSS classes:
- `.tresc-zadania` — wyróżniony blok z treścią oryginalnego zadania CKE (lewy border indigo)
- `.krok` (w `.kroki-lista`) — pojedynczy krok rozwiązania z auto-counter
- `.odpowiedz` — końcowa odpowiedź (zielone tło, check icon)
- `.pulapka` — typowy błąd (żółte tło, warning icon)
- `.katex-display` — math block (lewy border teal, kontener z bg-elevated)

## Co bym powiedział uczniowi gdyby zapytał "po co ten design"

> Spędzasz tu 10 minut z jednym zadaniem. Strona musi się usunąć z drogi: czarny tekst na warm-white, duża czcionka, wzory w KaTeX (nie obrazki, nie laggy MathJax), kroki ponumerowane wyraźnie, pułapka osobnym żółtym blokiem żebyś jej nie minął. Tryb nocny bo połowa nauki to wieczorem.
