import katex from "katex";

// Renderuje plain-text z fragmentami $...$ (inline) i $$...$$ (block) do HTML z KaTeX.
// Pozostałe znaki są escape'owane HTML-em — żeby pole frontmatter mogło zawierać <, > itp.
// Wynik wstawia się przez `set:html={...}`.
//
// renderInlineMath  — tylko matematyka (reszta jako zwykły, zescapowany tekst).
// renderRichText    — matematyka + lekki inline-markdown (**bold**, *italic*, `code`),
//                     dla pól frontmatter które autorzy piszą w markdown (tresc, longDescription).

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
// Kolejność: bold przed italic, żeby ** nie złapało się jako dwa *.
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

export function renderRichText(text: string): string {
  return renderCore(text, (chunk) => inlineMarkdown(escapeHtml(chunk)));
}
