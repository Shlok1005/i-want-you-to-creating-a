#!/usr/bin/env python3
"""Generate Fitness Gurukul blog pages from topic 1–4 source files."""

from __future__ import annotations

import glob
import html
import json
import os
import re
import zipfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "blog"
SITE_URL = "https://fitnessgurukul.co.in"
SITE_NAME = "Fitness Gurukul"
AUTHOR = "Fitness Gurukul Coaching Team"

CATEGORIES = {
    "strength-training": {
        "name": "Strength & Training",
        "short": "Strength",
        "description": "Guides on strength training, fat loss, posture, recovery, and getting started in the gym — built for Hyderabad trainees.",
        "keywords": "strength training, weight loss, personal training Hyderabad, gym guide, posture correction",
        "topic": 1,
    },
    "group-fitness": {
        "name": "Group Fitness",
        "short": "Group",
        "description": "Group yoga, Zumba, cycling, 5K prep, webinars, and community fitness events around Hyderabad.",
        "keywords": "group fitness, yoga classes Hyderabad, Zumba, cycling routes, community fitness",
        "topic": 2,
    },
    "kids-fitness": {
        "name": "Kids Fitness",
        "short": "Kids",
        "description": "Structured kids fitness, youth posture, teen strength, summer camps, and family-friendly events in Hyderabad.",
        "keywords": "kids fitness Hyderabad, youth training, summer camp, children exercise, teen strength",
        "topic": 3,
    },
    "race-endurance": {
        "name": "Race & Endurance",
        "short": "Race",
        "description": "Race-day strategy, triathlon and marathon prep, swimathons, cycling rallies, and fitness tourism across India.",
        "keywords": "triathlon training, marathon prep, swimathon, endurance racing India, Ladakh Marathon",
        "topic": 4,
    },
}

PLACEHOLDER_CATEGORIES = [
    {
        "slug": "nutrition-tips",
        "name": "Nutrition Tips",
        "description": "Indian meal plans, macros, and fueling strategies — coming soon.",
        "placeholders": [
            "High-Protein Indian Meals for Busy Professionals",
            "How to Track Macros Without Obsessing",
            "Pre- and Post-Workout Nutrition Made Simple",
        ],
    },
    {
        "slug": "yoga-recovery",
        "name": "Yoga & Recovery",
        "description": "Mobility, breathwork, and recovery protocols — coming soon.",
        "placeholders": [
            "Breathwork Routines for Stressful Work Weeks",
            "Mobility Flows for Lifters",
            "Sleep, Recovery, and Training Adaptation",
        ],
    },
    {
        "slug": "success-stories",
        "name": "Success Stories",
        "description": "Member transformations and journey write-ups — coming soon.",
        "placeholders": [
            "From Desk Fatigue to First 5K",
            "90-Day Transformation: What Consistency Looks Like",
        ],
    },
    {
        "slug": "wellness-tips",
        "name": "Wellness Tips",
        "description": "Everyday habits for long-term health — coming soon.",
        "placeholders": [
            "Building a Morning Routine That Sticks",
            "Managing Energy Across a Hybrid Work Week",
        ],
    },
]

HEADER_ROOT = """\
<header class="site-header">
  <div class="header-inner">
    <div class="header-left">
      <a class="brand" href="{home}">
        <span class="brand-mark"><img src="{assets}assets/fitness-gurukul-logo.png" alt="" /></span>
        <span class="brand-text"><strong>Fitness</strong><span>Gurukul</span></span>
      </a>
    </div>
    <nav class="desktop-nav">
      <a href="{home}">Home</a>
      <a href="{prefix}services.html">Services</a>
      <a href="{prefix}coaches.html">Coaches</a>
      <a href="{prefix}events.html">Events</a>
      <a href="{prefix}blog.html">Blog</a>
      <a href="{prefix}testimonials.html">Testimonials</a>
      <a href="{prefix}tools.html">Tools</a>
      <a href="{prefix}transformation-challenge.html">Challenge</a>
    </nav>
    <div class="header-app-links">
      <a class="header-play-btn" href="https://apps.apple.com/us/app/fitness-gurukul/id6771451272" target="_blank" rel="noopener" aria-label="Download on the App Store">
        <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .76-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 16.99 2.93 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.02 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83zM13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
        <span>App Store</span>
      </a>
      <a class="header-play-btn" href="https://play.google.com/store/apps/details?id=com.fitnessgurukul.app" target="_blank" rel="noopener" aria-label="Get it on Google Play">
        <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M4.5 3.5v17l14-8.5z"/></svg>
        <span>Play Store</span>
      </a>
    </div>
    <button class="menu-button" id="menuButton" aria-label="Open navigation" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</header>
<nav class="mobile-nav" id="mobileNav">
  <div class="mobile-nav-header">
    <a class="brand" href="{home}">
      <span class="brand-mark"><img src="{assets}assets/fitness-gurukul-logo.png" alt="" /></span>
      <span class="brand-text"><strong>Fitness</strong><span>Gurukul</span></span>
    </a>
    <button class="mobile-nav-close" id="mobileNavClose">&times;</button>
  </div>
  <a href="{home}">Home</a>
  <a href="{prefix}services.html">Services</a>
  <a href="{prefix}coaches.html">Coaches</a>
  <a href="{prefix}events.html">Events</a>
  <a href="{prefix}blog.html">Blog</a>
  <a href="{prefix}testimonials.html">Testimonials</a>
  <a href="{prefix}tools.html">Tools</a>
  <a href="{prefix}transformation-challenge.html">Challenge</a>
  <div class="mobile-nav-app-links">
    <a class="header-play-btn" href="https://apps.apple.com/us/app/fitness-gurukul/id6771451272" target="_blank" rel="noopener">App Store</a>
    <a class="header-play-btn" href="https://play.google.com/store/apps/details?id=com.fitnessgurukul.app" target="_blank" rel="noopener">Play Store</a>
  </div>
</nav>
"""

