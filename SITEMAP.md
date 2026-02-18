# Sitemap Update Process

When you add a new API page or blog post to the catalog, update `sitemap.xml` so search engines can discover it.

## Steps

1. **Open** `sitemap.xml`.

2. **Add a new `<url>` block** before the closing `</urlset>`:

   ```xml
   <url>
     <loc>https://precisionsolutionstech-netizen.github.io/api-catalog/apis/YOUR-PAGE.html</loc>
     <lastmod>YYYY-MM-DD</lastmod>
     <changefreq>monthly</changefreq>
     <priority>0.8</priority>
   </url>
   ```

   - Use the full base URL: `https://precisionsolutionstech-netizen.github.io/api-catalog/`
   - For API pages: path is `apis/your-page.html`.
   - For blog: path is `blog/your-post.html` (use `priority` 0.7 if you prefer).
   - Set `lastmod` to today’s date (ISO YYYY-MM-DD).

3. **Optional: update `lastmod`** on existing entries when you make meaningful content changes to a page.

## Automation (future)

You can add a small script (e.g. Node or Python) that:

- Scans `apis/*.html` and `blog/*.html`.
- Reads `sitemap.xml`, adds any missing URLs, and updates `lastmod` for modified files.
- Run it before deploy or in CI.

For now, manual updates are sufficient.
