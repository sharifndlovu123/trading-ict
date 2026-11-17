# Hunt prep prompts (for CronCreate; jobs are session-only and expire after 7 days)

Times are local (SAST = New York + 7 h in winter; re-check after a US clock change).
London prep: `35 7 * * 1-5` (fires about 08:05). New York prep: `15 14 * * 1-5` (fires about 14:45).
In the text below replace `<SESSION>` and `<OPEN>` (London: opens 02:00 New York = 09:00 SAST, watched for learning, not traded; New York: cash open 09:30 New York = 16:30 SAST).

---

HUNT PREP, <SESSION> session (<OPEN>). Work in /home/sharif/Documents/vs_code/personal/trading-ict. FIRST read the memory file hunting-playbook.md and follow it step by step (it is how Sharif taught me to think at the chart), and today's and the last session's research/hunt-log/<date>.md.

(1) Clean chart: archive the old out/live/overlay.json in research/hunt-log/, then overwrite it: empty marks for US100, US500, US30; gold and silver `watch: false` with a one-line read (for looking only); `hunt: {on: true, session, next}`; a new `at`.
(2) Make sure the live loop (`uv run python research/scripts/live_recipe.py --assets US100 US500 US30 XAUUSD XAGUSD`, background) and the 8776 server (`liqmap_server.py --host 0.0.0.0 --password-env LIVE_PAGE_PASSWORD --port 8776 --data out/live --page viewer/live.html --answers reports/reviews/live.jsonl`) are running; start what is missing.
(3) Read reports/reviews/live.jsonl (read-only) for new marks or notes from Sharif.
(4) For each index, in this order: **conditions** (is the market moving cleanly and fast enough to even consider a trade, or is it choppy; do the three move together) → **eaten** (what liquidity the last session took) → **created** (what it left behind) → top-down from the monthly: long-term and short-term reads stated separately; old and new higher-timeframe gaps and blocks, each judged on its OWN timeframe's candles (wicks in, bodies out = holding; a same-timeframe close inside = weaker); liquidity built against the edge of those areas; what the last session did; scheduled news; the three compared (weakest / strongest, cleanest pool, divergence) → ideas labelled with or against, scenarios open, the sweep never a condition (price can eat liquidity and then move, or leave it and move).
(5) Draw marks only (no text), each with its `tf` and an END (`t1`) where it stopped mattering; only marks still in play stay open; keep the chart from getting busy. Words go in `read`; the three fixed lines go in `now: {conditions, eaten, created, at}` per index.
(6) Start the watcher in the background: `uv run python research/scripts/hunt_watch.py --until-event --checker-min 5 2>&1`; when it reports, act (order on first in a fast market, write-up after) and start it again. Every report to Sharif leads with conditions, eaten, created. Paper ideas go in the hunt log with entry, stop, targets, conditions and what I learned; an idea taken in chop is labelled so.
(7) At the close: marks cleared, reads replaced with the present state, `hunt.on` false with the next prep's time, watcher stopped, overlay archived.

Never save a reading Sharif has not confirmed. Never paper trade or hunt gold and silver. Do not look at the forward recipe's trade results. Remind him of anything in the memory index marked REMIND. Report to Sharif briefly.
