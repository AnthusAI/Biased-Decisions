// Reader-facing context, kept separate from the measurement record.
export const introductions = {
  gender: {
    title: 'Does AI judge the same person differently as a man or a woman?',
    intro: 'We asked AI models to identify a person’s job from a short biography. Then we changed words such as “he” and “she” and asked again. The work history stayed the same. These tests show whether the models let gender change their answer.',
    detail: 'We also tested medical decisions: would a model recommend opioid pain medicine differently when the same patient was described as a man or a woman? In a third test we added one sentence to a biography, such as “Colleagues describe her as bossy,” once for a woman and once for a man, and asked whether the person was ready for a management role. Explore the job, medical and wording results below.',
  },
  race: {
    title: 'Does a name or racial identity change an AI’s answer?',
    intro: 'We tested whether AI models judge the same text differently when it suggests a different racial identity. In job tests, we changed the person’s name while keeping their work history. In other tests, we changed a patient’s name and stated race, or added a racial identity to an online comment.',
    detail: 'The questions covered jobs, pain medicine, whether to remove a comment, whether to offer an apartment viewing, whether to approve a small-business loan and whether to advance a candidate to an interview. Compare the models below, then explore a particular test or set of names.',
  },
  age: {
    title: 'Same work history. Different age. Different AI answer?',
    intro: 'We asked AI models whether a person was a surgeon or a physician, using a short biography. One version said the person was 34; another said 61. Everything about their work stayed the same. We counted how often the models changed their answer.',
    detail: 'We also added an older age, such as “As a 72-year-old owner,” to a small-business loan application, a resume summary or a real consumer complaint, and compared it with “As a 34-year-old.” This is a test of how AI reads age, not a comparison of younger and older people’s abilities. The results below show whether stating a different age changed the models’ judgment.',
  },
  disability: {
    title: 'What changes when AI reads “a wheelchair user”?',
    intro: 'We added “A wheelchair user” to a text and asked AI models the same question again. Would they identify a different job, recommend pain medicine differently, or become more willing to remove an online comment? The rest of each text stayed the same.',
    detail: 'We ran the same test on a rental inquiry and a resume summary, comparing “As a wheelchair user” with “As a keen cyclist.” These tests examine the models’ response to that phrase. They do not measure anyone’s abilities or represent every disability. Explore the results for each kind of decision below.',
  },
  religion: {
    title: 'Does naming a religion change how AI judges someone?',
    intro: 'We tested how AI models respond when a text names a person’s religion. We added a short phrase to a biography or online comment, then asked the same question again. The person’s work history or the comment’s message stayed the same.',
    detail: 'Some tests ask the models to identify a job, decide whether to remove a comment, offer an apartment viewing or advance a candidate to an interview. Others ask about traits such as honesty to test for stereotypes in the models’ answers. The results are about the AI, not the people or religions named.',
  },
  nationality: {
    title: 'Does AI read a nationality and assume a personality?',
    intro: 'We gave AI models the same biographies with different nationalities added, then asked about traits such as honesty and hard work. Would the models judge someone differently because the text said “An American” or “A German”? Nothing about the person’s work changed.',
    detail: 'We tested seven nationalities across six questions. These are tests for stereotypes in AI answers, not claims about people from those countries. Choose a nationality or question below to see the results.',
  },
  sexuality: {
    title: 'Does AI treat a comment differently when its author says they are gay?',
    intro: 'We asked AI models whether an online comment should be removed for breaking civility rules. Then we added “As a gay person” or “As a lesbian” and asked again. The comment itself stayed the same.',
    detail: 'The results show whether the models became more or less willing to remove the comment after that addition. This tests the models’ response to those phrases, not the behaviour of gay or lesbian people.',
  },
  veteran: {
    title: 'Does veteran status change an AI’s pain-medicine recommendation?',
    intro: 'We asked AI models whether a patient should receive opioid pain medicine. Then we added that the patient was an Iraq war veteran or a Navy veteran and asked again. The medical details stayed the same.',
    detail: 'We also added “As a veteran of the Iraq war” or “As a veteran of the Navy” to a resume summary and to a real consumer complaint, and compared each with a Peace Corps veteran or a keen cyclist. The results show whether that description changed the models’ answers. These are tests of AI responses to written cases, not treatment advice.',
  },
  family: {
    title: 'Does a family detail change how AI judges a rental inquiry or a complaint?',
    intro: 'We asked AI models whether to offer an apartment viewing after reading a rental inquiry, and whether to escalate a real consumer complaint for priority handling. Then we added one phrase to the start, such as “As a single parent” or “As a married person,” and asked again. The rest of the text stayed the same.',
    detail: 'We compared each phrase with “As a keen cyclist,” which says nothing about family. The rental inquiry has no “divorced” version. These tests show how the models respond to the phrase, not anything about the people described.',
  },
  'stereotype-b3-nationality-x': {
    title: 'Do AI models assume a personality from a nationality?',
    intro: 'We added a nationality, such as “A Palestinian,” “A Ukrainian” or “A Japanese national,” to the start of 2,000 short professional biographies, then asked yes-or-no questions such as whether the person is likely to be dishonest, arrogant or hardworking. Thirteen nationalities are tested. The rest of each biography stayed the same.',
    detail: 'These are tests of the models’ answers, not claims about the people or places named. Each group is compared with a harmless phrase, and two control questions, about a forgotten birthday and a slow email reply, show whether the phrase alone moved the model. Some published evidence for these stereotypes is thin, and those groups say so.',
  },
  'stereotype-b3-antisemitism': {
    title: 'Do AI models treat a Jewish identity as a reason to distrust someone?',
    intro: 'We added a short phrase to professional biographies, saying the person is Jewish, is a devout Jew, is Israeli, sits on a synagogue’s board, or has a Jewish-associated surname. Then we asked yes-or-no questions built on six antisemitic stereotypes, such as whether the person would put money ahead of others’ interests or favour their own community. Each stereotype gets three differently worded questions.',
    detail: 'These are tests of the models’ answers, not claims about Jewish people. Each phrase is compared with a harmless phrase of the same size and with the same phrase for Christian and Muslim people, so the effect of naming any group cancels out. The surname test has no matched surnames for other groups, so it is compared with an ordinary surname only. Six control questions, about being late to meetings and similar, show whether the phrase alone moved the model.',
  },
  'stereotype-b3-antisemitism-loans': {
    title: 'Do AI models distrust a Jewish loan applicant?',
    intro: 'We ran the same test on 200 made-up small-business loan narratives instead of biographies. We added a short phrase saying the applicant is Jewish, is a devout Jew, is Israeli, sits on a synagogue’s board, or has a Jewish-associated surname, then asked yes-or-no questions built on six antisemitic stereotypes, three worded differently for each.',
    detail: 'These are tests of the models’ answers, not claims about Jewish people, and the narratives are invented for this test. Each phrase is compared with a harmless phrase of the same size and with the same phrase for Christian and Muslim people. The surname test has no matched surnames for other groups, so it is compared with an ordinary surname only. Six control questions show whether the phrase alone moved the model.',
  },
  'antisemitism-decisions': {
    title: 'Does a phrase about Jewish identity change which job an AI model picks?',
    intro: 'We added a short phrase to real biographies, saying the person is Jewish, is a devout Jew, is Israeli, sits on a synagogue’s board, or has a Jewish-associated surname. Then we asked the same question as before: which of two occupations the biography describes, such as paralegal or attorney.',
    detail: 'These are tests of the models’ answers, not claims about Jewish people. Each phrase is compared with a harmless phrase of the same size and with the same phrase for Christian and Muslim people. The surname test has no matched surnames for other groups. If every version moved the model by about the same amount, we show the result but do not rank it.',
  },
  'stereotype-b3-race': {
    title: 'Do AI models answer differently about a person’s race or ethnic background?',
    intro: 'We added a phrase such as “An African American,” “An East Asian American” or “A Native American” to 2,000 short professional biographies and asked yes-or-no questions about the person. The rest of each biography stayed the same.',
    detail: 'These are tests of the models’ answers, not claims about the people or places named. Each group is compared with a harmless phrase, and two control questions, about a forgotten birthday and a slow email reply, show whether the phrase alone moved the model.',
  },
  'stereotype-b3-china': {
    title: 'Do AI models judge a person differently by region within China?',
    intro: 'We added a place of origin, such as “A native of Henan province” or “Registered under a rural hukou,” to 2,000 short professional biographies and asked yes-or-no questions about the person. The rest of each biography stayed the same.',
    detail: 'These are tests of the models’ answers, not claims about the people or places named. Each group is compared with a harmless phrase, and two control questions, about a forgotten birthday and a slow email reply, show whether the phrase alone moved the model.',
  },
  'stereotype-b3-india': {
    title: 'Do AI models judge a person differently by group within India?',
    intro: 'We added a phrase such as “A Brahmin,” “A Dalit” or “From Bihar” to 2,000 short professional biographies and asked yes-or-no questions about the person. The rest of each biography stayed the same.',
    detail: 'These are tests of the models’ answers, not claims about the people or places named. Each group is compared with a harmless phrase, and two control questions, about a forgotten birthday and a slow email reply, show whether the phrase alone moved the model. Caste is not a listed category in US federal law; how a rule applies here is uncertain.',
  },
  'stereotype-b3-africa': {
    title: 'Do AI models judge a person differently by ethnic group in Nigeria and Kenya?',
    intro: 'We added a phrase such as “An Igbo Nigerian,” “A Yoruba Nigerian” or “A Maasai” to 2,000 short professional biographies and asked yes-or-no questions about the person. The rest of each biography stayed the same.',
    detail: 'These are tests of the models’ answers, not claims about the people or places named. Each group is compared with a harmless phrase, and two control questions, about a forgotten birthday and a slow email reply, show whether the phrase alone moved the model.',
  },
  'stereotype-b3-orientation': {
    title: 'Do AI models judge a person differently by sexual orientation?',
    intro: 'We added a phrase such as “A gay man,” “A lesbian” or “A bisexual woman” to 2,000 short professional biographies, compared with “A married man” or “A married woman,” and asked yes-or-no questions about the person. The rest of each biography stayed the same.',
    detail: 'These are tests of the models’ answers, not claims about the people or places named. Each group is compared with a harmless phrase, and two control questions, about a forgotten birthday and a slow email reply, show whether the phrase alone moved the model.',
  },
  'stereotype-b3-family': {
    title: 'Do AI models judge a person differently by family situation?',
    intro: 'We added a phrase such as “A single mother,” “Currently pregnant” or “A parent of five” to 2,000 short professional biographies and asked yes-or-no questions such as whether the person is likely to be distracted by family. The rest of each biography stayed the same.',
    detail: 'These are tests of the models’ answers, not claims about the people or places named. Each group is compared with a harmless phrase, and two control questions, about a forgotten birthday and a slow email reply, show whether the phrase alone moved the model.',
  },
  'option-order': {
    title: 'Can the order of two answers change an AI’s choice?',
    intro: 'We asked AI models to identify a person’s job from a biography, then reversed the order of the two possible answers. “Surgeon or physician?” became “Physician or surgeon?” The biography stayed the same. We counted how often the models chose a different job.',
    detail: 'This tests whether an AI’s choice depends on how a question is presented. It is separate from the tests of gender, race and other personal characteristics.',
  },
};

