// The data contract, published beside the pages it built, byte for byte.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export function GET() {
  const body = readFileSync(resolve(process.cwd(), "data/leaderboard.json"));
  return new Response(body, { headers: { "Content-Type": "application/json; charset=utf-8" } });
}
