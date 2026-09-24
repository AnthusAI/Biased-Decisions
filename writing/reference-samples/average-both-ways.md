# One fix, and what it costs

One way to reduce the effect of a pronoun is to ask twice. Make a second copy of each text with only
the gendered words swapped: she becomes he, her becomes his. Ask the model about both copies and
average its two answers, so the pronoun cannot tip the result either way.

In our shortlist test this moved women's share of the shortlist much closer to men's, for both models
we tried it on. It also made the models match the dataset's own job labels a little less often,
because in this data the pronoun carries some real information about the job, and we took it out.

It is not a guarantee. For nurse and physician biographies the averaged ranking went too far and
favoured women. Check the shortlist again after any fix.
