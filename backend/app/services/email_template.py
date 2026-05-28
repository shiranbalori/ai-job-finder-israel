"""Modern HTML email templates for daily job digest."""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any


def _skill_tags(skills: list[str]) -> str:
    if not skills:
        return ""
    return "".join(
        f'<span style="display:inline-block;background:#ecfdf5;color:#047857;padding:4px 10px;'
        f'border-radius:999px;font-size:12px;margin:2px 4px 2px 0;">{escape(s)}</span>'
        for s in skills[:6]
    )


def render_digest_html(
    matches: list[dict[str, Any]],
    *,
    recipient: str,
    min_score: int,
    language: str = "en",
) -> str:
    """Build responsive HTML digest from match dicts (with nested job info)."""
    today = datetime.utcnow().strftime("%B %d, %Y")
    title = "Your daily AI job matches" if language != "he" else "משרות AI יומיות עבורך"
    subtitle = (
        f"Top roles scoring {min_score}%+ — {today}"
        if language != "he"
        else f"משרות מעל {min_score}% — {today}"
    )

    cards: list[str] = []
    for m in matches:
        job = m.get("job") or {}
        score = float(m.get("match_score", 0))
        matched_skills = m.get("matched_skills") or []
        apply_url = job.get("url") or "#"
        score_color = "#059669" if score >= 70 else "#2563eb" if score >= 55 else "#d97706"

        cards.append(
            f"""
            <tr>
              <td style="padding:0 0 16px 0;">
                <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
                  style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;">
                  <tr>
                    <td style="padding:20px 24px;">
                      <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                        <tr>
                          <td>
                            <p style="margin:0;font-size:18px;font-weight:700;color:#0f172a;">
                              {escape(str(job.get("title", "Job")))}
                            </p>
                            <p style="margin:6px 0 0;font-size:14px;color:#64748b;">
                              {escape(str(job.get("company", "")))} · {escape(str(job.get("location", "")))}
                            </p>
                          </td>
                          <td align="right" style="vertical-align:top;">
                            <span style="display:inline-block;background:{score_color};color:#fff;
                              font-weight:700;font-size:14px;padding:8px 14px;border-radius:999px;">
                              {score:.0f}%
                            </span>
                          </td>
                        </tr>
                      </table>
                      <p style="margin:14px 0 10px;font-size:13px;line-height:1.5;color:#475569;">
                        {escape(str(m.get("match_reason", ""))[:220])}
                      </p>
                      <div style="margin:8px 0 16px;">{_skill_tags(matched_skills)}</div>
                      <a href="{escape(str(apply_url))}" target="_blank"
                        style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                        color:#ffffff;text-decoration:none;font-weight:600;font-size:14px;
                        padding:10px 20px;border-radius:10px;">
                        {"Apply now" if language != "he" else "הגש מועמדות"}
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            """
        )

    jobs_html = "".join(cards) if cards else (
        "<p style='color:#64748b;'>No new matches today.</p>"
    )

    return f"""<!DOCTYPE html>
<html lang="{language}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#f1f5f9;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" role="presentation" style="max-width:600px;width:100%;">
        <tr>
          <td style="padding:0 0 24px;text-align:center;">
            <p style="margin:0;font-size:12px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#6366f1;">
              AI Job Finder Israel
            </p>
            <h1 style="margin:8px 0 4px;font-size:28px;color:#0f172a;">{escape(title)}</h1>
            <p style="margin:0;font-size:14px;color:#64748b;">{escape(subtitle)}</p>
            <p style="margin:8px 0 0;font-size:12px;color:#94a3b8;">To: {escape(recipient)}</p>
          </td>
        </tr>
        {jobs_html}
        <tr>
          <td style="padding:24px 0 0;text-align:center;font-size:12px;color:#94a3b8;">
            Sent by AI Job Finder Israel · Adjust preferences in Settings
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def render_digest_plain(matches: list[dict[str, Any]], *, min_score: int) -> str:
    lines = [
        f"AI Job Finder Israel — Daily Digest ({datetime.utcnow().strftime('%Y-%m-%d')})",
        f"Matches scoring {min_score}%+:",
        "",
    ]
    for m in matches:
        job = m.get("job") or {}
        lines.append(f"• {job.get('title')} @ {job.get('company')} — {m.get('match_score', 0):.0f}%")
        location = job.get("location")
        if location:
            lines.append(f"  Location: {location}")
        skills = ", ".join((m.get("matched_skills") or [])[:5])
        if skills:
            lines.append(f"  Skills: {skills}")
        if job.get("url"):
            lines.append(f"  Apply: {job['url']}")
        lines.append("")
    return "\n".join(lines)
