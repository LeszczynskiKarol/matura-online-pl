# Launch report — matura-online.pl

**Data launchu**: 2026-05-27
**Mode**: szkielet + 3 demo strony (uzgodnione z Karolem przed startem)

---

## ✅ Live

- 🌐 **https://www.matura-online.pl/** — strona główna z listą 10 przedmiotów
- 🌐 **https://matura-online.pl/** — 301 redirect → www
- 📚 **https://www.matura-online.pl/matematyka/** — subject hub
- 📄 **https://www.matura-online.pl/matematyka/2024-maj-pp/** — arkusz hub (31 zadań, 3 z rozwiązaniem)
- 📐 3× strony zadań demo:
  - `/matematyka/2024-maj-pp/zadanie-1/` — wartość bezwzględna (1 pkt, zamknięte)
  - `/matematyka/2024-maj-pp/zadanie-3/` — dowód podzielności (2 pkt, otwarte z dwoma sposobami)
  - `/matematyka/2024-maj-pp/zadanie-9/` — wielomian metodą grupowania (3 pkt)
- 9× przedmioty "wkrótce" (placeholdery, gotowe do wypełnienia w MVP-100)

---

## 🛠 Co zostało skonfigurowane

### DNS / domena
- `matura-online.pl` na koncie Karola (Aftermarket, expires 2026-07-08)
- NS-y zmienione: Aftermarket → Route53 AWS (4× `awsdns-*`)
- Hosted zone: `Z03980322EDKLYBP3DCJL`

### AWS infrastructure
- **S3**: bucket `www.matura-online.pl` (public read, website hosting) + bucket `matura-online.pl` (301 redirect)
- **ACM cert** (us-east-1): `cbd6515b-7242-4b36-a5c0-634e0be9bffc` (`www.matura-online.pl` + SAN `matura-online.pl`)
- **CloudFront**:
  - `EWPUJ4X7VMGIQ` → www (cache: HTML no-store, assets 1 rok, 404 fallback)
  - `E2XFMZDFBGL9FG` → naked redirect
- **Route53**: A + AAAA alias na obie dystrybucje + TXT GSC verification

### Stack
- Astro 5.18.2 + Tailwind 4 + KaTeX (remark-math + rehype-katex)
- MDX dla treści zadań (frontmatter + body z math)
- Content collections: `subjects` (10), `arkusze` (1), `zadania` (3) — type-safe schema w `src/content.config.ts`
- 17 stron static-built, sitemap-index.xml z 16 indexable URL-i
- TypeScript strict
- Dark/light theme (`prefers-color-scheme` default + toggle, init `is:inline`)

### Analytics
- **GA4**: `properties/539248479` / measurement ID `G-BJ3MW4B1GB` (auto-provisioned, account "Root dla zaplecz z astro generator")
- Consent Mode v2 wpięty (denied defaults, PL/EU override, restore from localStorage)
- Cookie banner controls `gtag('consent', 'update')` — działa idiomatycznie

### CI/CD
- Repo: **public** https://github.com/LeszczynskiKarol/matura-online-pl
- IAM role: `gh-deploy-matura-online-pl` (OIDC, trust policy ograniczone do `repo:LeszczynskiKarol/matura-online-pl:ref:refs/heads/main`)
- GitHub secrets: `AWS_ROLE_ARN`, `AWS_REGION`, `S3_BUCKET`, `CLOUDFRONT_DIST_ID` (auto-zsetowane)
- Workflow `.github/workflows/deploy.yml` — push do main → build + S3 sync + CF invalidation
- Pierwszy run zielony (workflow_dispatch po wstępnym race condition z sekretami)

### Search Console / seo_panel
- **GSC sc-domain**: `sc-domain:matura-online.pl` dodany, **DNS_TXT verified** (`google-site-verification=c9Gw3tGsSwZQOnmuTPScG90x5ZliOSFWJ3YjqCwqFzY`)
- Sitemap submitted: `https://www.matura-online.pl/sitemap-index.xml`
- Próba delegate ownership do `karolleszczynskikorektor@gmail.com` przez API: **OK** (`owners` zawiera Karol email po PUT)
- Wpis w prod `seo_panel.Domain`: `cm4463e5bb8000e94ff0b2b4` (linkGroup=`EDU`, role=`SATELLITE`, category=`CONTENT_SITE`, githubRepo=`matura-online-pl`)
- Wpis w prod `seo_panel.DomainIntegration`: `cm39d89e06df02e3e29c5c2a` (GOOGLE_ANALYTICS → `properties/539248479`)

