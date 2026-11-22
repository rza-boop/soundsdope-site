# soundsdope.io site

Static site for https://www.soundsdope.io, served by GitHub Pages from `rza-boop/soundsdope-site` (branch `main`, root).
Built from the cabin comps in `CreatorLand/Brands/soundsdope/site-mock/v7/cabin/` by `_build/build_site.py`.

## Rebuild and push

```
cd ~/Desktop/CreatorLand/Brands/soundsdope/site
python3 _build/build_site.py          # rewrites every page, assets/, favicons, og.jpg, robots.txt, sitemap.xml
git status && git diff --stat         # look before you push
git add -A && git commit -m "Rebuild from the v7 cabin comps" && git push
```

GitHub Pages republishes within a minute or two. Check with
`curl -s --resolve www.soundsdope.io:443:185.199.108.153 https://www.soundsdope.io/ | head`.

If the build stops with an `AssertionError`, a comp changed where the build strips something (a draft mark, a
pending section, a rival row). Read the message, adjust the matching line in `build_site.py`, and rerun. The build
refuses to write a page that still says draft, placeholder, decision pending, needs a source, Gemini or Rza.

## What the live build leaves out (until the comps or Rza settle it)

- Review bar, draft marks, image credits, "(decision pending)" sections.
- Home: the placeholder quotes and their heading; the rival columns of the compare teaser; the copyright row.
- Compare: rival rows, the Admin fee column (not set), the copyright column, the links to the rival pages.
- The seven rival pages (`/compare/<rival>`) and the news post template (`/news/<post>`).
- Learn: the four article titles that have no article yet; the article's Related articles.
- News: the placeholder posts ("The first summaries are coming soon." instead).
- About: the placeholder people.
- Resources: MCPSI (mcpsi.ie does not resolve).
- Terms and Privacy: one line each saying the text is being written.

## Held for decisions

- Forms (calculator, inquiry, contact) show "Opens soon" with the submit disabled: no soundsdope inbox yet.
- Not indexed: `robots.txt` disallows all and every page has `noindex`. To open: change both in `build_site.py`.
- Footer legal-entity line: counsel.

## Hosting

- `CNAME` www.soundsdope.io; apex A records 185.199.108-111.153 and `www` CNAME `rza-boop.github.io.` at Namecheap.
- Namecheap records before go-live: `_build/namecheap-before.xml` (EmailType FWD, passed again on setHosts).
- Process: `CreatorLand/New Channel Build Kit/How we build complex sites.md`, section 6.
