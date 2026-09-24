// How each model is introduced to a reader the first time a page names it, in plain words. The
// facts are the ones in the data file's engines[].about and engines[].kind; nothing here adds to them.
// (A leading underscore keeps this file out of the site's routes.)
import { engineById } from "../../lib/site.js";

const FAST = "a fast decision model: it answers a yes-or-no question about a text instantly and gives no reasons";

const ABOUT = {
  jev: `Jev is ${FAST}. It runs as an online service, and the confidence it reports for each answer is its own, to two decimal places.`,
  laya: `Laya is ${FAST}. Anyone can download it. We ran it two ways: an Apple MLX build (laya-mlx 0.1.0, the faster one, used wherever we have it) and the original PyTorch build its authors released (laya 0.3.7). They agree to three decimal places, so we show one Laya, and each result says which build gave it. The confidence it reports for each answer is its own.`,
  kev: `Kev is an open-source decision model. It answers questions about text with yes-or-no, choice, or rating answers.`,
};

const SHORT = {
  jev: `Jev is ${FAST}.`,
  laya: `Laya is ${FAST}.`,
  kev: `Kev is an open-source decision model.`,
};

// The full introduction for a model's own page and the list of models.
export const aboutModel = (en) => en.about_plain || ABOUT[en.id] || en.about;
// One sentence, for a page that is about something else.
export const introModel = (en) => SHORT[en.id] || aboutModel(en);

// The models in two sentences, for a page that names them all.
export function introModels() {
  const models = ["jev", "laya", "kev"].map((id) => engineById[id]).filter(Boolean).map((e) => e.label);
  return models.length ? `${models.join(", ").replace(/, ([^,]*)$/, " and $1")} are decision models that answer questions about text.` : "";
}
