// How each model is introduced to a reader the first time a page names it, in plain words. The
// facts are the ones in the data file's engines[].about and engines[].kind; nothing here adds to them.
// (A leading underscore keeps this file out of the site's routes.)
import { engineById } from "../../lib/site.js";

const FAST = "a fast decision model: it answers a yes-or-no question about a text instantly and gives no reasons";

const ABOUT = {
  jev: `Jev is ${FAST}. It runs as an online service, and the confidence it reports for each answer is its own, to two decimal places.`,
  laya: `Laya is ${FAST}. Anyone can download it; we ran the version its authors released (laya 0.3.7), and the confidence it reports for each answer is its own.`,
  "laya-mlx": "Laya-mlx is the same model as Laya, run a different way: an independent version made for Apple computers (laya-mlx 0.1.0). It gives the same answers as Laya to three decimal places. Any Laya result we published before we separated the two came from Laya-mlx.",
};

const SHORT = {
  jev: `Jev is ${FAST}.`,
  laya: `Laya is ${FAST}.`,
  "laya-mlx": "Laya-mlx is the same model as Laya, run a different way.",
};

// The full introduction for a model's own page and the list of models.
export const aboutModel = (en) => en.about_plain || ABOUT[en.id] || en.about;
// One sentence, for a page that is about something else.
export const introModel = (en) => SHORT[en.id] || aboutModel(en);

// The three models in two sentences, for a page that names them all.
export function introModels() {
  const fast = ["jev", "laya"].map((id) => engineById[id]).filter(Boolean).map((e) => e.label);
  const port = engineById["laya-mlx"];
  const first = fast.length ? `${fast.join(" and ")} are fast decision models: they answer a yes-or-no question about a text instantly and give no reasons.` : "";
  return [first, port ? `${port.label} is the same model as ${engineById.laya ? engineById.laya.label : "Laya"}, run a different way.` : ""].filter(Boolean).join(" ");
}
