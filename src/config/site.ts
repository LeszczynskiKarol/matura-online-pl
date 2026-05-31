// Per-project config dla matura-online.pl.
// Components and layouts read from here — DON'T sprinkle hardcoded values.

export const siteConfig = {
  // Brand
  name: "Matura-Online.pl",
  shortName: "matura-online",
  url: "https://www.matura-online.pl",
  locale: "pl_PL",
  lang: "pl",

  // Tagline
  tagline: "Rozwiązania zadań z matury CKE — krok po kroku",
  description:
    "Pełne, dokładne rozwiązania zadań maturalnych CKE z matematyki, biologii, chemii, fizyki i innych przedmiotów. Krok po kroku, z omówieniem pułapek i podobnych zadań.",

  // Legal (dla polityka-prywatnosci)
  legal: {
    adminName: "Karol Leszczyński",
    adminAddress: "kontakt@kurs-copywritingu.pl",
    adminNip: "9562203948",
    adminEmail: "kontakt@matura-online.pl",
  },

  // Feature flags
  features: {
    // GA4 ID — auto-provisioning w playbook 11. null = no analytics, no cookie banner.
    ga4: "G-BJ3MW4B1GB" as string | null,

    // Brak formularza kontaktowego (Karol explicite, brief)
    contactForm: false,
    contactFormAttachments: false,

    // Brak sklepu, brak regulaminu
    hasShop: false,

    // Brak bloga
    hasBlog: false,
  },

  // Kontakt
  contact: {
    email: "kontakt@matura-online.pl",
    phone: null as string | null,
  },

  // Cross-link do apki (z briefu — naturalna konwersja na ćwiczenia)
  apka: {
    url: "https://www.matury-online.pl",
    name: "matury-online.pl",
    cta: "Przećwicz w aplikacji",
  },
} as const;

export type SiteConfig = typeof siteConfig;