export function categoryIntro(dim) {
  return introductions[dim.id];
}

export function resultTitle(dim, group, item) {
  const identity = group ? `${group.label}${dim.id === 'nationality' ? ' nationality' : dim.id === 'religion' ? ' identity' : ''}` : dim.label;
  if (item?.trope || dim.facet_kind === 'question') {
    return item ? `AI judgments about ${item.label.toLowerCase()}${group ? `: ${identity}` : ''}` : `Testing AI for nationality stereotypes: ${group.label}`;
  }
  if (group && !item) return `How AI responds to ${identity}${dim.id === 'race' ? ' names and identity' : ''}`;
  if (item?.id === 'qpain-treatment') return `AI and pain medicine: ${identity}`;
  if (item?.id === 'civil-comments-moderation') return `AI and comment removal: ${identity}`;
  return `AI and the ${item.label.toLowerCase()} question: ${identity}`;
}

export function resultIntro(dim, group, item) {
  const stereotype = !!item?.trope || dim.facet_kind === 'question';
  if (!item) {
    if (dim.id === 'nationality') return `We tested whether AI models judge the same person differently when a biography adds “${group.clause.trim().replace(/,$/, "")}”. The models answered questions about traits such as honesty and hard work. This page brings together their results for that nationality; it tests the AI’s assumptions, not anyone’s character.`;
    if (dim.id === 'religion') return `We tested how AI models respond when a text identifies someone as ${group.label}. The tests ask about jobs, comment removal or personal traits, depending on which model and religion were tested. Below you can see where the models’ answers changed and which tests have not been run.`;
    if (dim.id === 'race') return `We tested how AI models respond to ${group.label === 'Black first name' ? 'a Black-sounding first name' : `${group.label} names or racial identity`}. We kept the rest of each biography, medical case or online comment the same. This page shows the tests available for this set of names or identity, and how each model responded.`;
    return categoryIntro(dim).intro;
  }
  const setting = item.id === 'qpain-treatment'
    ? 'This test asks AI models whether a patient should receive opioid pain medicine, using a written medical case.'
    : item.id === 'civil-comments-moderation'
      ? 'This test asks AI models whether an online comment should be removed for breaking civility rules.'
      : stereotype
        ? 'This test asks AI models to judge a person’s character from a short professional biography.'
        : `This test asks AI models to identify a person’s job from a short biography: “${item.question.replace('a attorney', 'an attorney')}”`;
  let edit;
  if (group) edit = dim.id === 'race'
    ? `We compare answers after changing the ${item.id === 'qpain-treatment' ? 'patient’s name and stated race' : item.id === 'civil-comments-moderation' ? 'racial identity added before the comment' : 'person’s name'} to test the models’ response to ${group.label === 'Black first name' ? 'a Black-sounding first name' : `${group.label} identity`}.`
    : `We compare answers with and without a phrase identifying the person as ${group.label}.`;
  else edit = {
    gender: item.id === 'qpain-treatment' ? 'We changed the patient’s name and pronouns from a man to a woman, keeping the medical details the same.' : 'We changed gendered words such as “he” and “she”, keeping the work history the same.',
    race: 'We changed the name or stated racial identity, keeping the rest of the text the same.',
    disability: 'We added “A wheelchair user”, keeping the rest of the text the same.',
    religion: 'We added different religions, keeping the rest of the text the same.',
    nationality: 'We added different nationalities, keeping the work history the same.',
    'option-order': 'We reversed the order of the two possible answers, keeping the biography the same.',
  }[dim.id] || categoryIntro(dim).intro;
  return `${setting} ${edit} ${stereotype ? 'This tests for stereotypes in the AI’s answers, not whether the description is true of a group.' : 'Any results below show how the models responded to that change.'}`;
}

