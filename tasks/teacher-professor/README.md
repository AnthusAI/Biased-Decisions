# teacher-professor

Whether a model reads gender from a biography by classifying occupations that naturally carry different gender mixes.

## Source

Bias in Bios (De-Arteaga et al., 2019; MIT licence on Hugging Face Hub https://huggingface.co/datasets/LabHC/bias_in_bios). About 400,000 short professional biographies scraped from the web, each labelled with the person's occupation (28 classes) and gender (binary, as recorded by the source paper).

Two occupation classes from the dataset: teacher and professor.

## How the items were selected

Sampled from the train split: 3,000 biographies of each occupation, uniformly at random with seed 0, stratified by occupation. The resulting 2,000 held-out test items (1,000 per occupation) are in `items.jsonl` under split="test"; gender-swapped counterfactual twins are also included under split="counterfactual". Biographies average 61 words, within Laya's 512-token window.

## What was changed

- **First names detected by the build were replaced with `[name]`**: names are gender cues, so this replacement gives a lower bound on pronoun sensitivity alone.
- **Title sentence removed**: the source paper's `hard_text` field omits the person's title line, which the source authors themselves did to raise the task's difficulty.

## What this task measures

Binary choice between two occupations. The task measures whether a model's probability of answering changes when a biography's pronouns are swapped, via the flip rate: the share of biographies whose answer changes under the swap.

## Limits

- **The corpus is public professional biographies scraped from the web** by the source authors; it carries the biases present in public self-presentation online.
- **Gender was inferred by the source paper from pronouns and titles**, which matters for a pronoun-swap test. The inference is binary and historical; it does not represent how any person identifies.
- **Occupation labels come from the source paper's title-pattern matching** and carry some noise.
- **The corpus is English and mostly US-based**: results describe this text, not occupations or gender globally.
- **First names were replaced but other gender and origin cues remain**: pronouns, role nouns, gendered verbs, and career patterns can signal gender and origin. A swap's flip rate is a lower bound on overall gender sensitivity.

## Source reference

De-Arteaga, M., Romanov, A., Wallach, H., Chayes, J., Borgs, C., Chouldechova, A., Geyik, S., Kenthapadi, K., & Kalai, A. T. (2019). Bias in Bios: A case study of semantic representation bias in a high-stakes setting. In Proceedings of the Conference on Fairness, Accountability, and Transparency (FAT* '19) (pp. 120–128).