FOOTER = """\
<footer class="site-footer footer-news">
  <div class="footer-news-inner">
    <div class="footer-news-proof">
      <div class="footer-news-proof-item"><strong>50+</strong><span>Events</span></div>
      <div class="footer-news-proof-item"><strong>10K+</strong><span>Participants</span></div>
      <div class="footer-news-proof-item"><strong>13</strong><span>Years</span></div>
    </div>
    <div class="footer-news-main">
      <div class="footer-news-brand">
        <a class="brand" href="{home}">
          <img src="{assets}assets/fitness-gurukul-logo.png" alt="Fitness Gurukul" />
          <span class="brand-text"><strong>Fitness</strong><span>Gurukul</span></span>
        </a>
        <p class="footer-news-tagline">Personal training, made personal. Hyderabad's trusted fitness coaching since 2013.</p>
        <div class="footer-news-contact">
          <a href="tel:+917207113310">+91 72071 13310</a>
          <a href="mailto:contact@fitnessgurukul.co.in">contact@fitnessgurukul.co.in</a>
          <span>Manikonda, Hyderabad</span>
        </div>
      </div>
      <div class="footer-news-links">
        <div class="footer-news-col">
          <h4>Discover</h4>
          <nav>
            <a href="{prefix}about.html">About Us</a>
            <a href="{prefix}coaches.html">Our Coaches</a>
            <a href="{prefix}blog.html">Blog</a>
            <a href="{prefix}testimonials.html">Testimonials</a>
          </nav>
        </div>
        <div class="footer-news-col">
          <h4>Blog Topics</h4>
          <nav>
            <a href="{prefix}blog.html#strength-training">Strength &amp; Training</a>
            <a href="{prefix}blog.html#group-fitness">Group Fitness</a>
            <a href="{prefix}blog.html#kids-fitness">Kids Fitness</a>
            <a href="{prefix}blog.html#race-endurance">Race &amp; Endurance</a>
          </nav>
        </div>
        <div class="footer-news-col">
          <h4>Support</h4>
          <nav>
            <a href="{prefix}contact.html">Contact Us</a>
            <a href="{prefix}tools.html">Fitness Tools</a>
            <a href="{prefix}book-consultation.html">Book a Call</a>
          </nav>
        </div>
      </div>
    </div>
    <div class="footer-news-bottom">
      <p class="footer-news-copy">&copy; 2026 Fitness Gurukul. All rights reserved.</p>
    </div>
  </div>
</footer>
"""

WA_FAB = """\
<div class="fab-wa">
  <a href="https://wa.me/917207113310" target="_blank" rel="noopener" aria-label="WhatsApp">
    <svg viewBox="0 0 24 24" fill="currentColor" width="28" height="28"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
  </a>
</div>
"""


def docx_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    paras = re.findall(r"<w:p[\s>][\s\S]*?</w:p>", xml)
    out: list[str] = []
    for p in paras:
        texts = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)
        t = html.unescape("".join(texts)).strip()
        if t:
            out.append(t)
    return out


