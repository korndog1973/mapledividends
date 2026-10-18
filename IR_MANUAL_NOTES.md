# Stars & Syrup: manual IR entries

54 entries across 19 companies.

`data/us_ir_manual.json` holds dividend declarations that a person copied from the company's own investor-relations page or press release, because the SEC filings the pipeline reads don't have them yet. All entries were checked on 2026-10-18 (America/Vancouver). On the site each one shows the source label "IR page" and links to the page it came from. No newswires, aggregators or quote sites were used.

**How to retire an entry:** once the filing below is on EDGAR and `pipeline/parse.py` picks up the same record date, delete the manual entry. `site/syrup.py` never lets a manual entry override an EDGAR record with the same record date, so a leftover entry is harmless but redundant.

Entries with no `announced` date come from a dividend-history table that doesn't list a declaration date (AT&T).

## BLK
Replace with: Q3 2026 10-Q (due early Nov 2026) for the Jul 22 declaration. Also check the Q3 earnings 8-K (Ex. 99.1), which may announce the next dividend.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-09-08 | 2026-09-22 | 5.73 | 2026-07-22 | https://ir.blackrock.com/news-and-events/press-releases/press-releases-details/2026/BlackRock-Declares-Quarterly-Dividend-of-5-73-on-Common-Stock-5cb0e6776/default.aspx |
| 2026-06-05 | 2026-06-23 | 5.73 | 2026-05-20 | https://ir.blackrock.com/stock-information/dividend-history/ |
| 2025-12-05 | 2025-12-23 | 5.21 | 2025-11-19 | https://ir.blackrock.com/stock-information/dividend-history/ |

## CVX
Replace with: Q3 2026 10-Q (due early Nov 2026) for the Jul 31 declaration. Older rows: Q1/Q2 10-Qs and the FY2025 10-K.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-08-19 | 2026-09-10 | 1.78 | 2026-07-31 | https://chevroncorp.gcs-web.com/stock-information/dividend-history |
| 2026-05-19 | 2026-06-10 | 1.78 | 2026-05-01 | https://chevroncorp.gcs-web.com/stock-information/dividend-history |
| 2026-02-17 | 2026-03-10 | 1.78 | 2026-01-30 | https://chevroncorp.gcs-web.com/stock-information/dividend-history |
| 2025-11-18 | 2025-12-10 | 1.71 | 2025-10-31 | https://chevroncorp.gcs-web.com/stock-information/dividend-history |

## HD
Replace with: Q3 FY2026 10-Q (due late Nov 2026) for the Aug 20 declaration. The Mar 12 row already comes from an 8-K.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-09-03 | 2026-09-17 | 2.33 | 2026-08-20 | https://ir.homedepot.com/news-releases/2026/08-20-2026-211013830 |
| 2026-06-04 | 2026-06-18 | 2.33 | 2026-05-21 | https://ir.homedepot.com/stock-information/dividend-history |
| 2025-12-04 | 2025-12-18 | 2.3 | 2025-11-20 | https://ir.homedepot.com/stock-information/dividend-history |

## JNJ
Replace with: 10-K for fiscal 2026 (due Feb 2027), which covers the Oct 13 declaration. The Q3 2026 10-Q may mention it earlier as a subsequent event.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-11-24 | 2026-12-08 | 1.34 | 2026-10-13 | https://investor.jnj.com/investor-news/news-details/2026/Johnson--Johnson-Announces-Quarterly-Dividend-for-Fourth-Quarter-2026/default.aspx |

## JPM
Replace with: Q3 2026 10-Q (due early Nov 2026) for the Sep 15 raise. Older rows: Q1/Q2 2026 10-Qs.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-10-06 | 2026-10-31 | 1.65 | 2026-09-15 | https://www.jpmorganchase.com/ir/news/2026/jpmc-declares-increased-common-stock-dividend-9-15 |
| 2026-07-06 | 2026-07-31 | 1.5 | 2026-05-18 | https://www.jpmorganchase.com/ir/news/2026/jpmc-declares-common-stock-dividend-5-18 |
| 2026-04-06 | 2026-04-30 | 1.5 | 2026-03-17 | https://www.jpmorganchase.com/ir/news/2026/jpmc-declares-common-stock-dividend-3-17 |

