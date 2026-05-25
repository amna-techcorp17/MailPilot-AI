import html
import re
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.classifier import classify_email, detect_urgency
from src.followup_generator import generate_followup
from src.llm import has_api_key
from src.reply_generator import generate_reply
from src.summarizer import summarize_email
from src.task_extractor import extract_tasks
from src.tone_manager import describe_tone, get_tones
from src.utils import EmailAnalysis


APP_DIR = Path(__file__).parent
STYLE_PATH = APP_DIR / "assets" / "styles.css"
SAMPLE_EMAIL = (
    "Hi Amna,\n\nCan we schedule a meeting next Tuesday to review the revised proposal "
    "and updated project timeline? Please also send the latest pricing sheet before the call.\n\n"
    "Thanks,\nJohn"
)

DEMO_EMAILS = {
    "Complaint Email": (
        "Hello,\n\nMy order has not arrived yet and I need an update urgently. "
        "This was supposed to be delivered two days ago, and I have not received any tracking update.\n\n"
        "Please confirm the delivery status today.\n\nThanks,\nSarah"
    ),
    "Meeting Request": SAMPLE_EMAIL,
    "Client Follow-up": (
        "Hi Amna,\n\nI wanted to follow up on the proposal we discussed last week. "
        "Can you share the revised scope and timeline before Friday so we can review internally?\n\n"
        "Best,\nMichael"
    ),
    "Sales Inquiry": (
        "Hi,\n\nWe are exploring AI automation for our customer support team and would like to know your pricing, "
        "implementation timeline, and whether you offer a demo for agencies.\n\nRegards,\nNadia"
    ),
}


