# Deploying the leaderboard

AWS Amplify Hosting serves the static production artifact. It does not connect to GitHub, install
dependencies, generate leaderboard data, replay studies, or run tests. GitHub Actions performs
those source and site checks, builds `site/dist`, and uploads that exact artifact to Amplify only
after a successful `main` run.

## Contributor workflow

`site/data/leaderboard.json` is a committed release input. When changing an answer, study, or
other input to the leaderboard data:

```sh
# Commit the record change first, so the data provenance names its record commit.
make refresh-site-data
git add site/data/leaderboard.json
git commit -m "chore(site): refresh leaderboard data"
make verify-publish
```

`make refresh-site-data` verifies that `bd replay` leaves `studies/` unchanged, then runs
`bd report --json`. `make verify-publish` repeats the local record check, regenerates the JSON,
requires it to match the committed file, and builds/tests the site. Neither command is part of
GitHub Actions or Amplify.

`make ci` mirrors the non-data GitHub checks: Python unit tests plus the Astro build and site
tests. It intentionally never calls `bd replay` or `bd report`.

## GitHub Actions

`.github/workflows/site.yml` runs on pull requests, `main` pushes, and manual dispatches.

1. The verification job installs Python 3.11 and Node 22.12, runs the Python unit tests, builds
   and tests the Astro site, and caches pip and npm package stores. The npm cache is keyed by
   `site/package-lock.json`; `node_modules`, Astro output, and prior deployment artifacts are not
   cached.
2. For `main` only, the tested `site/dist` directory is passed to the deployment job as a
   one-day GitHub Actions artifact.
3. The deployment job assumes the AWS role through GitHub OIDC, packages the artifact contents
   at the ZIP root, calls Amplify's manual deployment API, and waits for the resulting job to
   succeed. The job is serialized as `amplify-production`; a newer main deployment cancels an
   older pending one.

The deployment job has no AWS access on pull requests. It uses the GitHub `production`
Environment, which must be restricted to the `main` branch.

## One-time AWS and GitHub setup

Perform this setup with an AWS administrator. It deliberately is not automated by this
repository because it changes account-level hosting, IAM, and DNS state.

1. In `us-east-1`, create a **new static manual-deployment Amplify app** and production branch.
   Do not connect it to a Git provider. Copy the existing app's custom headers from
   `customHttp.yml` and redirect rules from `deploy/amplify-rules.json`, for example:

   ```sh
   aws amplify update-app --region us-east-1 --app-id <new-app-id> \
     --custom-rules file://deploy/amplify-rules.json \
     --custom-headers file://customHttp.yml
   ```
2. Create or reuse the GitHub Actions OIDC provider, then create a deployment role whose trust
   policy allows only `repo:AnthusAI/Biased-Decisions:environment:production` with audience
   `sts.amazonaws.com`. Its permissions allow only `amplify:CreateDeployment`,
   `amplify:StartDeployment`, and `amplify:GetJob` for the new app's production branch. The
   pre-signed upload URL returned by Amplify needs no extra S3 permission.
3. Create the GitHub `production` Environment, restrict deployments to `main`, and set these
   Environment variables: `AWS_DEPLOY_ROLE_ARN`, `AWS_REGION`, `AMPLIFY_APP_ID`, and
   `AMPLIFY_BRANCH`. None is an AWS access key.
4. Dispatch the Site CI and deployment workflow from `main`; test the new app's default Amplify
   URL before touching the custom domain. Confirm a representative page, redirect, 404, and the
   immutable cache headers for `/_astro/*` and `/og/*`.
5. Move `biased-decisions.anth.us` to the new app, repeat those smoke checks at the production
   URL, then disable automatic builds on the old Git-connected app. Keep the old app temporarily
   for rollback and remove it only after the new production deployment is stable.

The manual-deployment API is specifically for Amplify apps not connected to a Git repository.
See [CreateDeployment](https://docs.aws.amazon.com/amplify/latest/APIReference/API_CreateDeployment.html)
and [GitHub's AWS OIDC guidance](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws).

## Local preview

```sh
make site    # build site/dist/ and run its specs
make serve   # http://127.0.0.1:4323/ with production redirects and headers
make dev     # http://127.0.0.1:4321/ with live reload
```
