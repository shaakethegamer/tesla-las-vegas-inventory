# Las Vegas Tesla Model 3 Premium inventory watch

Checks Tesla's new Model 3 inventory around ZIP 89109 every 10 minutes using GitHub Actions. Only explicitly labeled Premium trims qualify. Standard/base, Performance, used and demo cars are excluded. First successful run establishes a baseline silently; subsequent newly appearing VINs send ntfy notifications.

## Setup

1. Change this repository to **Private** in GitHub Settings.
2. In Settings → Secrets and variables → Actions, create repository secret `NTFY_TOPIC` containing your ntfy topic name (the part after ntfy.sh/).
3. In Settings → Actions → General, ensure workflow permissions allow **Read and write permissions**.
4. Under Actions → Check Tesla Inventory, enable the workflow if requested and click **Run workflow** to establish a baseline.
5. Subscribe to the same topic in the Android ntfy app and allow its notifications.

**Important:** ntfy.sh public topics are not private or authenticated; use a long random topic name and avoid sharing it. Scheduled GitHub Actions may be delayed. Tesla's undocumented inventory endpoint can change or block automated requests. The monitor deliberately fails rather than silently reporting zero inventory when the response shape changes. The Tesla vehicle order link is constructed from the VIN and may not always resolve to an active listing. Premium trim labels and location availability depend on the inventory data Tesla returns.

VIN fingerprints are stored in `seen_vins.json` rather than publishing full VINs in Git. No alerts are sent if the job fails. Inspect Actions logs for failures. The monitor is not considered operational until the first run succeeds and an ntfy test has been received.
