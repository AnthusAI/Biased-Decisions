// /og/<page>.png: one Open Graph card per page, rendered at build time.
import { ogPages } from "../../lib/site.js";
import { ogEnabled, renderPng } from "../../lib/og.js";

export function getStaticPaths() {
  if (!ogEnabled) return [];
  return ogPages().map(({ slug, card }) => ({ params: { slug }, props: { card } }));
}

export async function GET({ props }) {
  return new Response(await renderPng(props.card), { headers: { "Content-Type": "image/png" } });
}
