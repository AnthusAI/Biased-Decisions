// Where the stereotypes we tested come from. Only what our own checking established (2026-09-23,
// with four sources read again on 2026-09-25); see docs/batch3-preregistration.md and
// docs/antisemitic-tropes-preregistration.md. "read" = we read the page ourselves; "confirmed" =
// we confirmed it exists and is about this topic but could not read the wording; "weak" = real,
// but it supports the claim less strongly than we first thought.
export const CHECKED = {
  read: "We read it ourselves",
  confirmed: "Confirmed to exist and be on topic; we could not read the wording",
  weak: "Real, but supports the claim only weakly",
};

export const SOURCES = [
  { group: "Jewish people", title: "Antisemitism Uncovered: A Guide to Old Myths in a New Era", by: "Anti-Defamation League", url: "https://antisemitism.adl.org/", checked: "read" },
  { group: "Jewish people", title: "Translate Hate glossary", by: "American Jewish Committee", url: "https://www.ajc.org/translatehateglossary", checked: "confirmed" },
  { group: "Nationalities", title: "SeeGULL: stereotypes about 178 countries", by: "Google Research", url: "https://github.com/google-research-datasets/seegull", checked: "read" },
  { group: "Nationalities", title: "SeeGULL paper", by: "Google Research", url: "https://arxiv.org/abs/2305.11840", checked: "read" },
  { group: "Racial and ethnic groups in the U.S.", title: "Asian Americans and the “forever foreigner” stereotype", by: "Pew Research Center", url: "https://www.pewresearch.org/race-and-ethnicity/2023/11/30/asian-americans-and-the-forever-foreigner-stereotype/", checked: "read" },
  { group: "Racial and ethnic groups in the U.S.", title: "Asian Americans and the “model minority” stereotype", by: "Pew Research Center", url: "https://www.pewresearch.org/race-and-ethnicity/2023/11/30/asian-americans-and-the-model-minority-stereotype/", checked: "read" },
  { group: "Racial and ethnic groups in the U.S.", title: "What is the model minority myth?", by: "Learning for Justice", url: "https://www.learningforjustice.org/magazine/what-is-the-model-minority-myth", checked: "read" },
  { group: "Racial and ethnic groups in the U.S.", title: "Corporate Challenges for Asian American Leaders (“Beyond the Bamboo Ceiling”)", by: "CKGSB Knowledge", url: "https://english.ckgsb.edu.cn/knowledge/article/corporate-leadership-for-asian-american-barriers/", checked: "read" },
  { group: "Racial and ethnic groups in the U.S.", title: "Stereotypes of African Americans", by: "Wikipedia (a secondary source)", url: "https://en.wikipedia.org/wiki/Stereotypes_of_African_Americans", checked: "read" },
  { group: "Racial and ethnic groups in the U.S.", title: "Stereotypes of Hispanic and Latino Americans in the United States", by: "Wikipedia (a secondary source)", url: "https://en.wikipedia.org/wiki/Stereotypes_of_Hispanic_and_Latino_Americans_in_the_United_States", checked: "read" },
  { group: "Racial and ethnic groups in the U.S.", title: "Native American stereotypes, Leavitt, Covarrubias, Perez and Fryberg (2015), as summarized by Journalist’s Resource", by: "Journalist’s Resource", url: null, checked: "read" },
  { group: "China", title: "Anti-Henan sentiment", by: "Wikipedia (a secondary source)", url: "https://en.wikipedia.org/wiki/Anti-Henan_sentiment", checked: "read" },
  { group: "China", title: "Hukou", by: "Wikipedia (a secondary source)", url: "https://en.wikipedia.org/wiki/Hukou", checked: "read" },
  { group: "China", title: "A map of China’s regional stereotypes", by: "ChinaFile", url: "https://chinafile.com/reporting-opinion/media/map-china-stereotype", checked: "read" },
  { group: "China", title: "Speaking with sharp tongues: touring China’s stereotypes", by: "The Nanjinger", url: "https://www.thenanjinger.com/magazine/feature-stories/speaking-with-sharp-tongues-touring-chinas-stereotypes/", checked: "read" },
  { group: "India", title: "OpenAI’s models show caste bias (news report)", by: "MIT Technology Review", url: "https://www.technologyreview.com/2025/10/01/1124621/openai-india-caste-bias/", checked: "read" },
  { group: "India", title: "IndRegBias: regional bias in Indian comments", by: "research paper", url: "https://arxiv.org/abs/2601.06477", checked: "weak" },
  { group: "Africa", title: "AfriStereo: stereotypes about African ethnic groups", by: "research paper", url: "https://arxiv.org/abs/2511.22016", checked: "read" },
  { group: "Africa", title: "SAFARI: wealth-related stereotypes", by: "research paper", url: "https://arxiv.org/abs/2602.22404", checked: "read" },
  { group: "Sexual orientation", title: "WinoQueer: bias against LGBTQ+ people in language models", by: "research paper", url: "https://arxiv.org/abs/2306.15087", checked: "read" },
  { group: "Family", title: "Why do single parents still suffer stigma?", by: "University of Huddersfield", url: "https://www.hud.ac.uk/news/2019/december/single-parent-sigma/", checked: "read" },
  { group: "Family", title: "Workplace discrimination against pregnant and postpartum employees", by: "peer-reviewed review (PubMed Central)", url: "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12385767/", checked: "read" },
  { group: "Family", title: "Public views of marriage and cohabitation", by: "Pew Research Center", url: "https://www.pewresearch.org/social-trends/2019/11/06/public-views-of-marriage-and-cohabitation/", checked: "weak" },
];

export const DROPPED = [
  "Pages we could not read (NMAAHC, CAIR, Bridge Initiative, GLAAD, NPR, Facing History): not cited, and anything that rested only on them is out.",
  "UnidosUS (does not discuss the stereotypes it was cited for), the National Congress of American Indians (mascots only), a style guide on “inspiration” stories about disability (does not cover it), one 2025 paper (a different claim) and ILGA (weak): dropped.",
  "A Uyghur entry (its citation was the Henan article) and Hijra and transgender India entries (the cited dataset excludes them): dropped.",
  "Two rows for which we found no source at all (Latino financial responsibility; Native American violence): dropped.",
  "A group of disability questions: postponed, because its sources have not been read.",
];