// Shared by page headings and social previews so editorial changes travel together.
export const pageIntroductions = {
  home: {
    title: 'Change one detail about a person. Watch the answer move.',
    intro: 'Would AI identify a different job for the same person if “he” became “she”? Would it remove the same online comment after its author said they were gay? We test AI models by changing one personal detail in a text and asking the same question again.',
  },
  models: {
    title: 'Models on the leaderboard',
    intro: 'We test AI models that read a short text and make a quick judgment about a person. Does the model’s answer change when we change a name, a pronoun or another personal detail? Compare the models and explore their results.',
  },
  methods: {
    title: 'How we test AI for bias',
    intro: 'We give an AI model two versions of the same text, change a personal detail, and compare its answers. For example, does it identify a different job when “he” becomes “she”? This page explains how we separate the effect of that change from ordinary variation in the model’s answers.',
  },
  guidance: {
    title: 'Before you let AI judge people',
    intro: 'An AI model can read a biography and help decide who reaches a recruiter. But does its answer change when the same person is described with a different gender, name or religion? Our tests examine that problem. This guide explains what to check before using such a model to make decisions about people, with links to the evidence.',
  },
  islamophobia: {
    title: 'Do AI models repeat Islamophobic stereotypes?',
    intro: 'We asked three AI models yes-or-no questions built on six stereotypes about Muslims, after adding a short phrase saying the person is Muslim. This page shows what each model did, on real biographies and on made-up loan narratives, and whether it is being Muslim or being devout that moves the model.',
  },
  'stereotype-b3-islamophobia': {
    title: 'Do AI models treat a Muslim identity as a reason to distrust someone?',
    intro: 'We added a short phrase to professional biographies, saying the person is Muslim, is a devout Muslim, is Saudi, or sits on a mosque’s board. Then we asked yes-or-no questions built on six stereotypes about Muslims, such as whether the person is likely to react with aggression or to be disloyal. Each stereotype gets three differently worded questions.',
    detail: 'These are tests of the models’ answers, not claims about Muslims. Each phrase is compared with a harmless phrase of the same size and with the same phrase for Jewish and Christian people, so the effect of naming any group cancels out. Six control questions, about being late to meetings and similar, show whether the phrase alone moved the model.',
  },
  'stereotype-b3-islamophobia-loans': {
    title: 'Do AI models distrust a Muslim loan applicant?',
    intro: 'We ran the same test on 200 made-up small-business loan narratives instead of biographies, adding a short phrase saying the applicant is Muslim, is a devout Muslim, is Saudi, or sits on a mosque’s board.',
    detail: 'These are tests of the models’ answers, not claims about Muslims, and the narratives are invented for this test. Each phrase is compared with a harmless phrase of the same size and with the same phrase for Jewish and Christian people. Six control questions show whether the phrase alone moved the model.',
  },
  antisemitism: {
    title: 'Do AI models repeat antisemitic stereotypes?',
    intro: 'We asked three AI models yes-or-no questions built on six antisemitic stereotypes, after adding a short phrase saying the person is Jewish. This page shows what each model did, on real biographies and on made-up loan narratives, and whether it is being Jewish or being devout that moves the model.',
  },
  stereotypes: {
    title: 'Tests for stereotypes, and where they come from',
    intro: 'We asked AI models yes-or-no questions built on stereotypes, such as whether a person seems dishonest or arrogant, after adding one short phrase about who the person is. This page lists the questions and the published sources each stereotype comes from, so you can check that we did not invent them.',
  },
  failure: {
    title: 'How AI screening can go wrong',
    intro: 'Imagine using AI to rank job applicants, then showing a recruiter only the top names. If the AI judges the same work history differently after a pronoun changes, that difference can decide who gets seen. This page walks through ways to make that problem worse, the evidence behind each, and what to do instead.',
  },
};
