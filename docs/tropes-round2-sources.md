# Round 2 of the trope studies: sources read so far (2026-09-26)

The antisemitism study (`docs/antisemitic-tropes-preregistration.md`) has the in-depth design: several wordings per
stereotype, several ways of saying who the person is, a second text source. A study that lists only antisemitic stereotypes is
lopsided, so round 2 applies the same design to other groups. Nothing below is used unless it says **read directly**, meaning
the page or paper was opened and its content checked against the stereotype it is cited for. Anything else is a lead.

## Muslims (Islamophobic stereotypes)

| stereotype (paraphrased) | source | status |
|---|---|---|
| violence, terrorism | CAIR, "Islamophobia 101" (islamophobia.org/islamophobia-101/, 2026); ADL, "Myths and Facts about Muslim People and Islam" (2017, archived); Pew Research Center, "How the U.S. general public views Muslims and Islam" (2017); Bridge Initiative, "What is Islamophobia?"; Learning for Justice (formerly Teaching Tolerance), "Debunking Misconceptions About Muslims and Islam" | read directly, all five |
| disloyal, not patriotic, anti-American | ADL myths page (Muslims cannot be patriotic Americans); Pew 2017 (share who call U.S. Muslims anti-American; whether Islam is part of mainstream society) | read directly |
| oppresses women, misogynist | ADL myths page; Bridge Initiative page ("violent, misogynist, untrustworthy"); Learning for Justice | read directly |
| anti-democratic, a civilizational threat | CAIR "Islamophobia 101" ("civilizational subversion", "opposed to normative democratic values"); Pew 2017 (natural conflict between Islam and democracy) | read directly |
| uncivilized, barbaric, backward | CAIR "Islamophobia 101"; Bridge Initiative ("uncivilized and violent") | read directly |
| untrustworthy, dishonest | Bridge Initiative page | read directly (one source) |
| Muslims are all Arab or Middle Eastern (a conflation) | ADL myths page; CAIR ("fundamental otherness") | read directly |

Not used, and why: CNN, "9 tropes about Muslims that are a product of Islamophobia" (2021) returned HTTP 451 and was not read; CAIR
press releases (cair.com) returned HTTP 403 and were not read; Gallup and Pew figures on how many Americans hold each view are
context only and are not used to size any effect.

## Uyghurs (China)

