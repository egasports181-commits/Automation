# Free Reels Scheduler: GitHub Actions + Cloudflare R2 + Meta API

A no-paid-server starter for scheduling Instagram Reels and Facebook Page Reels.

## Architecture
- Videos and `schedule.csv` live in Cloudflare R2.
- GitHub Actions runs `automation/worker.py` every 5 minutes.
- `state.json` in R2 tracks successful platform publishes.
- Instagram uses a public video URL from your R2 custom domain.
- Facebook Reels uploads the video bytes to Meta.

## Zero-cost notes
This can stay within free tiers for low volume, but free quotas, taxes, and account eligibility can change. Cloudflare R2 currently lists 10 GB-month Standard storage, 1M Class A operations, 10M Class B operations and free egress. GitHub Actions usage depends on repo visibility and plan. Do not enable paid usage if your goal is strict $0.
GitHub cron is best-effort, not exact-to-the-second scheduling. Run interval is 5 minutes.

## Requirements
- Instagram Professional account (Business or Creator) eligible for API publishing.
- Facebook Page with publishing permissions.
- Meta Developer app and valid access token with required permissions.
- Cloudflare R2 bucket, S3 API token and public custom domain.
- GitHub account.

## 1. Meta setup
Create an app at https://developers.facebook.com/ and configure the appropriate Instagram and Facebook Page API products/use cases. Connect your Instagram Professional account and Facebook Page. Get:
- `META_ACCESS_TOKEN` (a token with the required permissions; use a suitable long-lived token)
- `INSTAGRAM_USER_ID`
- `FACEBOOK_PAGE_ID`
- `META_API_VERSION` (a currently supported Graph API version, e.g. `vXX.X` is a placeholder; replace it)

Permission requirements depend on the API login flow and app access level. Common permissions for Facebook Login-based Instagram publishing include `instagram_basic`, `instagram_content_publish`, `pages_show_list`, and `pages_read_engagement`; Facebook Page publishing may need Page/video permissions such as `pages_manage_posts`. Verify the exact current requirements in Meta's official docs and App Dashboard. Never paste tokens into code or commit them.

Official Meta references:
- Instagram API docs: https://developers.facebook.com/docs/instagram-platform/
- Meta Instagram API Postman collection: https://www.postman.com/meta/workspace/instagram/
- Facebook Reels publishing docs: https://developers.facebook.com/docs/video-api/guides/reels-publishing/

## 2. R2 setup
1. In Cloudflare Dashboard, open Storage & databases > R2 and create a Standard bucket.
2. Create an R2 API token with read/write access only to this bucket.
3. Configure a public custom domain for the bucket, e.g. `https://media.example.com`. Instagram must be able to fetch the full video URL without login.
4. Keep these values for GitHub secrets: account ID, access key ID, secret access key, bucket name, endpoint URL and public domain.

Do not put R2 keys or Meta tokens in the repository.

## 3. GitHub repository and secrets
Create a repository. A private repo is safer for your code. GitHub Free includes a monthly hosted-runner allowance for private repos; public standard runners are free but source code is public. Add these repository Actions secrets under Settings > Secrets and variables > Actions:
- `META_ACCESS_TOKEN`
- `META_API_VERSION`
- `INSTAGRAM_USER_ID`
- `FACEBOOK_PAGE_ID`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ENDPOINT_URL`
- `PUBLIC_VIDEO_BASE_URL`

`R2_ENDPOINT_URL` format: `https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com`
`PUBLIC_VIDEO_BASE_URL`: your public R2 custom domain, no trailing slash.

## 4. Upload videos
Use the Cloudflare R2 Dashboard to upload:
- `schedule.csv`
- each video named in that CSV
- `state.json` (optional; if absent, worker creates it)

Or from your PC:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:R2_ACCOUNT_ID="..."
$env:R2_ACCESS_KEY_ID="..."
$env:R2_SECRET_ACCESS_KEY="..."
$env:R2_BUCKET="..."
$env:R2_ENDPOINT_URL="https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com"
python upload_to_r2.py --folder "D:\ReelsToPost"
```
This PC-side upload is manual and does not need the PC to stay on after upload.

## 5. Schedule format
Upload `schedule.csv` to the root of the bucket. Required columns:
`filename,caption,scheduled_at,platforms`

Example:
```csv
filename,caption,scheduled_at,platforms
anime01.mp4,"Anime edit #anime #reels",2026-10-20T19:00:00+06:00,instagram;facebook
anime02.mp4,"New short #anime",2026-10-21T20:00:00+06:00,instagram
```
Use ISO time with `+06:00` for Bangladesh. `platforms` accepts `instagram`, `facebook`, or `instagram;facebook`. Filenames should be unique per scheduled post; don't overwrite an existing filename for a new video if its prior state must remain distinct.

## 6. Test and run
1. Add all Actions secrets.
2. Upload a small test video and a schedule row 10-15 minutes in the future.
3. In GitHub, open Actions > `Publish scheduled Reels` > Run workflow to test.
4. Check logs and confirm posts on both platforms.
5. Workflow also runs every 5 minutes automatically.

## Important reliability notes
- This is a starter, not a guarantee of production-grade exactly-once delivery. If Meta accepts a post but the worker loses network before writing state to R2, you must inspect the platform before retrying to avoid duplicates.
- Failed jobs are recorded in `state.json` and will not automatically retry by default. Fix the issue, inspect whether a post was created, then remove the platform's state entry for that job only if you intentionally want to retry.
- Use only videos/audio you own or are licensed to publish.
- Meta may require app review or business verification for some use cases. API versions, permissions, and free tiers can change.
