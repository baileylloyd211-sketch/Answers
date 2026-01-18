import random
from statistics import pstdev
import streamlit as st

st.set_page_config(page_title="Trifactor Diagnostic", layout="centered")

# ────────────────────────────────────────────────────────────── 
# Constants
# ──────────────────────────────────────────────────────────────

LENSES = ["Interpersonal", "Financial", "Big Picture"]

SCALE_LABELS = {
    0: "0 — Not at all / Never",
    1: "1 — Rarely",
    2: "2 — Sometimes",
    3: "3 — Often",
    4: "4 — Almost always",
}

VARIABLE_WEIGHTS = {
    "Baseline": 1.2,
    "Clarity": 1.1,
    "Resources": 1.1,
    "Boundaries": 1.1,
    "Execution": 1.2,
    "Feedback": 1.0,
}

# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def clamp(n, lo, hi):
    return max(lo, min(hi, n))


def zone_name(score: float) -> str:  # 0–100
    if score < 45:
        return "RED"
    if score < 70:
        return "YELLOW"
    return "GREEN"


def zone_message(zone: str) -> str:
    return {
        "RED": "broken — needs urgent attention",
        "YELLOW": "unstable — fragile under pressure",
        "GREEN": "solid — working well",
    }[zone]


def lens_focus(lens: str) -> str:
    return {
        "Interpersonal": "relationship tension, clarity, boundaries, execution",
        "Financial": "money stability, buffer, boundaries, execution",
        "Big Picture": "mission clarity, resources, focus, execution, feedback",
    }[lens]


def variable_translation(lens: str, var: str) -> str:
    translations = {
        "Interpersonal": {
            "Baseline": "Emotional stability under contact",
            "Clarity": "Knowing what you want / what's true",
            "Resources": "Support & emotional capacity",
            "Boundaries": "Ability to hold limits",
            "Execution": "Following through on difficult conversations",
            "Feedback": "Repair & learning from conflict",
        },
        "Financial": {
            "Baseline": "Stability under financial stress",
            "Clarity": "Knowing your numbers & priorities",
            "Resources": "Income, buffer, tools",
            "Boundaries": "Control over spending & exposure",
            "Execution": "Actually doing the necessary actions",
            "Feedback": "Reviewing & closing leaks",
        },
        "Big Picture": {
            "Baseline": "Overall momentum & stability",
            "Clarity": "Clear direction & next step",
            "Resources": "Energy, support, environment",
            "Boundaries": "Protecting focus & saying no",
            "Execution": "Shipping & completing work",
            "Feedback": "Measuring & iterating",
        },
    }
    return translations.get(lens, {}).get(var, var)


def pressure_focus_summary(lens: str, weakest_var: str) -> str:
    summaries = {
        "Interpersonal": f"Biggest pressure is in **{weakest_var}** — likely too much emotional load or poor resolution patterns.",
        "Financial": f"Biggest pressure is in **{weakest_var}** — usually buffer, system, or leak problem.",
        "Big Picture": f"Biggest pressure is in **{weakest_var}** — goal is real, but structure/support isn't matching.",
    }
    return summaries.get(lens, f"Pressure concentrates in **{weakest_var}**.")


# ──────────────────────────────────────────────────────────────
# Question Bank (placeholder — fill with your real questions)
# ──────────────────────────────────────────────────────────────

QUESTION_BANK = {
    "Interpersonal": [],  # ← your ~75+ questions here
    "Financial": [],      # ← your ~75+ questions here
    "Big Picture": [],    # ← your ~75+ questions here
}

# Note: Make sure every question has unique "id" across ALL lenses
# Recommended structure:
# {"id": "i01", "text": "...", "variable": "Baseline", "weight": 1.2, "reverse": True}

# ──────────────────────────────────────────────────────────────
# Session State Initialization
# ──────────────────────────────────────────────────────────────

