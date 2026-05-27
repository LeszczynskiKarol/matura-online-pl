import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import icon from "astro-icon";
import mdx from "@astrojs/mdx";
import tailwindcss from "@tailwindcss/vite";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { readFileSync, readdirSync } from "node:fs";

const SITE = "https://www.matura-online.pl";

// Subject huby bez własnych arkuszy → noindex,follow, wykluczone z sitemap.
// Single source of truth: src/content/subjects/*.md (frontmatter `hasContent: true`).
// Aktualizuje się automatycznie po edycji frontmatter w content collection.
const SUBJECTS_DIR = "./src/content/subjects";
const subjectsWithoutContent = readdirSync(SUBJECTS_DIR)
  .filter((f) => f.endsWith(".md") || f.endsWith(".mdx"))
  .filter((f) => {
    const content = readFileSync(`${SUBJECTS_DIR}/${f}`, "utf-8");
    return !/^hasContent:\s*true/m.test(content);
  })
  .map((f) => f.replace(/\.(md|mdx)$/, ""));

const ARKUSZ_HUB_RE =
  /\/\d{4}-(maj|czerwiec|sierpien|marzec|probna)-(pp|pr)\/$/;

export default defineConfig({
  site: SITE,

  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [[rehypeKatex, { strict: false, output: "html" }]],
  },

  integrations: [
    mdx({
      remarkPlugins: [remarkMath],
      rehypePlugins: [[rehypeKatex, { strict: false, output: "html" }]],
    }),
    icon({
      include: {
        lucide: ["*"],
        heroicons: ["*"],
        tabler: ["*"],
      },
    }),
    sitemap({
      lastmod: new Date(),
      changefreq: "monthly",
      priority: 0.7,
      filter: (page) => {
        if (page.includes("/polityka-prywatnosci")) return false;
        for (const slug of subjectsWithoutContent) {
          if (page.endsWith(`/${slug}/`)) return false;
        }
        return true;
      },
      serialize(item) {
        if (item.url === `${SITE}/`) {
          item.priority = 1.0;
          item.changefreq = "weekly";
          return item;
        }
        if (item.url.includes("/zadanie-")) {
          item.priority = 0.9;
          item.changefreq = "yearly";
          return item;
        }
        if (ARKUSZ_HUB_RE.test(item.url)) {
          item.priority = 0.7;
          item.changefreq = "monthly";
          return item;
        }
        return item;
      },
    }),
  ],

  output: "static",

  build: {
    assets: "_assets",
    inlineStylesheets: "always",
  },

  vite: {
    plugins: [tailwindcss()],
    build: {
      cssMinify: true,
    },
  },
});
