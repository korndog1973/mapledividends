# MapleDividends audit and roadmap

Audit baseline: main at `a487622`. Scope: EDGAR ingestion, committed Canadian and U.S. dividend datasets, static rendering, GitHub Actions, and the public Ask function.

| Priority | Finding | Phase 1 change |
| --- | --- | --- |
| High | `build.sh` skipped downloads during cached builds but still reparsed missing exhibits and rewrote parsed data. | Cached builds validate and render saved snapshots without EDGAR or parser calls. |
| High | `pipeline/fetch_edgar.py` and `pipeline/parse.py` skipped upstream and local errors and the workflow could deploy reduced coverage. | Fail on incomplete inputs, compare the latest declarations against the starting snapshots, and restore local data on failed refreshes. |
| High | `site/build.py` compared numeric amounts before checking currency and accepted unresolved currencies. | Compare only a contiguous sequence in one confirmed currency. U.S. declared currency conflicts remain unresolved. |
| High | Special distributions were included in ex-date calendars using record dates as a proxy. Ask also used a different U.S. dataset than the public company pages. | Keep special distributions in record-date history, use regular distributions for inferred calendar dates, and use the rendered U.S. declaration set for Ask. |
| Medium | The Ask endpoint parsed the entire request before enforcing a question limit, and its answer cache conflated punctuation and case, both relevant to ticker retrieval. | Limit bytes at the stream, require text for the question, and key replies by the normalized question text with punctuation and case preserved. |
| Medium | Daily CSS cache versioning could serve stale assets after same-day rebuilds. Sitemap timestamps relied on build and filing dates. | Version CSS by content and omit estimated sitemap modification dates. |
| Medium | The generic 404 page interpolated issuer names into trusted HTML. | Escape issuer data before interpolation. Pull requests run validation and tests without deploying. |

## Remaining work

1. **Preserve coverage across deployments.** Persist the last successfully deployed snapshot for comparison and distinguish supported upstream removals from transport failures. Phase 1 compares against the starting files, which on a clean runner are the committed snapshots. Add operational alerts for failed refreshes and measure how often EDGAR queries or exhibits fail.
2. **Verify data against issuers.** Add fixture-based extraction tests for high-traffic issuers, confirm overrides and latest amounts against their announcements, and store explicit exchange ex-dates where licensed and available. Current regular ex-dates still use the T+1 record-date convention. The [TSX issuer guide](https://www.tsx.com/ebooks/en/etf-guide/) and [FINRA notice 24-04](https://www.finra.org/sites/default/files/2024-02/Regulatory_Notice_24-04.pdf) describe the convention and exceptions. Structural validation cannot prove a payout matches the filing.
3. **Review Ask in Cloudflare.** Verify quota and account settings. Current KV and Cache API counters are approximate under concurrency. Enforce global limits with an atomic service if required. Add source-linked deterministic answers for payout amounts and dates to avoid model errors. Review the live response headers and third-party widget scripts.
4. **Measure search performance.** Inspect indexed URLs and canonical selection in Search Console, check mobile Core Web Vitals, and reintroduce sitemap lastmod only where a meaningful content change can be dated. [Google sitemap documentation](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).

## Verify

Install `requirements.txt`, run `python -m unittest discover -s tests`, and run `SKIP_FETCH=1 ./build.sh`. Production refreshes also require EDGAR access and poppler. Review deployment logs and fresh coverage counts before merging.
