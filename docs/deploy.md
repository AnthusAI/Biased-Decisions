# Deploying the leaderboard

The leaderboard is a static site built by AWS Amplify Hosting from this repository. Amplify is
connected to `AnthusAI/Biased-Decisions` on GitHub and builds `main` on every push; there is no
deploy script, no GitHub Actions role and no manual upload. A build that fails any spec publishes
nothing, and the previous deploy stays live.

## What a build does

`amplify.yml` (repository root) is the build spec. Amplify uses it in place of any build settings
typed into the console.

1. **preBuild**: fetch the tags (the colophon's release version and date come from the latest
   one), create a virtualenv with Python 3.11 or newer (`python3.12`, else `python3.11`, else
   `dnf install python3.11` on the Amazon Linux 2023 image, whose default `python3` may be older
   than the 3.10 the harness needs), `pip install -e '.[dev]'`, Node 22 through `nvm`, and
   `npm ci` in `site/`.
2. **build**: `scripts/site-build.sh`, which is also `make ci` locally:
   the unit specs (`pytest biased_decisions`); `bd replay`, which must reproduce the committed
   `studies/` byte for byte (`git diff --exit-code`); `bd report --json` for
   `site/data/leaderboard.json`; `astro build` into `site/dist/`; the build specs in
   `site/test/` (every page has a card of the right size, alt text matches the page, the
   colophon names the release, every internal link resolves).
3. **artifacts**: `site/dist/`.

`SITE_URL` defaults to `https://biased-decisions.anth.us`, which every canonical, `og:url` and
`og:image` URL names. Set it as an Amplify environment variable only to build for another origin.

## Connecting the app (console)

The app `Biased-Decisions` already exists in `us-east-1`, connected to the repository, with `main`
as its production branch. Check these settings:

| Setting | Value |
|---|---|
| App type | Web (static hosting), not SSR / Web Compute |
| Monorepo | **No**. Leave "My app is a monorepo" unchecked; the app root is the repository root |
| Branch | `main`, auto-build on |
| Build settings | the repository's `amplify.yml` takes precedence over the console's build spec; the placeholder spec the console generated can be left or cleared |
| Build image | Amazon Linux 2023 (the default). No custom image needed |
| Environment variables | none required. Optional: `SITE_URL` |
| Rewrites and redirects | paste `deploy/amplify-rules.json` into **Hosting > Rewrites and redirects > Manage > JSON editor**, replacing the default SPA rule (`/<*>` -> `/index.html` 404-200), which would serve the home page for every mistyped address |
| Custom headers | read from `customHttp.yml` in the repository root; leave the console's header editor empty |

From the command line (same effect; needs credentials allowed to update the app):

```
aws amplify update-app --region us-east-1 --app-id <app-id> \
  --custom-rules file://deploy/amplify-rules.json
```

## Addresses, redirects and caching

- Every page is a directory with an `index.html` (`/stereotype-religion/jewish/greed/`); Amplify
  serves it at the trailing-slash path and redirects the slashless form to it.
- `deploy/amplify-rules.json`, top to bottom: `dimension.html?d=<d>` -> `/<d>/` and
  `engine.html?e=<e>` -> `/engines/<e>/` (Amplify matches a query-string placeholder in the
  source), `methods.html` -> `/methods/`, `index.html` -> `/`, all 301; then every unknown path
  gets `/404.html` with a 404 status. The first build's `dimension.html` and `engine.html` also
  exist as small static pages that redirect in the browser, for any host without these rules.
- `customHttp.yml`: pages, the data file and everything else `Cache-Control: public, max-age=0,
  must-revalidate`, so a new build shows at once; `/_astro/*` bundles and `/og/**` cards, whose
  names are fingerprinted by content, `public, max-age=31536000, immutable`. Plus `nosniff`, a
  referrer policy and `SAMEORIGIN` framing.
- After the first deploy, confirm the header precedence with
  `curl -sI https://biased-decisions.anth.us/og/<a card>.png | grep -i cache-control` (it should
  say `immutable`) and `curl -sI https://biased-decisions.anth.us/ | grep -i cache-control`.

## The custom domain

`anth.us` is a Route 53 hosted zone in the same account, so Amplify can create the DNS records and
the ACM certificate itself. The apex `anth.us` is already associated with the site's own Amplify
app (with `www`), and a domain can belong to only one app, so this app associates the full
subdomain `biased-decisions.anth.us` as its own domain, with an empty prefix mapped to `main`.

Console: **Hosting > Custom domains > Add domain**, type `biased-decisions.anth.us`, map the root
(no prefix) to `main`, leave "set up redirect from https://biased-decisions.anth.us to www" off,
and keep the Amplify-managed certificate. Or:

```
aws amplify create-domain-association --region us-east-1 --app-id <app-id> \
  --domain-name biased-decisions.anth.us --sub-domain-settings prefix=,branchName=main
aws amplify get-domain-association --region us-east-1 --app-id <app-id> \
  --domain-name biased-decisions.anth.us \
  --query 'domainAssociation.{status:domainStatus,reason:statusReason,sub:subDomains}'
```

Status moves from `CREATING` through `PENDING_VERIFICATION` and `PENDING_DEPLOYMENT` to
`AVAILABLE`, usually within an hour. Amplify adds only the certificate-validation CNAME and the
`biased-decisions` record; no other record in the zone changes.

## Local preview

```
make site      # build site/dist/ and run the build specs
make serve     # http://127.0.0.1:4323/ with the Amplify rules and headers (site/scripts/serve.mjs)
make dev       # http://127.0.0.1:4321/ live-reloading source
make ci        # the whole Amplify build: specs, replay check, data, site, build specs
```

## Releases

Semantic Release (`.github/workflows/release.yml`) tags `main` and pushes a
`chore(release): x.y.z` commit; Amplify builds that commit too, and its colophon and cards then
name the new version and date. The build that runs for the merge itself, before the tag exists,
shows the previous release (or "unreleased").