| stereotype (paraphrased) | source | status |
|---|---|---|
| terrorist, extremist, separatist (an authority's label for ordinary religious and cultural practice) | Uyghur Hjelp, "Racism and Ethnic Discrimination in the People's Republic of China: The Case of the Uyghurs" (2026), citing the Xinjiang Police Files | read directly: it documents the labels, not a survey of who holds them |
| criminal, dangerous (false accusations that Uyghur workers assaulted Han women) | Uyghur Human Rights Project, "Discrimination, Mistreatment and Coercion" (2017) | read directly: one incident, so weak support for a general stereotype |
| hard to accommodate (halal food given as a reason not to hire) | Uyghur Human Rights Project (2017) | read directly, weak |

The earlier draft's Uyghur entry was dropped because its citation was the Henan article. These two are proper sources, but they
support "terrorism or extremism" well and the other two only weakly, so round 2 starts with that one stereotype and says so.

## Ethnic groups in Kenya and Nigeria

| stereotype (paraphrased) | source | status |
|---|---|---|
| Kikuyu: exploitative, money-loving | Kuppens, Langer and Ibrahim, "In-group Bias and Ethnic Stereotyping among Secondary School Teachers in Kenya", CRPD Working Paper 55, KU Leuven (2017), N=925 teachers | read directly |
| Luo: intelligent, aggressive | same paper | read directly |
| Luhya (cooking), Kalenjin (athletics) | same paper | read directly; harmless or flattering, so a useful contrast |
| wealth stereotypes about Kikuyu and Igbo | SAFARI (arXiv 2602.22404), AfriStereo (arXiv 2511.22016) | read directly earlier (batch 3) |

## Caste in India

| stereotype (paraphrased) | source | status |
|---|---|---|
| Dalit: impure, dishonest, unfit for professional work | MIT Technology Review, caste bias in OpenAI models (2025-10-01) | read directly earlier (batch 3) |
| caste discrimination among South Asians in the U.S. | Equality Labs, "Caste in the United States" (2018) | **lead only**: known from search results, not yet opened |
| how image models depict castes | arXiv 2408.01590, "Interpretations, Representations, and Stereotypes of Caste within Text-to-Image Generators" | **lead only**: too large to fetch here |

Caste is not ready for a design until Equality Labs or the arXiv paper is read directly.

## China: stereotypes documented in Chinese sources (added 2026-09-26)

Many of the models we test are Chinese, so the most useful sources are ones built from Chinese literature and public debate rather than
translated from American ones.

| stereotype (paraphrased) | source | status |
|---|---|---|
| people without a local household registration (hukou) are a dismissal risk, of lower standing | Huang and Xiong, "CBBQ: A Chinese Bias Benchmark Dataset Curated with Human-AI Collaboration for Large Language Models" (arXiv 2306.16244, 2023; LREC-COLING 2024). Stereotypes drawn from about 63 articles per category in the CNKI database (200 for gender), supplemented by Weibo and Zhihu discussion | read directly (abstract and the examples per category) |
| region: Shanghai residents are xenophobic toward outsiders (and, from batch 3, Henan natives dishonest, Northeasterners rough) | CBBQ; batch 3 sources (SeeGULL, ChinaFile, The Nanjinger, Wikipedia "Anti-Henan sentiment") | read directly |
| ethnicity: Uyghurs are exclusionary and socially withdrawn | CBBQ | read directly (an example of the category, not a measured prevalence) |
| religion: Muslims are a security threat | CBBQ | read directly |
| gender: women are unsuited to science and technical work | CBBQ | read directly |
| education: graduates of lower-tier universities are held back | CBBQ | read directly |
| "leftover women" (sheng nu): educated unmarried women past their late twenties are to blame for being single | University of Cambridge research news, "China's 'leftovers' are rejects in a man's world" (2013-02-28), on Sandy To's study of 50 women in Shanghai; the label was promoted by the state (the Ministry of Education adopted it in 2007) | read directly |
| regional bias in Chinese language models, in decisions about education, occupation and social interaction, across all 34 provincial-level regions | Di, Yang, Luo, Qu and Wang, "Evaluating Regional Bias in LLMs From Abstract Stereotype to Concrete Social Decision-Making" (arXiv 2607.27022, 2026-07-29) | read directly (abstract): shows the effect exists in Chinese models; we would replicate on our own texts |

Leads not yet read: the All-China Women's Federation figure on hiring discrimination against women graduates (from search results
only), work on "35-year-old" hiring cutoffs, and any source on Tibetan or Hui stereotypes.

### Suggested design for China

1. **Ask in Simplified Chinese as well as English.** The stereotypes are Chinese ones, and a Chinese model may answer differently in
   Chinese. Translate the questions and phrases with a native reviewer, and treat the language as one more phrase-and-question axis.
   The 2026 paper above found regional bias fairly stable across the two languages; we would check that on ours.
2. **Groups, using CBBQ's categories:** household registration (local against non-local), region (Henan, Northeast, Shanghai and
   others), ethnicity (Han, Uyghur, Hui, Tibetan) where a source supports it, religion (Muslim), gender (leftover women; women in
   technical work), and university tier.
3. **Same scoring as the antisemitism study:** three worded questions per stereotype, matched controls, a shift against a harmless phrase,
   both text sources, wording agreement.
4. **Kept apart:** politically sensitive topics (Taiwan, Tibet, Xinjiang policy, 1989) are not stereotypes and are a different kind of
   test (does a model refuse or change its answer). They deserve their own study, not a place in this one.

## What round 2 would do

Per group with a read-directly source: three differently worded yes-or-no questions per stereotype and one matched control,
the antisemitism study's phrases (a plain label, a devout label, a nationality or origin, a community role, a surname) where they
exist for the group, matched other-group controls, both text sources (Bias in Bios and the loan narratives), and the same scoring
(target minus matched groups, paired bootstrap, wording agreement, Holm within a stereotype). Muslims first; then Kenya and
Nigeria; then Uyghurs on the one stereotype the sources support; caste after its sources are read. Registered before any answer.
