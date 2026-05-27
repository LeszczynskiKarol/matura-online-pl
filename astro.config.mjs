import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import icon from "astro-icon";
import mdx from "@astrojs/mdx";
import tailwindcss from "@tailwindcss/vite";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

const SITE = "https://www.matura-online.pl";

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
      changefreq: "weekly",
      priority: 0.7,
      filter: (page) => !page.includes("/polityka-prywatnosci"),
      serialize(item) {
        if (item.url === `${SITE}/`) item.priority = 1.0;
        if (item.url.includes("/zadanie-")) item.priority = 0.9;
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
