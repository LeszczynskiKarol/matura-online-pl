import { defineCollection, z, reference } from "astro:content";
import { glob } from "astro/loaders";

// ────────────────────────────────────────────────────────────────
// Subjects — przedmioty maturalne (matematyka, biologia, ...).
// Każdy subject ma slug = część URL, np. /matematyka/.
// ────────────────────────────────────────────────────────────────
const subjects = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/subjects" }),
  schema: z.object({
    name: z.string(),                  // "Matematyka"
    nameMianownik: z.string(),         // "matematyka" (do tekstu)
    nameDopelniacz: z.string(),        // "matematyki" (z matury matematyki)
    slug: z.string(),                  // "matematyka"
    icon: z.string(),                  // np. "lucide:sigma"
    order: z.number().default(99),
    color: z.string().default("teal"), // tailwind color name
    description: z.string(),
    longDescription: z.string().optional(),
    // Czy mamy treść w tej sesji (dla MVP — tylko matma ma demo)
    hasContent: z.boolean().default(false),
  }),
});

// ────────────────────────────────────────────────────────────────
// Arkusze — konkretne arkusze CKE (przedmiot × rok × sesja × poziom).
// slug = "matematyka-2024-maj-pp" → URL /matematyka/2024-maj-pp/
// ────────────────────────────────────────────────────────────────
const arkusze = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/arkusze" }),
  schema: z.object({
    subject: reference("subjects"),
    rok: z.number(),
    sesja: z.enum(["maj", "czerwiec", "sierpien", "marzec", "probna"]),
    poziom: z.enum(["pp", "pr"]),  // podstawowy / rozszerzony
    formula: z.string().default("Formuła 2023"),
    symbol: z.string(),            // np. "MMAP-P0-100"
    dataPubl: z.string(),          // "8 maja 2024 r."
    liczbaZadan: z.number(),
    liczbaPunktow: z.number(),
    czasMinut: z.number(),
    pdfArkuszUrl: z.string().url().optional(), // link na CKE.gov.pl
    pdfKluczUrl: z.string().url().optional(),
    opis: z.string().optional(),
    audioUrl: z.string().url().optional(),     // MP3 dla zadań słuchania (jezyk angielski)
    audioTranscriptUrl: z.string().url().optional(), // PDF z transkrypcją na CKE
  }),
});

// ────────────────────────────────────────────────────────────────
// Zadania — pojedyncze zadania CKE z pełnym rozwiązaniem.
// slug = "matematyka-2024-maj-pp-1" → URL /matematyka/2024-maj-pp/zadanie-1
// Body w MDX = długie rozwiązanie (z KaTeX, blokami .krok, .pulapka).
// ────────────────────────────────────────────────────────────────
const zadania = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/zadania" }),
  schema: z.object({
    arkusz: reference("arkusze"),
    subject: reference("subjects"),
    nr: z.number(),                 // numer zadania w arkuszu
    punkty: z.number(),              // 1, 2, 3, ...
    typ: z.enum([
      "zamkniete-abcd",
      "zamkniete-pf",
      "zamkniete-dobierz",
      "otwarte-krotkie",
      "otwarte-rozszerzone",
      "dowod",
    ]),
    topic: z.string(),               // "wartość bezwzględna", "wielomiany"
    difficulty: z.number().min(1).max(5).default(3),
    tresc: z.string(),               // krótka treść (do meta description + listy)
    odpowiedz: z.string(),           // np. "B" lub "x = 2, √3, -√3"
    pulapka: z.string().optional(),  // typowy błąd, 1-2 zdania
    wymaganie: z.string().optional(),// "I.7 — interpretacja geometryczna wartości bezwzględnej"
    podobne: z.array(z.string()).default([]), // slugi innych zadań
    hasAudio: z.boolean().default(false),     // zadanie ze słuchaniem (renderuje player)
    audioUrl: z.string().url().optional(),    // MP3 per zadanie (gdy mamy pocięte na pojedyncze pliki — dla angielskiego)
    // Obraz strony arkusza CKE — renderowany przez szablon TUŻ POD linią "Źródło",
    // przed sekcją Rozwiązanie (żeby odpowiedzi były pod arkuszem, nie nad nim).
    zrodloImg: z.string().optional(),
    zrodloImgAlt: z.string().optional(),
    zrodloImgCaption: z.string().optional(),
    zrodloPdfPage: z.number().optional(),
  }),
});

export const collections = { subjects, arkusze, zadania };