### Weryfikacja live
- `curl https://www.matura-online.pl/` → **200 OK**
- `curl https://matura-online.pl/` → **301** → www
- `curl https://www.matura-online.pl/matematyka/2024-maj-pp/zadanie-9/` → **200 OK**
- `curl https://www.matura-online.pl/sitemap-index.xml` → XML z `sitemap-0.xml`
- KaTeX renderuje w HTML (klasy `katex` i `katex-display` obecne)
- OG title prawidłowy na stronach zadań
- JSON-LD `LearningResource` + `BreadcrumbList` obecny

---

## ⚠️ Do uzupełnienia przez Karola

### Krytyczne — żeby Karol miał pełną kontrolę

- [ ] **GSC: dodaj property w swoim panelu** — jeśli po próbie delegate przez API nie widzisz `sc-domain:matura-online.pl` w https://search.google.com/search-console, dodaj ręcznie:
  - Add property → Domain → wpisz `matura-online.pl`
  - GSC sprawdzi TXT (już istnieje w Route53) → **weryfikacja natychmiastowa** (10 sekund klikania).

- [ ] **GA4 ↔ GSC link** (API nie istnieje — manual UI only):
  - https://analytics.google.com/ → Property `matura-online.pl` → Admin → Product links → Search Console links → Link → wybierz `sc-domain:matura-online.pl` → Submit
  - Bez tego linka raporty "Search Console" w GA4 są puste.

### Dane administracyjne (opcjonalne)

- [ ] **Polityka prywatności — NIP i adres** — w `src/config/site.ts` placeholdery `ADMIN_ADDRESS_PLACEHOLDER`, `NIP_PLACEHOLDER`. Strona realnie nie zbiera danych (brak formularza, brak konta), więc RODO ma minimalne zastosowanie. Można zostawić jako placeholder, można uzupełnić jeśli Karol chce być formalnie compliant.

- [ ] **Skrzynka kontakt@matura-online.pl** — w stopce i w polityka-prywatnosci jest podany ten adres. Karol może założyć ją na Aftermarket (forward na osobistą skrzynkę) — MX-y na Aftermarket nie są ustawione (bo brak formularza, brak realnej potrzeby). Wystarczy alias w Aftermarket gdyby ktoś jednak pisał.

### Następne fazy z briefu strategicznego

- [ ] **Faza 2 (~2 tyg)**: MVP-100 — wypełnić matematykę 2024 maj PP + PR, 2025 maj PP + PR (~100 stron). Karol ma własny PDF scraper — warto sprawdzić czy pasuje do pipeline'u ekstrakcji.
- [ ] **Faza 3 (~8-12 tyg)**: pomiar GSC + GA4 + czas na stronie + scroll depth. Decyzja go/no-go na skalę.
- [ ] **Faza 4**: jeśli MVP rusza — skala na chem/fiz/geo/hist/wos/info; potem bio (trudniejsze, biologhelp.pl jest silny) i polski (interpretacje, nakładka z maturapolski-static).

---

## 🧷 TXT w Route53 — NIE KASOWAĆ

`google-site-verification=c9Gw3tGsSwZQOnmuTPScG90x5ZliOSFWJ3YjqCwqFzY` na apex `matura-online.pl` **musi zostać na zawsze**. GSC robi re-check ownership co ~7 dni — usunięcie TXT = utrata ownership = utrata historii danych.

---

## 📋 Drobnostki

- **PSI score**: nie zmierzono w tej sesji — Google PSI API zwróciło quota exceeded (anonymous quota = 0/day, API key dla PSI nie znaleziono w `D:\seo-panel\backend\.env`). Strona jest static + CloudFront + inline CSS + preloaded fonts → spodziewany score mobile ≥90, desktop ≥98. Karol może zmierzyć ręcznie na pagespeed.web.dev.
- **`_commit.txt` na live**: lokalny `deploy.sh` generuje manifest commit SHA i pushuje do S3. Workflow GitHub Actions tego nie kopiuje (template workflowu nie zawiera `_commit.txt` w sync include) — można dodać jako follow-up.
- **Industry GA4**: ustawione na `JOBS_AND_EDUCATION`. Walutę PLN, strefę Europe/Warsaw.
- Brak: formularza kontaktowego, regulaminu, bloga, sklepu (zgodne z briefem).