## LMT
Replace with: FY2026 10-K (due late Jan/Feb 2027) for the Oct 9 raise. The Q3 2026 10-Q (late Oct) may mention it as a subsequent event.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-12-01 | 2026-12-31 | 3.6 | 2026-10-09 | https://lockheedmartin.gcs-web.com/news-releases/news-release-details/lockheed-martin-declares-fourth-quarter-2026-dividend/ |
| 2026-09-01 | 2026-09-25 | 3.45 | 2026-07-22 | https://investors.lockheedmartin.com/stock-information/dividend-history |
| 2026-06-01 | 2026-06-26 | 3.45 | 2026-05-12 | https://investors.lockheedmartin.com/stock-information/dividend-history |
| 2026-03-02 | 2026-03-27 | 3.45 | 2026-02-06 | https://investors.lockheedmartin.com/stock-information/dividend-history |

## MCD
Replace with: Q3 2026 10-Q (due early Nov 2026) for the Sep 17 raise.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-12-01 | 2026-12-15 | 1.93 | 2026-09-17 | https://mcdonalds.mediaroom.com/2026-09-17-McDONALDS-MARKS-50-CONSECUTIVE-YEARS-OF-DIVIDEND-INCREASES,-JOINING-THE-RANKS-OF-DIVIDEND-KINGS |
| 2026-09-01 | 2026-09-16 | 1.86 | 2026-07-23 | https://mcdonalds.mediaroom.com/2026-07-23-McDONALDS-ANNOUNCES-QUARTERLY-CASH-DIVIDEND |

## MMM
Replace with: Q3 2026 10-Q (due late Oct 2026) for the Aug 14 declaration.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-08-24 | 2026-09-11 | 0.78 | 2026-08-14 | https://investors.3m.com/news-events/press-releases/detail/1939/3m-board-declares-quarterly-dividend |
| 2026-05-22 | 2026-06-12 | 0.78 | 2026-05-12 | https://investors.3m.com/news-events/press-releases/detail/1927/3m-board-declares-quarterly-dividend |
| 2026-02-13 | 2026-03-12 | 0.78 | 2026-02-03 | https://investors.3m.com/news-events/press-releases/detail/1916/3m-board-declares-quarterly-dividend |

## MO
Replace with: Q3 2026 10-Q (due late Oct 2026) for the Aug 27 raise.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-09-15 | 2026-10-09 | 1.11 | 2026-08-27 | https://investor.altria.com/press-releases/news-details/2026/Altria-Increases-Quarterly-Dividend-to-1-11-Per-Share/default.aspx |
| 2026-06-15 | 2026-07-10 | 1.06 | 2026-05-14 | https://investor.altria.com/press-releases/news-details/2026/Altria-Holds-2026-Annual-Meeting-of-Shareholders-Declares-Regular-Quarterly-Dividend-of-1-06-Per-Share/default.aspx |
| 2026-03-25 | 2026-04-30 | 1.06 | 2026-02-26 | https://investor.altria.com/press-releases/news-details/2026/Altria-Declares-Regular-Quarterly-Dividend-of-1-06-Per-Share/default.aspx |

## MRK
Replace with: Q3 2026 10-Q (due early Nov 2026) for the Jul 29 declaration.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-09-15 | 2026-10-07 | 0.85 | 2026-07-29 | https://www.merck.com/news/merck-announces-fourth-quarter-2026-dividend/ |
| 2026-06-15 | 2026-07-08 | 0.85 | 2026-05-26 | https://www.merck.com/news/merck-announces-third-quarter-2026-dividend/ |

## MSFT
Replace with: 10-Q for the quarter ended Sep 30, 2026 (due late Oct 2026). Its dividend table lists the Sep 15 declaration.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-11-19 | 2026-12-10 | 0.98 | 2026-09-15 | https://news.microsoft.com/source/2026/09/15/microsoft-announces-quarterly-dividend-increase-7/ |

## NEE
Replace with: Q3 2026 10-Q (due early Nov 2026) for the Jul 30 declaration.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-08-28 | 2026-09-15 | 0.6232 | 2026-07-30 | https://newsroom.nexteraenergy.com/2026-07-30-NextEra-Energy-board-declares-quarterly-dividend |
| 2026-06-05 | 2026-06-15 | 0.6232 | 2026-05-21 | https://www.investor.nexteraenergy.com/stock-information/dividend-history |
| 2026-02-27 | 2026-03-16 | 0.6232 | 2026-02-13 | https://www.investor.nexteraenergy.com/stock-information/dividend-history |
| 2025-11-21 | 2025-12-15 | 0.5665 | 2025-10-23 | https://www.investor.nexteraenergy.com/stock-information/dividend-history |

## O
Replace with: Q3 2026 10-Q (due early Nov 2026) for the Sep 8 raise; FY2026 10-K for the Oct 13 declaration.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-10-30 | 2026-11-13 | 0.2715 | 2026-10-13 | https://www.realtyincome.com/investors/press-releases/realty-income-announces-676th-consecutive-common-stock-monthly-dividend |
| 2026-09-30 | 2026-10-15 | 0.2715 | 2026-09-08 | https://www.realtyincome.com/investors/press-releases/136th-common-stock-monthly-dividend-increase-declared-realty-income |