def md_to_paragraphs(text: str) -> list[str]:
    lines = text.splitlines()
    paras: list[str] = []
    buf: list[str] = []
    for line in lines:
        raw = line.rstrip()
        if not raw.strip():
            if buf:
                paras.append(" ".join(buf).strip())
                buf = []
            continue
        if raw.lstrip().startswith("#"):
            if buf:
                paras.append(" ".join(buf).strip())
                buf = []
            paras.append(re.sub(r"^#+\s*", "", raw).strip())
            continue
        if re.match(r"^[-*]\s+", raw.strip()) or re.match(r"^\d+\.\s+", raw.strip()):
            if buf:
                paras.append(" ".join(buf).strip())
                buf = []
            paras.append(re.sub(r"^([-*]|\d+\.)\s+", "", raw.strip()))
            continue
        # bold markers strip for plain storage; keep text
        buf.append(re.sub(r"\*\*([^*]+)\*\*", r"\1", raw.strip()))
    if buf:
        paras.append(" ".join(buf).strip())
    return [p for p in paras if p]


def slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


def _is_short_tip(text: str) -> bool:
    """Bullet-like tip line (not a full prose paragraph or section title)."""
    if _looks_like_section_heading(text):
        return False
    if len(text) > 120 or len(text.split()) > 20:
        return False
    if text.endswith(("?", "!")):
        return False
    # numbered ranges / tip fragments often lack a terminal period
    if re.match(r"^\d", text) or "–" in text[:8] or ":" in text:
        return True
    if not text.endswith(".") and len(text) <= 110:
        return True
    return False


