#!/usr/bin/env python3
"""Build the soundsdope.io static site from the v7 cabin comps.

Site lead, 22 Nov 2026. Same route as ndigocartel.com and frankwhitedealsdope.com
(CreatorLand/New Channel Build Kit/How we build complex sites.md, sections 5 and 6).

It reads the built comps in Brands/soundsdope/site-mock/v7/cabin/ (read only), and for each live page:
  - drops the review chrome: the review bar, "draft" marks, placeholder tags, image credits, "(decision pending)" sections;
  - drops what is not ready to publish: placeholder quotes, competitor cells that need a source, placeholder people,
    placeholder news posts, and article titles that have no article yet;
  - turns every form into an honest "Opens soon" form with the submit disabled (no inbox yet);
  - wraps the page in a real <head> (title, description, canonical, og, favicon, noindex) and points links at /<page>/.
Every replacement asserts that the text it expects is there, so a change in the comps stops the build with the
reason instead of publishing something half-stripped. A last pass refuses to write if any review word survives.

Run: python3 _build/build_site.py [comps-dir]     (default: ../../site-mock/v7/cabin from this file)
"""
import html, pathlib, re, shutil, sys

SITE = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else SITE.parent / "site-mock" / "v7" / "cabin"
FAVSRC = SITE.parent / "brand" / "brick3d"          # the clef-and-sharp favicon set (Rza, 19 Nov 2026)
ORIGIN = "https://www.soundsdope.io"
ARTICLE = "what-the-mlc-does"

# comp file -> (live path, title, description or None to take the page's own lede)
PAGES = {
    "index.html":        ("",                       "soundsdope.io", None),
    "how-it-works.html": ("how-it-works/",          "How it works", None),
    "calculator.html":   ("calculator/",            "Calculator", None),
    "start.html":        ("start/",                 "Sign up", None),
    "contact.html":      ("contact/",               "Contact", None),
    "compare.html":      ("compare/",               "Compare", None),
    "learn.html":        ("learn/",                 "Learn", None),
    "learn-article.html": (f"learn/{ARTICLE}/",     "What The MLC does", "The US body that collects streaming mechanicals, and what \"unmatched\" means."),
    "resources.html":    ("resources/",             "Resources", None),
    "news.html":         ("news/",                  "News", None),
    "about.html":        ("about/",                 "About", None),
    "faq.html":          ("faq/",                   "FAQ", "Questions about soundsdope.io, answered plainly."),
    "terms.html":        ("terms/",                 "Site terms", "Site terms for soundsdope.io."),
    "privacy.html":      ("privacy/",               "Privacy policy", "Privacy policy for soundsdope.io."),
}
# Held back from the live build (listed in README.md): the seven rival pages (every rival cell needs a source,
# so nothing sourced is left) and the news post template (no real post yet).
HELD = ["compare-songtrust.html", "compare-sentric.html", "compare-tunecore.html", "compare-distrokid.html",
        "compare-routenote.html", "compare-kosign.html", "compare-rightstune.html", "news-post.html"]
LINKS = {f: "/" + p for f, (p, _, _) in PAGES.items()}

EXTRA_CSS = """<style>
.key[disabled]{opacity:.55;cursor:not-allowed;filter:grayscale(.4)}
.soon{font-size:13px;color:#A6A8AE;margin-top:10px}
</style>"""


def sub1(s, old, new, why):
    """Replace exactly one occurrence, or stop the build."""
    n = s.count(old)
    assert n == 1, f"{why}: expected 1, found {n}: {old[:80]!r}"
    return s.replace(old, new)


def rx(s, pat, new, why, count_min=1, flags=re.S):
    out, n = re.subn(pat, new, s, flags=flags)
    assert n >= count_min, f"{why}: pattern not found: {pat[:80]!r}"
    return out


def body_of(f):
    s = (SRC / f).read_text()
    a = s.index("</header>") + len("</header>")      # after the site nav
    b = s.index("<footer>")
    nav = s[s.index('<header class="nav">'):a]
    foot = s[b:s.index("</footer>") + len("</footer>")]
    return nav, s[a:b], foot


