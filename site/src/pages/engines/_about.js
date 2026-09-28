// How each model is introduced to a reader the first time a page names it, in plain words. The
// facts are the ones in the data file's engines[].about and engines[].kind; nothing here adds to them.
// (A leading underscore keeps this file out of the site's routes.)
import { engines } from "../../lib/site.js";

const FAST = "a fast decision model";

const ABOUT = {
  jev: `Jev is a hosted ${FAST}. We reach it through its maker's software kit, typesafe-sdk, on paid API access. We pay for that access and have no other relationship with its maker. The version tested is jev-1.13.0.`,
  laya: `Laya is an open-source ${FAST}. We reached it at github.com/NandhaKishorM/laya (Apache-2.0). We ran two builds on our own Apple-silicon hardware. The independent Apple MLX port (laya-mlx 0.1.0) was used wherever we have it; the original PyTorch build (laya 0.3.7) was used where the MLX build has not run yet. The headline results matched, though probabilities can differ by up to about 0.02 on a single text.`,
  kev: `Kev is an open-source ${FAST}. We reached it at github.com/jaredpalmer/kev. We ran it on our own Apple-silicon hardware with checkpoint jaredpalmer/kev-0.8b@54f4f8777356cd5bbbb6c6919c657f26e6f2f6d8, base model Qwen/Qwen3.5-0.8B-Base@dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68, MLX backend, bfloat16 precision.`,
};

const SHORT = {
  jev: `Jev is a hosted ${FAST}.`,
  laya: `Laya is an open-source ${FAST}.`,
  kev: `Kev is an open-source ${FAST}.`,
};

// The full introduction for a model's own page and the list of models.
export const aboutModel = (en) => en.about_plain || ABOUT[en.id] || en.about;
// One sentence, for a page that is about something else.
export const introModel = (en) => SHORT[en.id] || aboutModel(en);

// The models in one sentence, for a page that names them all. Every model we've tested, not a
// fixed list -- this reads correctly whether we've tested two models or ten.
export function introModels() {
  const labels = engines.map((e) => e.label);
  return labels.length ? `${labels.join(", ").replace(/, ([^,]*)$/, " and $1")} are decision models that answer questions about text.` : "";
}
