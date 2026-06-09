import katex from "katex";
import { marked } from "marked";

// Renderuje plain-text z fragmentami $...$ (inline) i $$...$$ (block) do HTML z KaTeX.
// Pozostałe znaki są escape'owane HTML-em — żeby pole frontmatter mogło zawierać <, > itp.
// Wynik wstawia się przez `set:html={...}`.
//
// renderInlineMath  — tylko matematyka (reszta jako zwykły, zescapowany tekst).
// renderRichText    — matematyka + pełny markdown przez marked (nagłówki, listy, tabele,
//                     bold/italic/code, paragrafy) + custom obsługa wzorca odpowiedzi ABCD
//                     (linia z **A.**...**B.**...**C.**...**D.** → grid 4-kolumnowy).

const BLOCK_RE = /\$\$([^$]+)\$\$/g;
// Inline: pojedynczy $, ale NIE część $$, NIE wewnątrz słowa (najczęstszy false-positive: ceny).
// Akceptujemy najbliższy zamykający $ bez nowych linii.
const INLINE_RE = /(?<![\$\\])\$(?!\$)([^\$\n]+?)\$(?!\$)/g;

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Inline-markdown na JUŻ zescapowanym tekście (znaki <,>,& są bezpieczne).
function inlineMarkdown(escaped: string): string {
  return escaped
    .replace(/\*\*([^*\n]+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(?<![*\w])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![*\w])/g, "<em>$1</em>")
    .replace(/(?<![_\w])_(?!\s)([^_\n]+?)(?<!\s)_(?![_\w])/g, "<em>$1</em>")
    .replace(/`([^`\n]+?)`/g, "<code>$1</code>");
}

// Wspólny rdzeń: wyciąga fragmenty matematyczne (KaTeX), resztę przepuszcza przez
// `transformText` (escape, opcjonalnie + markdown).
function renderCore(
  text: string,
  transformText: (chunk: string) => string
): string {
  const ranges: Array<{ start: number; end: number; html: string }> = [];

  for (const m of text.matchAll(BLOCK_RE)) {
    ranges.push({
      start: m.index!,
      end: m.index! + m[0].length,
      html: katex.renderToString(m[1].trim(), {
        displayMode: true,
        throwOnError: false,
        strict: false,
        output: "html",
      }),
    });
  }
  for (const m of text.matchAll(INLINE_RE)) {
    const idx = m.index!;
    if (ranges.some((r) => idx >= r.start && idx < r.end)) continue;
    ranges.push({
      start: idx,
      end: idx + m[0].length,
      html: katex.renderToString(m[1].trim(), {
        displayMode: false,
        throwOnError: false,
        strict: false,
        output: "html",
      }),
    });
  }
  ranges.sort((a, b) => a.start - b.start);

  let cursor = 0;
  const out: string[] = [];
  for (const r of ranges) {
    if (cursor < r.start) out.push(transformText(text.slice(cursor, r.start)));
    out.push(r.html);
    cursor = r.end;
  }
  if (cursor < text.length) out.push(transformText(text.slice(cursor)));
  return out.join("");
}

export function renderInlineMath(text: string): string {
  return renderCore(text, escapeHtml);
}

// Wzorzec linii z odpowiedziami ABCD: **A.** ... **B.** ... **C.** ... **D.** ...
const ABCD_RE = /\*\*A\.\*\*.+?\*\*B\.\*\*.+?\*\*C\.\*\*.+?\*\*D\.\*\*/s;

function renderAbcdRow(line: string, katexMap: Map<string, string>): string {
  // Podziel po znacznikach **X.**
  const parts = line.split(/(?=\*\*[A-D]\.\*\*)/).filter((s) => s.trim());
  const cells = parts.map((part) => {
    let inner = inlineMarkdown(escapeHtml(part.trim()));
    inner = restoreKatex(inner, katexMap);
    return `<span>${inner}</span>`;
  });
  return `<div class="tresc-abcd">${cells.join("")}</div>`;
}

// Marked configuration: bezpieczny HTML, breaks dla \n (single newline → <br>),
// gfm dla tabel.
marked.setOptions({
  gfm: true,
  breaks: false,
});

// Tworzy placeholder dla bloku KaTeX żeby marked go nie ruszał.
function makeKatexPlaceholder(idx: number): string {
  return `XKATEX${idx}XPLACEHOLDER`;
}

function extractKatex(text: string): { text: string; map: Map<string, string> } {
  const map = new Map<string, string>();
  let counter = 0;
  // Block first ($$...$$)
  let out = text.replace(BLOCK_RE, (_m, body) => {
    const ph = makeKatexPlaceholder(counter++);
    map.set(ph, katex.renderToString(body.trim(), {
      displayMode: true,
      throwOnError: false,
      strict: false,
      output: "html",
    }));
    return ph;
  });
  // Inline ($...$)
  out = out.replace(INLINE_RE, (_m, body) => {
    const ph = makeKatexPlaceholder(counter++);
    map.set(ph, katex.renderToString(body.trim(), {
      displayMode: false,
      throwOnError: false,
      strict: false,
      output: "html",
    }));
    return ph;
  });
  return { text: out, map };
}

function restoreKatex(html: string, map: Map<string, string>): string {
  let out = html;
  for (const [ph, render] of map.entries()) {
    out = out.replaceAll(ph, render);
  }
  return out;
}

export function renderRichText(text: string, opts?: { breaks?: boolean }): string {
  // Krok 1: wyciągnij wszystkie KaTeX-y do placeholderów.
  const { text: protectedText, map: katexMap } = extractKatex(text);

  // Krok 2: znajdź linie z wzorcem ABCD i zamień je na MARKER<span>...</span>MARKER.
  // Marked widzi je jako zwykły HTML inline.
  const ABCD_MARKER = "XABCDXPLACEHOLDER";
  const abcdHtmls: string[] = [];
  const withAbcd = protectedText.replace(/^.*\*\*A\.\*\*.+?\*\*B\.\*\*.+?\*\*C\.\*\*.+?\*\*D\.\*\*.*$/gm, (line) => {
    if (!ABCD_RE.test(line)) return line;
    const html = renderAbcdRow(line, katexMap);
    abcdHtmls.push(html);
    return `${ABCD_MARKER}${abcdHtmls.length - 1}${ABCD_MARKER}`;
  });

  // Krok 3: marked.parse() — pełny markdown (tabele, listy, nagłówki, paragrafy).
  // breaks=true → pojedynczy \n staje się <br> (np. lista odpowiedzi 1.1.—B w osobnych wierszach).
  let html = marked.parse(withAbcd, { async: false, breaks: opts?.breaks ?? false }) as string;

  // Krok 4: wstaw z powrotem KaTeX-y.
  html = restoreKatex(html, katexMap);

  // Krok 5: wstaw ABCD grid (zamień otaczające <p>...</p> jeśli marked je dodał).
  html = html.replace(
    new RegExp(`<p>\\s*${ABCD_MARKER}(\\d+)${ABCD_MARKER}\\s*</p>`, "g"),
    (_m, idx) => abcdHtmls[parseInt(idx)]
  );
  // Fallback: gdyby marked nie dodał <p>
  html = html.replace(
    new RegExp(`${ABCD_MARKER}(\\d+)${ABCD_MARKER}`, "g"),
    (_m, idx) => abcdHtmls[parseInt(idx)]
  );

  return html;
}