def strip_common(s):
    s = re.sub(r'<p class="mark">.*?</p>', "", s, flags=re.S)                        # "Draft ..." marks
    s = re.sub(r'<p class="meta"[^>]*>[^<]*(Draft|Placeholder)[^<]*</p>\s*', "", s)  # article / legal draft lines
    s = re.sub(r'<p class="draftnote">.*?</p>', "", s, flags=re.S)
    s = re.sub(r'<span class="credit">[^<]*</span>\s*', "", s)                        # "Generated image (Gemini), draft"
    # "(decision pending)" sections: a section that holds only a heading and the pending box goes; inline boxes go
    s = re.sub(r'<section class="sec[^"]*"><div class="wrap"><h2>[^<]*</h2><div style="margin-top:\d+px"><div class="pending">[^<]*</div></div></div></section>', "", s)
    s = re.sub(r'<div style="margin-top:\d+px">\s*<div class="pending">[^<]*</div></div>', "", s)
    s = re.sub(r'<div class="f full"><div class="pending">[^<]*</div></div>', "", s)
    return s


def soon_form(s, button_text, why):
    """No inbox yet (open with Rza): the form shows, the submit is disabled and says so (playbook section 5)."""
    s = rx(s, r'<form class="([^"]*)" action="#" method="post">|<form action="#" method="post">',
           lambda m: f'<form class="{m.group(1)}" onsubmit="return false">' if m.group(1) else '<form onsubmit="return false">', why)
    s = sub1(s, f'<button class="key go" type="submit">{button_text}</button>',
             '<button class="key go" type="submit" disabled aria-disabled="true">Opens soon</button>', why)
    return s


def page_body(f, s):
    if f == "index.html":
        # placeholder quotes: the whole quotes block and its heading go until real quotes exist; "Where we file" stays
        s = rx(s, r'\s*<h2>Writers who looked</h2>\s*<div class="quotes">.*?</div>\s*(?=<div class="where">)', "\n      ", "home quotes")
        # compare teaser: rival columns are all "needs a source"; only our answers and the questions stay
        # "You keep your copyright" was cut from the comps as unsupported except in rows marked draft (commit 43e4e62);
        # with the draft label gone it would read as a stated fact, so the row stays off the live pages
        s = rx(s, r'<tr><th>Do you keep your copyright\?</th>.*?</tr>', "", "home copyright row")
        s = rx(s, r'<th>Distributor publishing add-ons</th><th>Traditional admins</th>', "", "home compare head")
        s = rx(s, r'<td data-l="(Distributor publishing add-ons|Traditional admins)">&mdash;<span class="src">needs a source</span></td>', "", "home compare cells", 6)
        s = sub1(s, '<p class="lede">The same plain questions, asked of each kind of service.</p>',
                 '<p class="lede">The plain questions to ask of any service, and our answers.</p>', "home compare lede")
        s = soon_form(s, "See what may be uncollected", "home calculator")
    elif f == "calculator.html":
        s = soon_form(s, "See what may be uncollected", "calculator")
    elif f == "start.html":
        s = soon_form(s, "Send the inquiry", "start")
    elif f == "contact.html":
        s = soon_form(s, "Send", "contact")
    elif f == "compare.html":
        s = rx(s, r'<tr><th>[^<]*</th>(<td data-l="[^"]*">&mdash;<span class="src">needs a source</span></td>)+</tr>', "", "rival rows", 7)
        # "Admin fee" is still "Draft: Rza sets": the column goes until he sets it
        s = sub1(s, "<th>You keep your copyright</th>", "", "copyright head")
        s = sub1(s, '<td class="us" data-l="You keep your copyright">Yes</td>', "", "copyright cell")
        s = sub1(s, "<th>Admin fee</th>", "", "admin fee head")
        s = sub1(s, '<td class="us" data-l="Admin fee">Draft: Rza sets</td>', "", "admin fee cell")
        s = rx(s, r'<section class="sec[^"]*"><div class="wrap"><h2>One page per rival</h2>.*?</section>', "", "rival links")
        s = sub1(s, "Us against the services writers ask about, on the same plain questions. Every figure will carry its source and the date we checked it.",
                 "The plain questions to ask of any service, and our answers. Other services go on this table as each answer is sourced and dated.", "compare lede")
    elif f == "learn.html":
        # five draft titles, one article: only the article that exists is listed
        s = rx(s, r'(<ul class="rows"><li><a href="learn-article.html">.*?</li>)(<li>.*?</li>)+(</ul>)', r"\1\3", "learn list")
    elif f == "learn-article.html":
        s = rx(s, r'<section class="sec[^"]*"><div class="wrap"><h2>Related articles</h2>.*?</section>', "", "related articles")
    elif f == "news.html":
        s = rx(s, r'<ul class="rows">.*?</ul>', '<p class="lede">The first summaries are coming soon.</p>', "news posts")
    elif f == "resources.html":
        # mcpsi.ie does not resolve (checked 22 Nov 2026), so the dead link stays off the live page
        s = sub1(s, '<li><a href="https://www.mcpsi.ie">MCPSI</a><span>Mechanicals</span></li>', "", "mcpsi")
    elif f in ("terms.html", "privacy.html"):
        # the comp's section-by-section "Legal text to come. This section will say..." is a note to ourselves
        # (playbook section 5); live, the page says plainly that the text is being written (counsel writes final)
        name = "site terms" if f == "terms.html" else "privacy policy"
        s = rx(s, r'(<article class="prose">)(?:<p class="meta"[^>]*>[^<]*</p>)?(?:<h2>[^<]*</h2><p>Legal text to come\.[^<]*</p>)+(</article>)',
               rf'\1<p>Our {name} are being written and will be posted on this page.</p>\2' if f == "terms.html"
               else rf'\1<p>Our {name} is being written and will be posted on this page.</p>\2', f"legal body {f}")
        s = sub1(s, '<p class="lede">Last updated: to come.</p>', "", "legal lede")
    elif f == "about.html":
        s = rx(s, r'<section class="sec[^"]*"><div class="wrap"><h2>Who runs it</h2>.*?</section>', "", "placeholder people")
    return strip_common(s)