## PEP
Replace with: Q3 2026 10-Q (due Oct 2026) for the Jul 17 declaration. The older rows are already in the Q1/Q2 10-Qs and the FY2025 10-K.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-09-04 | 2026-09-30 | 1.48 | 2026-07-17 | https://www.pepsico.com/newsroom/press-releases/2026/pepsico-declares-quarterly-dividend-0726 |
| 2026-06-05 | 2026-06-30 | 1.48 | 2026-05-06 | https://www.pepsico.com/newsroom/press-releases/2026/pepsico-declares-quarterly-dividend-0526 |
| 2026-03-06 | 2026-03-31 | 1.4225 | 2026-02-04 | https://www.pepsico.com/investors/dividend-information |
| 2025-12-05 | 2026-01-06 | 1.4225 | 2025-11-19 | https://www.pepsico.com/investors/dividend-information |
| 2025-09-05 | 2025-09-30 | 1.4225 | 2025-07-24 | https://www.pepsico.com/investors/dividend-information |

## PM
Replace with: 8-K filed 2026-09-18 (pm-20260918) is already on EDGAR; our fetch didn't pick it up (MAXDOCS cap). Re-run the US fetch with a higher MAXDOCS, or wait for the Q3 2026 10-Q (late Oct).

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-10-02 | 2026-10-26 | 1.6 | 2026-09-18 | https://www.pmi.com/media-center/press-releases/press-details?newsId=30411 |

## T
Replace with: Q3 2026 10-Q (due late Oct/early Nov 2026) for the Sep 24 declaration. Older rows: Q1/Q2 10-Qs and the FY2025 10-K.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-10-12 | 2026-11-02 | 0.2775 | 2026-09-24 | https://investors.att.com/stock-information/historical-stock-information/historical-common-dividends/att-inc |
| 2026-07-10 | 2026-08-03 | 0.2775 | (not listed) | https://investors.att.com/stock-information/historical-stock-information/historical-common-dividends/att-inc |
| 2026-04-10 | 2026-05-01 | 0.2775 | (not listed) | https://investors.att.com/stock-information/historical-stock-information/historical-common-dividends/att-inc |
| 2026-01-12 | 2026-02-02 | 0.2775 | (not listed) | https://investors.att.com/stock-information/historical-stock-information/historical-common-dividends/att-inc |

## TXN
Replace with: Q3 2026 10-Q (due late Oct 2026) for the Jul 16 row; FY2026 10-K (Feb 2027) for the Oct 15 raise.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-10-30 | 2026-11-10 | 1.52 | 2026-10-15 | https://www.ti.com/about-ti/newsroom/news-releases/2026/2026-10-15-texas-instruments-board-declares-fourth-quarter-2026-quarterly-dividend.html |
| 2026-07-31 | 2026-08-11 | 1.42 | 2026-07-16 | https://investor.ti.com/stock-information/dividends-stock-splits |
| 2026-05-05 | 2026-05-19 | 1.42 | 2026-04-16 | https://investor.ti.com/stock-information/dividends-stock-splits |
| 2026-01-30 | 2026-02-10 | 1.42 | 2026-01-15 | https://investor.ti.com/stock-information/dividends-stock-splits |

## UPS
Replace with: Q3 2026 10-Q (due early Nov 2026) for the Aug 5 declaration.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-08-17 | 2026-09-03 | 1.64 | 2026-08-05 | https://investors.ups.com/news-events/press-releases/detail/2166/ups-announces-quarterly-dividend |
| 2026-05-18 | 2026-06-04 | 1.64 | 2026-05-06 | https://investors.ups.com/news-events/press-releases/detail/2159/ups-announces-quarterly-dividend |

## VZ
Replace with: Q3 2026 10-Q (due late Oct 2026) for the Sep 9 declaration. The Apr 10 row already comes from an 8-K.

| Record | Pay | Amount (US$) | Announced | Source |
|---|---|---|---|---|
| 2026-10-09 | 2026-11-02 | 0.7075 | 2026-09-09 | https://www.verizon.com/about/news/verizon-declares-quarterly-dividend-september-2026 |
| 2026-07-10 | 2026-08-03 | 0.7075 | 2026-06-04 | https://www.verizon.com/about/investors/dividend-history |
| 2026-01-12 | 2026-02-02 | 0.69 | 2025-12-04 | https://www.verizon.com/about/investors/dividend-history |