def _looks_like_section_heading(text: str) -> bool:
    if len(text) > 90 or len(text.split()) > 14:
        return False
    if text.endswith((".", "?", "!")):
        return False
    # Prefer headings that read like titles (multiple capitals / no leading digit tip)
    if re.match(r"^\d", text):
        return False
    words = [w for w in text.replace("—", " ").replace("-", " ").split() if w]
    if not words:
        return False
    # Tip fragments with a colon mid-line are usually list items ("Progressive overload: ...")
    if ":" in text and not text.endswith(":"):
        return False
    caps = sum(1 for w in words if w[:1].isupper())
    return caps >= max(2, (len(words) + 1) // 2) or (len(text) <= 70 and text[0].isupper() and caps >= 2)


def paragraphs_to_html(paras: list[str]) -> tuple[str, str, str, list[str]]:
    """Return title, subtitle, body_html, toc_headings."""
    if not paras:
        return "Untitled", "", "", []
    title = paras[0]
    subtitle = paras[1] if len(paras) > 1 else ""
    body_paras = paras[2:] if len(paras) > 1 else []
    toc: list[str] = []
    parts: list[str] = []
    i = 0
    n = len(body_paras)
    while i < n:
        p = body_paras[i]
        # Cluster of 2+ short tip lines => unordered list
        if _is_short_tip(p):
            run = [p]
            j = i + 1
            while j < n and _is_short_tip(body_paras[j]):
                run.append(body_paras[j])
                j += 1
            if len(run) >= 2:
                parts.append("<ul>")
                for it in run:
                    parts.append(f"<li>{html.escape(it)}</li>")
                parts.append("</ul>")
                i = j
                continue
            # Single short line: section heading if it looks like one, else paragraph
            if _looks_like_section_heading(p):
                hid = slugify(p)
                toc.append(p)
                parts.append(f'<h2 id="{html.escape(hid)}">{html.escape(p)}</h2>')
                i += 1
                continue
        elif _looks_like_section_heading(p):
            hid = slugify(p)
            toc.append(p)
            parts.append(f'<h2 id="{html.escape(hid)}">{html.escape(p)}</h2>')
            i += 1
            continue
        parts.append(f"<p>{html.escape(p)}</p>")
        i += 1
    return title, subtitle, "\n".join(parts), toc


def estimate_read_minutes(text: str) -> int:
    words = len(re.findall(r"\w+", text))
    return max(2, round(words / 200))


def chrome(depth: int = 0) -> tuple[str, str, str, str, str]:
    prefix = "../" * depth
    home = f"{prefix}index.html"
    assets = prefix
    header = HEADER_ROOT.format(home=home, prefix=prefix, assets=assets)
    footer = FOOTER.format(home=home, prefix=prefix, assets=assets)
    return prefix, assets, header, footer, home


def seo_head(
    *,
    title: str,
    description: str,
    canonical: str,
    keywords: str,
    og_type: str = "website",
    depth: int = 0,
    json_ld: list | None = None,
    published: str | None = None,
) -> str:
    prefix = "../" * depth
    esc = html.escape
    parts = [
        f"<title>{esc(title)}</title>",
        f'<meta name="description" content="{esc(description)}" />',
        f'<meta name="keywords" content="{esc(keywords)}" />',
        f'<meta name="author" content="{esc(AUTHOR)}" />',
        '<meta name="robots" content="index, follow, max-image-preview:large" />',
        f'<link rel="canonical" href="{esc(canonical)}" />',
        f'<meta property="og:type" content="{esc(og_type)}" />',
        f'<meta property="og:site_name" content="{esc(SITE_NAME)}" />',
        f'<meta property="og:title" content="{esc(title)}" />',
        f'<meta property="og:description" content="{esc(description)}" />',
        f'<meta property="og:url" content="{esc(canonical)}" />',
        f'<meta property="og:image" content="{SITE_URL}/assets/fitness-gurukul-logo.png" />',
        '<meta name="twitter:card" content="summary_large_image" />',
        f'<meta name="twitter:title" content="{esc(title)}" />',
        f'<meta name="twitter:description" content="{esc(description)}" />',
        f'<link rel="stylesheet" href="{prefix}styles.css" />',
        f'<script src="{prefix}app.js?v=gs-20260805" defer></script>',
    ]
    if published:
        parts.insert(5, f'<meta property="article:published_time" content="{esc(published)}" />')
        parts.insert(6, f'<meta property="article:author" content="{esc(AUTHOR)}" />')
    if json_ld:
        for block in json_ld:
            parts.append(
                '<script type="application/ld+json">'
                + json.dumps(block, ensure_ascii=False)
                + "</script>"
            )
    return "\n  ".join(parts)


def load_posts() -> list[dict]:
    posts: list[dict] = []
    base_date = date(2026, 1, 8)
    idx = 0

    # Topic 1–3: docx
    for topic_num, folder, cat_slug in [
        (1, "topic 1", "strength-training"),
        (2, "topic 2", "group-fitness"),
        (3, "topic 3", "kids-fitness"),
    ]:
        files = sorted((ROOT / folder).glob("*.docx"))
        for f in files:
            paras = docx_paragraphs(f)
            title, subtitle, body_html, toc = paragraphs_to_html(paras)
            # Prefer filename-derived slug without topic prefixes (keep inner 1-1 etc.)
            raw = f.stem
            raw = re.sub(r"^T[23]-\d+-", "", raw)
            raw = re.sub(r"^\d{2}-", "", raw)
            slug = slugify(raw)
            pub = base_date + timedelta(days=idx * 3)
            idx += 1
            full_text = "\n".join(paras)
            desc = subtitle if subtitle else full_text[len(title) :].strip()[:155]
            desc = re.sub(r"\s+", " ", desc).strip()
            if len(desc) > 155:
                desc = desc[:152].rsplit(" ", 1)[0] + "…"
            posts.append(
                {
                    "slug": slug,
                    "title": title,
                    "subtitle": subtitle,
                    "description": desc,
                    "body_html": body_html,
                    "toc": toc,
                    "category": cat_slug,
                    "source": str(f.relative_to(ROOT)),
                    "date": pub.isoformat(),
                    "read_minutes": estimate_read_minutes(full_text),
                    "keywords": f"{CATEGORIES[cat_slug]['keywords']}, {title.lower()}",
                }
            )

    # Topic 4: markdown
    for f in sorted((ROOT / "topic 4").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        paras = md_to_paragraphs(text)
        title, subtitle, body_html, toc = paragraphs_to_html(paras)
        # Better markdown body: convert properly from original
        body_html, toc = md_body_html(text)
        if paras:
            title = re.sub(r"^#+\s*", "", paras[0])
            subtitle = paras[1] if len(paras) > 1 and not paras[1].startswith("#") else ""
            # For md, first non-heading paragraph as subtitle if needed
            if not subtitle:
                for p in paras[1:]:
                    if len(p) > 80:
                        subtitle = p[:140] + ("…" if len(p) > 140 else "")
                        break
        raw = re.sub(r"^\d+-", "", f.stem)
        slug = slugify(raw)
        pub = base_date + timedelta(days=idx * 3)
        idx += 1
        desc = re.sub(r"\s+", " ", subtitle or title)[:155]
        posts.append(
            {
                "slug": slug,
                "title": title,
                "subtitle": subtitle,
                "description": desc,
                "body_html": body_html,
                "toc": toc,
                "category": "race-endurance",
                "source": str(f.relative_to(ROOT)),
                "date": pub.isoformat(),
                "read_minutes": estimate_read_minutes(text),
                "keywords": f"{CATEGORIES['race-endurance']['keywords']}, {title.lower()}",
            }
        )

    # ensure unique slugs
    seen: dict[str, int] = {}
    for p in posts:
        s = p["slug"]
        if s in seen:
            seen[s] += 1
            p["slug"] = f"{s}-{seen[s]}"
        else:
            seen[s] = 1
    return posts


def md_body_html(text: str) -> tuple[str, list[str]]:
    """Convert markdown article body (skip H1) to HTML."""
    lines = text.splitlines()
    parts: list[str] = []
    toc: list[str] = []
    i = 0
    # skip leading blank / H1
    while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("# ")):
        i += 1
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            parts.append("</ul>")
            in_list = False

    para_buf: list[str] = []

    def flush_para():
        nonlocal para_buf
        if para_buf:
            joined = " ".join(para_buf)
            joined = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", joined)
            parts.append(f"<p>{joined}</p>")
            para_buf = []

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if not s:
            flush_para()
            close_list()
            i += 1
            continue
        if s.startswith("## "):
            flush_para()
            close_list()
            heading = s[3:].strip()
            hid = slugify(heading)
            toc.append(heading)
            parts.append(f'<h2 id="{html.escape(hid)}">{html.escape(heading)}</h2>')
            i += 1
            continue
        if s.startswith("### "):
            flush_para()
            close_list()
            heading = s[4:].strip()
            hid = slugify(heading)
            toc.append(heading)
            parts.append(f'<h3 id="{html.escape(hid)}">{html.escape(heading)}</h3>')
            i += 1
            continue
        m = re.match(r"^[-*]\s+(.*)$", s) or re.match(r"^\d+\.\s+(.*)$", s)
        if m:
            flush_para()
            if not in_list:
                parts.append("<ul>")
                in_list = True
            item = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", m.group(1))
            parts.append(f"<li>{item}</li>")
            i += 1
            continue
        close_list()
        para_buf.append(re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s))
        i += 1
    flush_para()
    close_list()
    return "\n".join(parts), toc