defaults = {
    "stage": "setup",
    "lens": "Interpersonal",
    "active_questions": [],
    "answers": {},
    "idx": 0,
    "followup_questions": [],
    "followup_answers": {},
    "followup_idx": 0,
    "followup_targets": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_session():
    for key, value in defaults.items():
        st.session_state[key] = value
    st.rerun()


# ──────────────────────────────────────────────────────────────
# UI – Header & Sidebar
# ──────────────────────────────────────────────────────────────

st.title("Trifactor")
st.caption("Pressure mapping across three lenses")

with st.sidebar:
    st.header("Controls")
    st.caption("25 initial questions + targeted follow-ups")
    if st.button("Reset Everything", type="secondary"):
        reset_session()

# ──────────────────────────────────────────────────────────────
# Setup Screen – Lens Selection
# ──────────────────────────────────────────────────────────────

if st.session_state.stage == "setup":
    st.subheader("Choose your diagnostic lens")

    st.session_state.lens = st.radio(
        "Which area feels most pressurized right now?",
        options=LENSES,
        index=LENSES.index(st.session_state.lens),
        horizontal=True,
    )

    st.markdown(
        f"**Focus of this lens:** {lens_focus(st.session_state.lens)}  \n"
        "The tool will show you **where** the system is weakest — not how to fix it yet."
    )

    if st.button("Start 25 Questions", type="primary"):
        lens = st.session_state.lens
        bank = QUESTION_BANK.get(lens, [])

        if not bank:
            st.error("Question bank for this lens is empty. Add questions first.")
            st.stop()

        # Random sample of 25 (or all if fewer)
        k = min(25, len(bank))
        st.session_state.active_questions = random.sample(bank, k=k)
        st.session_state.answers = {}
        st.session_state.idx = 0
        st.session_state.stage = "questions"
        st.rerun()

# ──────────────────────────────────────────────────────────────
# Questions Stage (25 questions) — starts here
# ──────────────────────────────────────────────────────────────

if st.session_state.stage == "questions":

# ──────────────────────────────────────────────────────────────
# Scoring & Analysis Functions
# ──────────────────────────────────────────────────────────────

def compute_scores(questions, answers):
    per_var_num = {}
    per_var_den = {}
    per_var_raw = {}
    scored_items = []  # (var, score_0_4, weight, question_dict, original_answer)

    for q in questions:
        qid = q["id"]
        if qid not in answers:
            continue

        a = int(answers[qid])
        score = (4 - a) if q.get("reverse", False) else a
        var = q["variable"]
        weight = float(q.get("weight", 1.0))

        per_var_num[var] = per_var_num.get(var, 0.0) + score * weight
        per_var_den[var] = per_var_den.get(var, 0.0) + weight
        per_var_raw.setdefault(var, []).append(score)

        scored_items.append((var, score, weight, q, a))

    per_variable = {}
    for var in per_var_num:
        den = per_var_den.get(var, 1.0) or 1.0
        mean_0_4 = per_var_num[var] / den
        pct = (mean_0_4 / 4.0) * 100

        raw_scores = per_var_raw.get(var, [])
        volatility = 0.0
        if len(raw_scores) >= 2:
            volatility = (pstdev(raw_scores) / 2.0) * 100
        volatility = clamp(volatility, 0, 100)

        per_variable[var] = {
            "pct": pct,
            "zone": zone_name(pct),
            "volatility": volatility,
        }

    # Overall weighted score
    overall_num = overall_den = 0.0
    for var, info in per_variable.items():
        w = VARIABLE_WEIGHTS.get(var, 1.0)
        overall_num += info["pct"] * w
        overall_den += w

    overall = (overall_num / overall_den) if overall_den > 0 else 0.0

    scored_items.sort(key=lambda x: (x[1], -x[2]))  # lowest first, then heaviest

    return overall, per_variable, scored_items


def choose_followup_targets(per_variable):
    if not per_variable:
        return []

    sorted_vars = sorted(per_variable.items(), key=lambda x: x[1]["pct"])
    weakest = sorted_vars[0][0]

    reds = [v for v, d in per_variable.items() if d["zone"] == "RED" and v != weakest]
    yellows = [v for v, d in per_variable.items() if d["zone"] == "YELLOW" and v != weakest]

    targets = [weakest] + reds[:2]

    if len(targets) < 3:
        for v in yellows:
            if v not in targets:
                targets.append(v)
            if len(targets) >= 3:
                break

    return targets[:3]


def pick_followup_questions(lens, targets, already_asked_ids, n=10):
    bank = QUESTION_BANK.get(lens, [])[:]

    # Priority: targeted variables, not asked yet
    priority = [q for q in bank if q["id"] not in already_asked_ids and q["variable"] in targets]
    random.shuffle(priority)
    selected = priority[:n]

    # Fill with any not asked
    if len(selected) < n:
        remaining = [q for q in bank if q["id"] not in already_asked_ids and q not in selected]
        random.shuffle(remaining)
        selected.extend(remaining[:n - len(selected)])

    # Last resort: anything
    if len(selected) < n:
        all_remaining = [q for q in bank if q not in selected]
        random.shuffle(all_remaining)
        selected.extend(all_remaining[:n - len(selected)])

    return selected[:n]


# ──────────────────────────────────────────────────────────────
# Results Screen (after 25 questions)
# ──────────────────────────────────────────────────────────────

if st.session_state.stage == "results":
    lens = st.session_state.lens
    questions = st.session_state.active_questions
    answers = st.session_state.answers

    overall, per_var, scored_sorted = compute_scores(questions, answers)
    targets = choose_followup_targets(per_var)

    st.subheader("Diagnostic Results")
    st.write(f"**Lens:** {lens}")
    st.write(f"**Focus:** {lens_focus(lens)}")
    st.metric("Overall Pressure Score", f"{overall:.0f}/100")

    st.markdown("### Category Breakdown")
    for var, info in per_var.items():
        label = variable_translation(lens, var)
        st.write(
            f"- **{label}**: {info['pct']:.0f}  —  {zone_message(info['zone'])}  "
            f"(volatility: {info['volatility']:.0f})"
        )

    if per_var:
        weakest_var = min(per_var.items(), key=lambda x: x[1]["pct"])[0]
        weakest_label = variable_translation(lens, weakest_var)

        st.markdown(f"**Main Pressure Point:** {weakest_label}")
        st.write(pressure_focus_summary(lens, weakest_label))

        st.markdown("**Strongest signals (lowest 3)**")
        for _, score, weight, q, _ in scored_sorted[:3]:
            st.write(f"- {q['text']}  (score: {score}/4)")

        # Recommended first action
        weakest_items = [t for t in scored_sorted if t[0] == weakest_var]
        if weakest_items:
            first_lever = weakest_items[0][3]  # already sorted lowest first
            st.markdown("**Recommended first move:**")
            st.write(f"→ {first_lever['text']}")

    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Continue → 10 Targeted Follow-ups", type="primary"):
            already = {q["id"] for q in questions}
            followups = pick_followup_questions(lens, targets, already, n=10)
            st.session_state.followup_questions = followups
            st.session_state.followup_answers = {}
            st.session_state.followup_idx = 0
            st.session_state.followup_targets = targets
            st.session_state.stage = "followups"
            st.rerun()

    with col2:
        if st.button("Start Over (same lens)"):
            st.session_state.stage = "setup"
            st.rerun()


# ──────────────────────────────────────────────────────────────
# Follow-up Questions (10 targeted)
# ──────────────────────────────────────────────────────────────

if st.session_state.stage == "followups":
    fqs = st.session_state.followup_questions
    idx = st.session_state.followup_idx
    total = len(fqs)

    if total == 0:
        st.error("No follow-up questions available.")
        st.stop()

    st.subheader(f"Follow-up Questions  ({idx+1}/{total})")
    st.caption("Digging deeper into weakest areas")

    st.progress(idx / total)

    q = fqs[idx]
    st.write(f"**{q['text']}**")
    st.caption(variable_translation(st.session_state.lens, q["variable"]))

    key = f"fu_{q['id']}_{idx}"
    current = st.session_state.followup_answers.get(key)

    choice = st.radio(
        "Select:",
        options=list(SCALE_LABELS.keys()),
        format_func=lambda x: SCALE_LABELS[x],
        index=list(SCALE_LABELS.keys()).index(current) if current is not None else 2,
        key=key,
        horizontal=True,
    )

    st.session_state.followup_answers[key] = choice

    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        if st.button("← Back", disabled=(idx == 0)):
            st.session_state.followup_idx = max(0, idx - 1)
            st.rerun()

    with col2:
        if st.button("Next →", disabled=(idx >= total - 1)):
            st.session_state.followup_idx = min(total - 1, idx + 1)
            st.rerun()

    with col3:
        if st.button("Finish & See Updated Results", type="primary"):
            st.session_state.stage = "final_results"
            st.rerun()


# ──────────────────────────────────────────────────────────────
# Final Results (25 + 10 follow-ups)
# ──────────────────────────────────────────────────────────────

if st.session_state.stage == "final_results":
    all_questions = st.session_state.active_questions + st.session_state.followup_questions
    all_answers = st.session_state.answers.copy()

    for key, val in st.session_state.followup_answers.items():
        qid = key.split("_")[1]  # extract qid from fu_{qid}_{idx}
        all_answers[qid] = val

    overall, per_var, scored_sorted = compute_scores(all_questions, all_answers)

    st.subheader("Updated Results (25 + 10 follow-ups)")
    st.metric("Overall Pressure Score", f"{overall:.0f}/100")

    st.markdown("### Category Breakdown (updated)")
    for var, info in sorted(per_var.items(), key=lambda x: x[1]["pct"]):
        label = variable_translation(st.session_state.lens, var)
        st.write(
            f"- **{label}**: {info['pct']:.0f}  —  {zone_message(info['zone'])}"
        )

    if per_var:
        weakest_var = min(per_var.items(), key=lambda x: x[1]["pct"])[0]
        weakest_label = variable_translation(st.session_state.lens, weakest_var)
        st.markdown(f"**Primary Pressure Point:** {weakest_label}")
        st.write(pressure_focus_summary(st.session_state.lens, weakest_label))

    st.divider()
    st.caption("This is still just a map — not a treatment plan.")

    if st.button("Run Again (same lens)", type="primary"):
        st.session_state.stage = "setup"
        st.rerun()
