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

## What round 2 would do

Per group with a read-directly source: three differently worded yes-or-no questions per stereotype and one matched control,
the antisemitism study's phrases (a plain label, a devout label, a nationality or origin, a community role, a surname) where they
exist for the group, matched other-group controls, both text sources (Bias in Bios and the loan narratives), and the same scoring
(target minus matched groups, paired bootstrap, wording agreement, Holm within a stereotype). Muslims first; then Kenya and
Nigeria; then Uyghurs on the one stereotype the sources support; caste after its sources are read. Registered before any answer.