def render_post(post: dict, all_posts: list[dict]) -> str:
    depth = 1
    prefix, assets, header, footer, home = chrome(depth)
    cat = CATEGORIES[post["category"]]
    canonical = f"{SITE_URL}/blog/{post['slug']}.html"
    related = [p for p in all_posts if p["category"] == post["category"] and p["slug"] != post["slug"]][:3]
    if len(related) < 3:
        extra = [p for p in all_posts if p["slug"] != post["slug"] and p not in related]
        related.extend(extra[: 3 - len(related)])

    toc_html = ""
    if post["toc"]:
        items = "".join(
            f'<li><a href="#{html.escape(slugify(h))}">{html.escape(h)}</a></li>' for h in post["toc"]
        )
        toc_html = f'<aside class="blog-toc" aria-label="Table of contents"><h2>Table of contents</h2><ol>{items}</ol></aside>'

    related_html = "".join(
        f"""<a class="blog-related-card" href="{html.escape(r['slug'])}.html">
          <span class="blog-card-cat">{html.escape(CATEGORIES[r['category']]['short'])}</span>
          <h3>{html.escape(r['title'])}</h3>
          <p>{html.escape(r['description'][:120])}…</p>
        </a>"""
        for r in related
    )

    json_ld = [
        {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post["title"],
            "description": post["description"],
            "datePublished": post["date"],
            "dateModified": post["date"],
            "author": {"@type": "Organization", "name": SITE_NAME},
            "publisher": {
                "@type": "Organization",
                "name": SITE_NAME,
                "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/assets/fitness-gurukul-logo.png"},
            },
            "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
            "articleSection": cat["name"],
            "keywords": post["keywords"],
            "wordCount": len(re.findall(r"\w+", post["title"] + " " + post["subtitle"] + " " + re.sub(r"<[^>]+>", "", post["body_html"]))),
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{SITE_URL}/blog.html"},
                {"@type": "ListItem", "position": 3, "name": cat["name"], "item": f"{SITE_URL}/blog.html#{post['category']}"},
                {"@type": "ListItem", "position": 4, "name": post["title"], "item": canonical},
            ],
        },
    ]

    head = seo_head(
        title=f"{post['title']} | {SITE_NAME} Blog",
        description=post["description"],
        canonical=canonical,
        keywords=post["keywords"],
        og_type="article",
        depth=depth,
        json_ld=json_ld,
        published=post["date"],
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  {head}
</head>
<body class="blog-page blog-article-page">
<div class="scroll-progress" id="scrollProgress" aria-hidden="true"></div>
{header}
<main>
  <article class="blog-article" itemscope itemtype="https://schema.org/BlogPosting">
    <header class="blog-article-hero">
      <div class="blog-article-hero-inner">
        <nav class="blog-breadcrumb" aria-label="Breadcrumb">
          <a href="{home}">Home</a>
          <span>/</span>
          <a href="{prefix}blog.html">Blog</a>
          <span>/</span>
          <a href="{prefix}blog.html#{post['category']}">{html.escape(cat['name'])}</a>
        </nav>
        <span class="blog-card-cat">{html.escape(cat['name'])}</span>
        <h1 itemprop="headline">{html.escape(post['title'])}</h1>
        <p class="blog-article-dek" itemprop="description">{html.escape(post['subtitle'])}</p>
        <div class="blog-article-meta">
          <span>By <span itemprop="author">{html.escape(AUTHOR)}</span></span>
          <span aria-hidden="true">·</span>
          <time datetime="{post['date']}" itemprop="datePublished">{post['date']}</time>
          <span aria-hidden="true">·</span>
          <span>{post['read_minutes']} min read</span>
        </div>
      </div>
    </header>
    <div class="blog-article-layout">
      {toc_html}
      <div class="blog-article-body" itemprop="articleBody">
        {post['body_html']}
        <div class="blog-cta">
          <h2>Ready to train with a plan?</h2>
          <p>Get a free consultation with Fitness Gurukul coaches in Hyderabad — or start online through the app.</p>
          <div class="blog-cta-actions">
            <a class="primary-button" href="{prefix}book-consultation.html">Book Free Consultation</a>
            <a class="ghost-button" href="{prefix}services.html">Explore Programs</a>
          </div>
        </div>
      </div>
    </div>
  </article>
  <section class="blog-related section-shell">
    <div class="page-shell">
      <div class="section-heading">
        <div>
          <span class="section-kicker">Keep reading</span>
          <h2>Related articles</h2>
        </div>
      </div>
      <div class="blog-related-grid">
        {related_html}
      </div>
    </div>
  </section>
</main>
{WA_FAB}
{footer}
</body>
</html>
"""


def post_card(post: dict, prefix: str = "blog/") -> str:
    cat = CATEGORIES[post["category"]]
    return f"""<a class="blog-card" href="{prefix}{html.escape(post['slug'])}.html" data-category="{post['category']}">
  <div class="blog-card-top">
    <span class="blog-card-cat">{html.escape(cat['short'])}</span>
    <span class="blog-card-meta">{post['read_minutes']} min · {post['date']}</span>
  </div>
  <h3>{html.escape(post['title'])}</h3>
  <p>{html.escape(post['description'])}</p>
  <span class="blog-card-more">Read article →</span>
</a>"""


def placeholder_card(title: str, category_name: str) -> str:
    return f"""<article class="blog-card blog-card-placeholder" aria-label="Coming soon">
  <div class="blog-card-top">
    <span class="blog-card-cat">{html.escape(category_name)}</span>
    <span class="blog-card-meta">Coming soon</span>
  </div>
  <h3>{html.escape(title)}</h3>
  <p>This article is a placeholder reserved for future SEO content in this topic.</p>
  <span class="blog-card-more">Placeholder</span>
</article>"""


def render_index(posts: list[dict]) -> str:
    depth = 0
    prefix, assets, header, footer, home = chrome(depth)
    canonical = f"{SITE_URL}/blog.html"
    item_list = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"Explore Blogs | {SITE_NAME}",
        "description": "Fitness tips, training guides, kids fitness, and race prep from Fitness Gurukul coaches in Hyderabad.",
        "url": canonical,
        "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": SITE_URL},
        "about": [{"@type": "Thing", "name": c["name"]} for c in CATEGORIES.values()],
    }
    head = seo_head(
        title=f"Explore Blogs | Fitness Tips & Training Guides | {SITE_NAME}",
        description="Explore Fitness Gurukul blogs on strength training, group fitness, kids fitness, and race endurance — practical guides for Hyderabad and beyond.",
        canonical=canonical,
        keywords="fitness blog Hyderabad, strength training tips, kids fitness, marathon training, group yoga, Fitness Gurukul blog",
        depth=0,
        json_ld=[item_list],
    )

    cat_pills = ['<button type="button" class="blog-filter active" data-filter="all">All</button>']
    for slug, cat in CATEGORIES.items():
        cat_pills.append(
            f'<button type="button" class="blog-filter" data-filter="{slug}">{html.escape(cat["name"])}</button>'
        )
    for ph in PLACEHOLDER_CATEGORIES:
        cat_pills.append(
            f'<button type="button" class="blog-filter" data-filter="{ph["slug"]}">{html.escape(ph["name"])}</button>'
        )

    sections = []
    for slug, cat in CATEGORIES.items():
        cards = "\n".join(post_card(p) for p in posts if p["category"] == slug)
        # one empty placeholder slot per live category
        cards += "\n" + placeholder_card(f"More {cat['name']} guides coming soon", cat["name"])
        sections.append(
            f"""<section class="blog-category-block" id="{slug}" data-category-section="{slug}">
  <div class="blog-category-head">
    <h2>{html.escape(cat['name'])}</h2>
    <p>{html.escape(cat['description'])}</p>
  </div>
  <div class="blog-grid">{cards}</div>
</section>"""
        )

    for ph in PLACEHOLDER_CATEGORIES:
        cards = "\n".join(placeholder_card(t, ph["name"]) for t in ph["placeholders"])
        # extra empty slot
        cards += "\n" + placeholder_card("Your next article title goes here", ph["name"])
        sections.append(
            f"""<section class="blog-category-block blog-category-placeholder-block" id="{ph['slug']}" data-category-section="{ph['slug']}">
  <div class="blog-category-head">
    <h2>{html.escape(ph['name'])}</h2>
    <p>{html.escape(ph['description'])}</p>
  </div>
  <div class="blog-grid">{cards}</div>
</section>"""
        )

    featured = posts[:6]
    featured_html = "\n".join(post_card(p) for p in featured)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  {head}
</head>
<body class="blog-page blog-index-page">
<div class="scroll-progress" id="scrollProgress" aria-hidden="true"></div>
{header}
<main>
  <section class="blog-hero">
    <div class="blog-hero-inner">
      <span class="section-kicker">Fitness Gurukul Blog</span>
      <h1>Explore Blogs</h1>
      <p>Practical training guides, group fitness ideas, kids programs, and race prep — written to help you train smarter in Hyderabad and beyond.</p>
      <form class="blog-search" role="search" onsubmit="return false;">
        <label class="sr-only" for="blogSearch">Search blogs</label>
        <input id="blogSearch" type="search" placeholder="Search articles…" autocomplete="off" />
      </form>
      <div class="blog-filters" role="tablist" aria-label="Blog categories">
        {''.join(cat_pills)}
      </div>
    </div>
  </section>

  <section class="section-shell blog-featured" id="featured">
    <div class="page-shell">
      <div class="section-heading">
        <div>
          <span class="section-kicker">Featured</span>
          <h2>Latest from the coaches</h2>
        </div>
      </div>
      <div class="blog-grid blog-featured-grid">
        {featured_html}
      </div>
    </div>
  </section>

  <section class="section-shell">
    <div class="page-shell blog-categories">
      {''.join(sections)}
    </div>
  </section>

  <section class="blog-newsletter section-shell">
    <div class="page-shell blog-newsletter-inner">
      <div>
        <span class="section-kicker">Stay consistent</span>
        <h2>Want a plan, not just another article?</h2>
        <p>Book a free consultation and get training built around your body, schedule, and goals.</p>
      </div>
      <a class="primary-button" href="book-consultation.html">Book Free Consultation</a>
    </div>
  </section>
</main>
{WA_FAB}
{footer}
<script>
(function () {{
  var search = document.getElementById('blogSearch');
  var filters = document.querySelectorAll('.blog-filter');
  var cards = document.querySelectorAll('.blog-card');
  var sections = document.querySelectorAll('[data-category-section]');
  var active = 'all';

  function apply() {{
    var q = (search.value || '').trim().toLowerCase();
    sections.forEach(function (sec) {{
      var cat = sec.getAttribute('data-category-section');
      var showSection = active === 'all' || active === cat;
      var visible = 0;
      sec.querySelectorAll('.blog-card').forEach(function (card) {{
        var text = (card.textContent || '').toLowerCase();
        var matchCat = active === 'all' || card.getAttribute('data-category') === active || (active === cat && card.classList.contains('blog-card-placeholder'));
        if (active !== 'all' && active !== cat && !card.classList.contains('blog-card-placeholder')) {{
          matchCat = card.getAttribute('data-category') === active;
        }}
        if (active !== 'all') {{
          matchCat = (card.getAttribute('data-category') === active) || (card.classList.contains('blog-card-placeholder') && cat === active);
        }}
        var matchQ = !q || text.indexOf(q) !== -1;
        var on = matchCat && matchQ && (active === 'all' ? true : (cat === active));
        if (active === 'all') on = matchQ;
        card.hidden = !on;
        if (on) visible++;
      }});
      sec.hidden = active !== 'all' && cat !== active ? true : visible === 0 && !!q;
      if (active !== 'all') sec.hidden = cat !== active;
    }});
    var featured = document.getElementById('featured');
    if (featured) featured.hidden = active !== 'all' || !!q;
  }}

  filters.forEach(function (btn) {{
    btn.addEventListener('click', function () {{
      active = btn.getAttribute('data-filter') || 'all';
      filters.forEach(function (b) {{ b.classList.toggle('active', b === btn); }});
      apply();
      if (active !== 'all') {{
        var el = document.getElementById(active);
        if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}
    }});
  }});
  search.addEventListener('input', apply);

  if (location.hash) {{
    var h = location.hash.replace('#', '');
    var match = document.querySelector('.blog-filter[data-filter="' + h + '"]');
    if (match) match.click();
  }}
}})();
</script>
</body>
</html>
"""


def write_sitemap(posts: list[dict]) -> None:
    urls = [
        ("/", "1.0", "weekly"),
        ("/blog.html", "0.9", "daily"),
        ("/services.html", "0.8", "weekly"),
        ("/coaches.html", "0.8", "weekly"),
        ("/events.html", "0.7", "weekly"),
        ("/tools.html", "0.7", "monthly"),
        ("/about.html", "0.6", "monthly"),
        ("/contact.html", "0.6", "monthly"),
        ("/book-consultation.html", "0.8", "monthly"),
        ("/testimonials.html", "0.6", "monthly"),
        ("/transformation-challenge.html", "0.7", "monthly"),
    ]
    for p in posts:
        urls.append((f"/blog/{p['slug']}.html", "0.7", "monthly"))

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    today = date.today().isoformat()
    for path, pri, freq in urls:
        parts.append("  <url>")
        parts.append(f"    <loc>{SITE_URL}{path}</loc>")
        parts.append(f"    <lastmod>{today}</lastmod>")
        parts.append(f"    <changefreq>{freq}</changefreq>")
        parts.append(f"    <priority>{pri}</priority>")
        parts.append("  </url>")
    parts.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_robots() -> None:
    (ROOT / "robots.txt").write_text(
        f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
""",
        encoding="utf-8",
    )


def write_manifest(posts: list[dict]) -> None:
    data = [
        {
            "slug": p["slug"],
            "title": p["title"],
            "description": p["description"],
            "category": p["category"],
            "date": p["date"],
            "read_minutes": p["read_minutes"],
            "url": f"blog/{p['slug']}.html",
        }
        for p in posts
    ]
    (BLOG_DIR / "posts.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")



def inject_seo_after_footer(html_path: Path, prefix: str = "") -> None:
    """Ensure crawlable blog SEO link directory sits below the page footer."""
    import json as _json
    posts = _json.loads((BLOG_DIR / "posts.json").read_text(encoding="utf-8"))
    cats = [
        ("strength-training", "Strength & Training"),
        ("group-fitness", "Group Fitness"),
        ("kids-fitness", "Kids Fitness"),
        ("race-endurance", "Race & Endurance"),
    ]
    blog = f"{prefix}blog.html"
    parts = ['<section class="footer-seo" aria-label="Blog and SEO links">', '<div class="footer-seo-inner">']
    parts.append('<div class="footer-seo-head"><h2>Explore fitness guides</h2>')
    parts.append(f'<p>Browse Fitness Gurukul blogs on strength training, group fitness, kids programs, and race prep. <a href="{blog}">View all blogs</a></p></div>')
    parts.append('<div class="footer-seo-cats">')
    for slug, name in cats:
        parts.append(f'<div class="footer-seo-col"><h3><a href="{blog}#{slug}">{html.escape(name)}</a></h3><ul>')
        for post in posts:
            if post["category"] != slug:
                continue
            parts.append(f'<li><a href="{prefix}{html.escape("blog/" + post["slug"] + ".html")}">{html.escape(post["title"])}</a></li>')
        parts.append("</ul></div>")
    parts.append("</div></div></section>")
    block = "\n".join(parts)
    text = html_path.read_text(encoding="utf-8")
    text = re.sub(r'\n?<section class="footer-seo"[\s\S]*?</section>\n?', "\n", text)
    idx = text.rfind("</footer>")
    if idx < 0:
        return
    end = idx + len("</footer>")
    html_path.write_text(text[:end] + "\n" + block + "\n" + text[end:], encoding="utf-8")

def main() -> None:
    BLOG_DIR.mkdir(exist_ok=True)
    # clear old generated html posts but keep folder
    for old in BLOG_DIR.glob("*.html"):
        old.unlink()

    posts = load_posts()
    print(f"Loaded {len(posts)} posts")

    for post in posts:
        path = BLOG_DIR / f"{post['slug']}.html"
        path.write_text(render_post(post, posts), encoding="utf-8")
        print("  wrote", path.relative_to(ROOT))

    index = ROOT / "blog.html"
    index.write_text(render_index(posts), encoding="utf-8")
    print("  wrote blog.html")

    write_manifest(posts)
    write_sitemap(posts)
    write_robots()
    # SEO footers on generated pages
    inject_seo_after_footer(index, "")
    for post in posts:
        inject_seo_after_footer(BLOG_DIR / f"{post['slug']}.html", "../")
    # write seo-groups.json for runtime footer injector
    groups = [
        {
            "slug": slug,
            "name": name,
            "posts": [{"title": p["title"], "url": f"blog/{p['slug']}.html"} for p in posts if p["category"] == slug],
        }
        for slug, name in [
            ("strength-training", "Strength & Training"),
            ("group-fitness", "Group Fitness"),
            ("kids-fitness", "Kids Fitness"),
            ("race-endurance", "Race & Endurance"),
        ]
    ]
    (BLOG_DIR / "seo-groups.json").write_text(json.dumps(groups, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("  wrote blog/posts.json, sitemap.xml, robots.txt, seo footers")


if __name__ == "__main__":
    main()