def links(s):
    for f, path in LINKS.items():
        s = s.replace(f'href="{f}"', f'href="{path}"').replace(f'href="{f}#', f'href="{path}#')
    return s


def lede(s):
    m = re.search(r'<p class="lede"[^>]*>(.*?)</p>', s, flags=re.S)
    assert m, "no lede for description"
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()


def fonts():
    """The comps' Google Fonts link, taken from the comp so a type change carries through."""
    m = re.search(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>', (SRC / "index.html").read_text())
    assert m, "no Google Fonts link in the comps"
    return m.group(0)


def wrap(title, desc, path, nav, body, foot):
    full = title if path == "" else f"{title} · soundsdope.io"
    url = ORIGIN + "/" + path
    e = html.escape
    FONTS = fonts()
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="noindex, nofollow">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="website"><meta property="og:site_name" content="soundsdope.io">
<meta property="og:title" content="{e(full)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{ORIGIN}/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#05070B">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{FONTS}
<link rel="stylesheet" href="/assets/cabin.css">
{EXTRA_CSS}
</head>
<body>
{nav}
{body.strip()}
{foot}
</body>
</html>
"""


# words that mean a review artefact survived; the build refuses to write if any is left in a live page
FORBIDDEN = ["draft", "placeholder", "decision pending", "needs a source", "mockup", "gemini", "rza", "for review",
             "class=\"review\"", "class=\"mark\"", "class=\"pending\"", "class=\"tag\"", "class=\"credit\""]


def check(path, s):
    low = re.sub(r' placeholder="[^"]*"', "", s).lower()  # the input hint attribute is not a placeholder section
    bad = [w for w in FORBIDDEN if w in low] + re.findall(r'href="(?!/|https?:|mailto:|#)[^"]*"', s)  # relative comp links left
    assert not bad, f"{path or 'home'}: still has {bad}"


def main():
    for f in list(PAGES) + HELD:
        assert (SRC / f).exists(), f"comp missing: {f}"
    # clean previous output (only what this script writes)
    for p in SITE.iterdir():
        if p.name in {"_build", ".git", "README.md", "CNAME", ".gitignore"}:
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()

    built = []
    for f, (path, title, desc) in PAGES.items():
        nav, body, foot = body_of(f)
        body = links(page_body(f, body))
        nav, foot = links(nav), links(strip_common(foot))
        foot = rx(foot, r'<span>Night street: generated image \(Gemini\), draft</span>', "", "footer credit", 0)
        page = wrap(title, desc or lede(body), path, nav, body, foot)
        check(path, page)
        d = SITE / path; d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page)
        built.append(path)
        print("wrote", (d / "index.html").relative_to(SITE))

    # 404: the site shell with a short not-found body (absolute asset paths, so it works at any depth)
    nav, _, foot = body_of("about.html")
    nf = """<main id="top">
<section class="phead"><div class="wrap"><h1>Page not found.</h1><p class="lede">That address isn't on this site.</p></div></section>
<hr class="led">
<section class="sec"><div class="wrap"><div class="cta panel"><p>Start from the home page.</p><a class="key go" href="/">Home</a></div></div></section>
</main>"""
    page = wrap("Page not found", "Page not found.", "404.html", links(nav), nf,
                links(rx(strip_common(foot), r'<span>Night street: generated image \(Gemini\), draft</span>', "", "footer credit", 0)))
    check("404", page); (SITE / "404.html").write_text(page)

    # assets: one stylesheet and its images (url(img/..) resolves next to the css)
    (SITE / "assets" / "img").mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / "cabin.css", SITE / "assets" / "cabin.css")
    css = (SRC / "cabin.css").read_text()
    for img in sorted(set(re.findall(r"url\(img/([^)]+)\)", css))):
        shutil.copy(SRC / "img" / img, SITE / "assets" / "img" / img)

    # favicon: the clef and sharp on the shade 2 tile (brand/brick3d, sd-logo lead, 19 Nov 2026)
    shutil.copy(FAVSRC / "svg" / "fav-tile.svg", SITE / "favicon.svg")
    shutil.copy(FAVSRC / "png" / "fav-tile-32.png", SITE / "favicon-32.png")
    shutil.copy(FAVSRC / "png" / "fav-tile-180.png", SITE / "apple-touch-icon.png")
    shutil.copy(FAVSRC / "png" / "fav-tile-32.png", SITE / "favicon.ico")  # browsers that ask for /favicon.ico get a PNG

    # og.jpg: 1200x630 crop of the hero picture
    import subprocess
    subprocess.run(["sips", "-s", "format", "jpeg", "--resampleWidth", "1200", str(SRC / "img" / "hero-trunk.jpg"),
                    "--out", str(SITE / "og.jpg")], check=True, capture_output=True)
    subprocess.run(["sips", "-c", "630", "1200", str(SITE / "og.jpg")], check=True, capture_output=True)  # centre crop

    # every internal link and asset resolves
    for p in SITE.rglob("*.html"):
        s = p.read_text()
        for h in re.findall(r'(?:href|src)="(/[^"#]*)', s):
            t = SITE / h.lstrip("/")
            assert (t / "index.html").exists() if h.endswith("/") else t.exists(), f"{p.relative_to(SITE)}: broken link {h}"

    (SITE / "CNAME").write_text("www.soundsdope.io\n")
    (SITE / ".nojekyll").write_text("")
    # Not indexed until Rza says to open it (orchestrator's call, 22 Nov 2026, reversible): every page also carries noindex.
    (SITE / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    (SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + "".join(f"  <url><loc>{ORIGIN}/{p}</loc></url>\n" for p in built) + "</urlset>\n")
    print(f"built {len(built)} pages from {SRC}")


if __name__ == "__main__":
    main()
