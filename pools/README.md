# Name pools

Two files, both ported unchanged from Jev-Flywheel (`fixtures/bios/first_names.txt` and
`fixtures/bios/name_pools.json`), used by `biased_decisions.cues.redaction` (which first names
count as redactable) and `biased_decisions.cues.fullname`/`race-fullname` (which first and last
names to draw for the race-from-a-full-name study).

## `first_names.txt`

2,686 US first names given to at least 5,000 babies, 1970-2021, from the Social Security
Administration's public-domain baby-names data (Hugging Face mirror `jbrazzy/baby_names`). Used
only to decide whether a token spaCy tags as part of a `PERSON` span is a first name (see
`biased_decisions.cues.redaction.redact_names`); the file itself carries this note as a header
comment.

## `name_pools.json`

Four-group (white, black, hispanic, asian) first- and last-name pools for the `race-fullname`
cue, with the provenance, thresholds, and pool sizes recorded inside the file itself under its
own `provenance`, `thresholds`, and `pool_sizes` keys:

- **`race_probability`** -- Rosenman, Olivella & Imai (2023), *Scientific Data*,
  [doi:10.7910/DVN/SGKW0K](https://doi.org/10.7910/DVN/SGKW0K) (CC0). Name-to-race probability
  tables for first and last names.
- **`first_name_gender`** -- SSA baby-names counts, 1970-2021 (Hugging Face mirror
  `jbrazzy/baby_names`, public domain). Used to restrict first names to ones with a clear,
  stated gender.
- **`last_name_frequency`** -- US Census Bureau 2010 surname file (`Names_2010Census.csv`,
  public domain). Used to restrict surnames to ones common enough to read as ordinary.

**Thresholds** a name had to clear to enter a pool: `first_name_prob >= 0.8` and
`last_name_prob >= 0.8` (Rosenman et al.'s race-probability estimate for that name), a first
name given to at least `20,000` babies (`first_name_min_births`) with at least `90%` of those
births one gender (`first_name_min_gender_frac`), and a surname borne by at least `5,000`
people (`last_name_min_bearers`).

**Pool sizes**: white 190 female / 174 male first names, ~3,300 last names; black 10 female /
14 male first names, 53 last names; hispanic 11 female / 39 male first names, 267 last names;
asian 0 stated-gender first names (drawn from the white pool by construction, since Rosenman et
al. has no Asian first-name table with a stated gender split) / 139 last names. The file's own
`pool_sizes.deviations` notes two off-by-one counts against the pre-registered expected sizes
(`white.last` and `asian.last`, each short by 1 name), recorded rather than silently corrected.

All three sources are public domain or CC0; none requires attribution to redistribute, and none
is personal data (they are population-level name-frequency tables, not records about any named
individual).