st.set_page_config(
    page_title="MailPilot AI",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css() -> None:
    if STYLE_PATH.exists():
        st.markdown(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def status_class(urgency: str) -> str:
    return {
        "Urgent": "urgent",
        "Medium": "medium",
        "Low Priority": "low",
    }.get(urgency, "medium")


def category_class(category: str) -> str:
    normalized = category.lower()
    if "complaint" in normalized:
        return "complaint"
    if "meeting" in normalized:
        return "meeting"
    if "sales" in normalized:
        return "sales"
    if "follow" in normalized:
        return "follow"
    if "support" in normalized:
        return "support"
    return "casual"


def category_icon(category: str) -> str:
    normalized = category.lower()
    if "complaint" in normalized:
        return "!"
    if "meeting" in normalized:
        return "CAL"
    if "sales" in normalized:
        return "$"
    if "follow" in normalized:
        return "NEXT"
    if "support" in normalized:
        return "HELP"
    return "OK"


def urgency_icon(urgency: str) -> str:
    return {
        "Urgent": "HIGH",
        "Medium": "MED",
        "Low Priority": "LOW",
    }.get(urgency, "MED")


def estimate_sentiment(email: str) -> str:
    text = email.lower()
    negative = ["angry", "unacceptable", "not arrived", "refund", "urgent", "issue", "problem", "complaint"]
    positive = ["thank", "great", "happy", "appreciate", "interested", "excited"]
    if any(word in text for word in negative):
        return "Concerned"
    if any(word in text for word in positive):
        return "Positive"
    return "Neutral"


def response_needed(email: str, category: str) -> str:
    text = email.lower()
    if "?" in email or any(word in text for word in ["please", "can you", "could you", "need", "send", "share", "schedule"]):
        return "Yes"
    if category in {"Complaint", "Support Request", "Sales Inquiry", "Meeting Request", "Follow-up"}:
        return "Yes"
    return "Review"


def confidence_score(email: str, analysis: EmailAnalysis) -> int:
    score = 88
    if len(email) > 160:
        score += 3
    if analysis.category != "Casual":
        score += 2
    if analysis.tasks and "No clear action items" not in analysis.tasks:
        score += 2
    if analysis.urgency == "Urgent":
        score += 1
    return min(score, 97)


def update_activity(category: str) -> None:
    activity = st.session_state.get("recent_activity", [])
    item = f"{category} processed"
    activity = [item] + [entry for entry in activity if entry != item]
    st.session_state["recent_activity"] = activity[:4]


def metric_card(label: str, value: str, variant: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card {variant}">
            <span>{html.escape(label)}</span>
            <strong>{html.escape(value)}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def workspace_card(title: str, value: str, icon: str, variant: str = "") -> None:
    st.markdown(
        f"""
        <div class="workspace-card {variant}">
            <div class="workspace-card-title">
                <span>{html.escape(icon)}</span>
                <p>{html.escape(title)}</p>
            </div>
            <strong>{html.escape(value)}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def smart_badge(label: str, value: str, variant: str) -> None:
    st.markdown(
        f"""
        <div class="smart-badge {variant}">
            <span>{html.escape(label)}</span>
            <strong>{html.escape(value)}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def analytics_panel(email: str, analysis: EmailAnalysis) -> None:
    confidence = confidence_score(email, analysis)
    analytics = [
        ("Sentiment", estimate_sentiment(email)),
        ("Response Needed", response_needed(email, analysis.category)),
        ("Estimated Reply Time", "2 mins" if len(email) < 700 else "4 mins"),
        ("Reply Confidence", f"{confidence}%"),
    ]
    cards = "".join(
        f'<div class="analytics-card"><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>'
        for label, value in analytics
    )
    st.markdown(
        f'<div class="section-label">Email Analytics</div><div class="analytics-grid">{cards}</div>',
        unsafe_allow_html=True,
    )


def compact_preview(text: str, limit: int = 140) -> str:
    clean = " ".join((text or "").split())
    clean = re.sub(r"[*_`#>]+", "", clean)
    clean = re.sub(r"^[-•]\s*", "", clean)
    clean = clean.replace("Summary:", "").replace("Follow-up plan:", "").strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rstrip() + "..."


def result_cards_panel(analysis: EmailAnalysis) -> None:
    cards = [
        ("Email Summary", compact_preview(analysis.summary, 150), "SUM"),
        ("Tasks Extracted", compact_preview(analysis.tasks, 130), "TASK"),
        ("Follow-up Suggestion", compact_preview(analysis.followup, 140), "NEXT"),
    ]
    html_cards = "".join(
        f'<div class="result-card"><div class="result-card-head"><span>{html.escape(icon)}</span><p>{html.escape(title)}</p></div><strong>{html.escape(value)}</strong></div>'
        for title, value, icon in cards
    )
    st.markdown(f'<div class="result-card-grid">{html_cards}</div>', unsafe_allow_html=True)


def copy_block(title: str, content: str, key: str) -> None:
    escaped_title = html.escape(title)
    escaped_content = html.escape(content)
    components.html(
        f"""
        <style>
        html, body {{
            margin: 0;
            background: transparent;
            color: #f8fafc;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        .copy-shell {{
            color: #f8fafc;
            background: rgba(15, 23, 42, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.24);
            border-radius: 8px;
            overflow: hidden;
        }}
        .copy-head {{
            height: 46px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 14px 0 16px;
            background: rgba(30, 41, 59, 0.96);
            border-bottom: 1px solid rgba(148, 163, 184, 0.18);
        }}
        .copy-head button {{
            height: 30px;
            padding: 0 12px;
            border: 1px solid rgba(20, 184, 166, 0.55);
            border-radius: 8px;
            background: rgba(20, 184, 166, 0.2);
            color: #ccfbf1;
            font-weight: 700;
            cursor: pointer;
        }}
        .copy-shell pre {{
            margin: 0;
            min-height: 228px;
            padding: 16px;
            white-space: pre-wrap;
            line-height: 1.55;
            color: #e2e8f0;
            font-size: 0.94rem;
        }}
        </style>
        <div class="copy-shell">
            <div class="copy-head">
                <strong>{escaped_title}</strong>
                <button id="btn-{key}" type="button">Copy</button>
            </div>
            <pre id="text-{key}">{escaped_content}</pre>
        </div>
        <script>
        const button = document.getElementById("btn-{key}");
        const text = document.getElementById("text-{key}");
        button.addEventListener("click", async () => {{
            await navigator.clipboard.writeText(text.innerText);
            button.innerText = "Copied";
            setTimeout(() => button.innerText = "Copy", 1300);
        }});
        </script>
        """,
        height=330,
        scrolling=True,
    )


def analyze_email(email: str, tone: str, temperature: float) -> EmailAnalysis:
    category = classify_email(email)
    urgency = detect_urgency(email)
    summary = summarize_email(email, temperature=temperature)
    reply = generate_reply(email=email, summary=summary, tone=tone, temperature=temperature)
    followup = generate_followup(email=email, summary=summary, temperature=temperature)
    tasks = extract_tasks(email, temperature=temperature)

    return EmailAnalysis(
        category=category,
        urgency=urgency,
        summary=summary,
        reply=reply,
        followup=followup,
        tasks=tasks,
        demo_mode=not has_api_key(),
    )


def load_template_email(template_name: str) -> None:
    st.session_state["email_input"] = DEMO_EMAILS[template_name]


def load_sample_email() -> None:
    load_template_email("Meeting Request")


def shorten_reply() -> None:
    analysis = st.session_state.get("analysis")
    if not analysis:
        return
    paragraphs = [part.strip() for part in analysis.reply.split("\n\n") if part.strip()]
    shortened = "\n\n".join(paragraphs[:3])
    if len(shortened) > 700:
        shortened = shortened[:697].rstrip() + "..."
    st.session_state["analysis"] = analysis.model_copy(update={"reply": shortened})


def make_reply_tone(tone_name: str) -> None:
    analysis = st.session_state.get("analysis")
    email = st.session_state.get("last_email", "")
    temperature = st.session_state.get("last_temperature", 0.4)
    if not analysis or not email:
        return
    reply = generate_reply(email=email, summary=analysis.summary, tone=tone_name, temperature=temperature)
    st.session_state["analysis"] = analysis.model_copy(update={"reply": reply})
    st.session_state["last_tone"] = tone_name


def regenerate_reply() -> None:
    analysis = st.session_state.get("analysis")
    email = st.session_state.get("last_email", "")
    tone = st.session_state.get("last_tone", "Professional")
    temperature = min(st.session_state.get("last_temperature", 0.4) + 0.1, 1.0)
    if not analysis or not email:
        return
    reply = generate_reply(email=email, summary=analysis.summary, tone=tone, temperature=temperature)
    st.session_state["analysis"] = analysis.model_copy(update={"reply": reply})


load_css()

st.sidebar.image(str(APP_DIR / "assets" / "logo.png"), width=58)
st.sidebar.title("MailPilot AI")
st.sidebar.caption("Smart Email Reply Assistant")

tone = st.sidebar.selectbox("Reply tone", get_tones(), index=0)
st.sidebar.info(describe_tone(tone))

st.sidebar.divider()
temperature = st.sidebar.slider(
    "Creativity",
    min_value=0.0,
    max_value=1.0,
    value=0.4,
    step=0.1,
    help="Lower values produce safer replies. Higher values make replies more varied.",
)

st.sidebar.divider()
st.sidebar.markdown('<div class="sidebar-label">Quick Load Examples</div>', unsafe_allow_html=True)
for template_name in DEMO_EMAILS:
    st.sidebar.button(
        template_name,
        use_container_width=True,
        on_click=load_template_email,
        args=(template_name,),
    )

st.sidebar.divider()
st.sidebar.markdown('<div class="sidebar-label">Recent Activity</div>', unsafe_allow_html=True)
activity = st.session_state.get("recent_activity", [])
if activity:
    for entry in activity:
        st.sidebar.markdown(f'<div class="activity-item">{html.escape(entry)}</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div class="activity-item muted">No emails processed yet</div>', unsafe_allow_html=True)

st.sidebar.markdown(
    """
    <div class="coming-soon">
        <strong>AI Inbox Copilot</strong>
        <span>Coming soon</span>
        <p>Gmail integration, auto drafts, and smart inbox prioritization.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="hero">
        <div class="hero-particles">
            <span></span><span></span><span></span>
        </div>
        <div>
            <p class="eyebrow">AI productivity dashboard</p>
            <h1>MailPilot AI</h1>
            <p class="subhead">Summarize, classify, prioritize, and draft polished email replies in one focused workspace.</p>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([0.84, 1.16], gap="large")

with left:
    st.markdown('<div class="panel-title">Incoming Email</div>', unsafe_allow_html=True)
    email = st.text_area(
        "Paste email content",
        height=360,
        placeholder=(
            "Example: My order has not arrived yet and I need an update urgently. "
            "Can someone confirm the delivery status today?"
        ),
        label_visibility="collapsed",
        key="email_input",
    )

    action_col, sample_col = st.columns([0.62, 0.38])
    generate = action_col.button("Analyze & Draft Reply", type="primary", use_container_width=True)

    sample_col.button("Use Sample Email", use_container_width=True, on_click=load_sample_email)

with right:
    placeholder = st.empty()

    if not generate and "analysis" not in st.session_state:
        with placeholder.container():
            st.markdown('<div class="empty-state">Paste an email and generate an AI workspace.</div>', unsafe_allow_html=True)
    elif "analysis" in st.session_state:
        placeholder.empty()

    if generate:
        if not email.strip():
            st.error("Paste an email first.")
        else:
            steps = [
                "Detecting intent",
                "Classifying urgency",
                "Summarizing key points",
                "Drafting reply",
                "Extracting action items",
            ]
            workflow = st.empty()
            progress = st.progress(0, text="Analyzing email...")
            for index, step in enumerate(steps, start=1):
                done_steps = "".join(
                    f'<li class="done">✓ {html.escape(done)}</li>' for done in steps[: index - 1]
                )
                active_step = f'<li class="active">{html.escape(step)}<span class="typing-dots"></span></li>'
                queued_steps = "".join(
                    f'<li>{html.escape(waiting)}</li>' for waiting in steps[index:]
                )
                workflow.markdown(
                    f"""
                    <div class="workflow-card">
                        <div class="typing-line">Generating AI workspace<span class="typing-dots"></span></div>
                        <ul>{done_steps}{active_step}{queued_steps}</ul>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                progress.progress(index / len(steps), text=step)
                time.sleep(0.18)

            analysis = analyze_email(email, tone, temperature)
            st.session_state["analysis"] = analysis
            st.session_state["last_email"] = email
            st.session_state["last_tone"] = tone
            st.session_state["last_temperature"] = temperature
            update_activity(analysis.category)
            progress.empty()
            workflow.empty()

if "analysis" in st.session_state:
    analysis: EmailAnalysis = st.session_state["analysis"]
    last_email = st.session_state.get("last_email", email if "email" in locals() else "")
    with right:
        st.markdown('<div class="panel-title">AI Results</div>', unsafe_allow_html=True)

        badge_cols = st.columns([1, 1, 1])
        with badge_cols[0]:
            smart_badge(category_icon(analysis.category), analysis.category, category_class(analysis.category))
        with badge_cols[1]:
            smart_badge(urgency_icon(analysis.urgency), analysis.urgency, status_class(analysis.urgency))
        with badge_cols[2]:
            smart_badge("CONF", f"{confidence_score(last_email, analysis)}%", "confidence")

        tabs = st.tabs(["Summary", "Reply", "Tasks", "Follow-up"])

        with tabs[0]:
            copy_block("Summary", analysis.summary, "summary")

        with tabs[1]:
            copy_block("AI Reply", analysis.reply, "reply")
            st.markdown('<div class="quick-actions-label">Quick Actions</div>', unsafe_allow_html=True)
            action_cols = st.columns(4)
            action_cols[0].button("Shorten Reply", use_container_width=True, on_click=shorten_reply)
            action_cols[1].button("Make Formal", use_container_width=True, on_click=make_reply_tone, args=("Formal",))
            action_cols[2].button("Make Friendly", use_container_width=True, on_click=make_reply_tone, args=("Friendly",))
            action_cols[3].button("Regenerate", use_container_width=True, on_click=regenerate_reply)
            st.download_button(
                "Download Reply",
                data=analysis.reply,
                file_name="mailpilot-reply.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with tabs[2]:
            copy_block("Action Items", analysis.tasks, "tasks")

        with tabs[3]:
            copy_block("Follow-Up Plan", analysis.followup, "followup")

        result_cards_panel(analysis)
        analytics_panel(last_email, analysis)
