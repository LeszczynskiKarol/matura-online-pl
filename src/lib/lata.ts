// Wspólna logika podziału na roczniki matur (rok egzaminu, nie rok szkolny —
// arkusz "maj 2025" to matura 2025, a nie 2024/2025).
//
// Używane przez /matura/ (hub roczników), /matura/[rok]/ i stopkę.

import type { CollectionEntry } from "astro:content";

export type Arkusz = CollectionEntry<"arkusze">;
export type Subject = CollectionEntry<"subjects">;

/** Lata z arkuszami, od najnowszego. */
export function lataZArkuszy(arkusze: Arkusz[]): number[] {
  return [...new Set(arkusze.map((a) => a.data.rok))].sort((a, b) => b - a);
}

/** Slug arkusza w URL przedmiotu: "matematyka-2025-maj-pp" → "2025-maj-pp". */
export function arkuszSlug(arkusz: Arkusz, subjectSlug: string): string {
  return arkusz.id.replace(`${subjectSlug}-`, "");
}

export function poziomLabel(poziom: "pp" | "pr"): string {
  return poziom === "pp" ? "Poziom podstawowy" : "Poziom rozszerzony";
}

export function poziomSkrot(poziom: "pp" | "pr"): string {
  return poziom === "pp" ? "PP" : "PR";
}

/** "arkusz / arkusze / arkuszy" — polska odmiana przez liczebnik. */
export function odmienArkusze(n: number): string {
  if (n === 1) return "arkusz";
  const setki = n % 100;
  const jednosci = n % 10;
  if (jednosci >= 2 && jednosci <= 4 && !(setki >= 12 && setki <= 14)) {
    return "arkusze";
  }
  return "arkuszy";
}

/** "zadanie / zadania / zadań". */
export function odmienZadania(n: number): string {
  if (n === 1) return "zadanie";
  const setki = n % 100;
  const jednosci = n % 10;
  if (jednosci >= 2 && jednosci <= 4 && !(setki >= 12 && setki <= 14)) {
    return "zadania";
  }
  return "zadań";
}

/** Sortowanie arkuszy w obrębie rocznika: rok malejąco, PR przed PP. */
export function sortujArkusze(arkusze: Arkusz[]): Arkusz[] {
  return [...arkusze].sort((a, b) => {
    if (a.data.rok !== b.data.rok) return b.data.rok - a.data.rok;
    if (a.data.poziom !== b.data.poziom) return a.data.poziom === "pr" ? -1 : 1;
    return 0;
  });
}
