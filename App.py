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
    "Interpersonal": [
        {"id":"i01","text":"How often do you feel tense before interacting with a specific person?","variable":"Baseline","weight":1.2,"reverse":True},
        {"id":"i02","text":"How often does one conversation ruin your whole day?","variable":"Baseline","weight":1.3,"reverse":True},
        {"id":"i03","text":"How often do you avoid a conversation you know you need to have?","variable":"Execution","weight":1.2,"reverse":True},
        {"id":"i04","text":"How clear are you about what you want from this relationship/situation?","variable":"Clarity","weight":1.3,"reverse":False},
        {"id":"i05","text":"How often do you leave a talk unsure what was actually decided?","variable":"Clarity","weight":1.1,"reverse":True},
        {"id":"i06","text":"How often do you say “yes” when you mean “no”?","variable":"Boundaries","weight":1.4,"reverse":True},
        {"id":"i07","text":"How often do you tolerate behavior that you resent later?","variable":"Boundaries","weight":1.3,"reverse":True},
        {"id":"i08","text":"How often do you communicate your limits early rather than late?","variable":"Boundaries","weight":1.2,"reverse":False},
        {"id":"i09","text":"How supported do you feel by at least one person in your life?","variable":"Resources","weight":1.1,"reverse":False},
        {"id":"i10","text":"How often do you feel alone carrying the emotional load?","variable":"Resources","weight":1.2,"reverse":True},
        {"id":"i11","text":"How often do conflicts repeat without resolution?","variable":"Feedback","weight":1.2,"reverse":True},
        {"id":"i12","text":"How often do you reflect after conflict and adjust your approach?","variable":"Feedback","weight":1.1,"reverse":False},
        {"id":"i13","text":"How often do you interpret neutral behavior as hostile?","variable":"Feedback","weight":1.0,"reverse":True},
        {"id":"i14","text":"How often do you apologize to restore peace even when you weren’t wrong?","variable":"Boundaries","weight":1.1,"reverse":True},
        {"id":"i15","text":"How often do you directly ask for what you need?","variable":"Execution","weight":1.2,"reverse":False},
        {"id":"i16","text":"How often do you replay conversations in your head afterward?","variable":"Baseline","weight":1.0,"reverse":True},
        {"id":"i17","text":"How often do you feel respected in the dynamic?","variable":"Resources","weight":1.2,"reverse":False},
        {"id":"i18","text":"How often do you keep your word when you set a boundary?","variable":"Execution","weight":1.3,"reverse":False},
        {"id":"i19","text":"How often do you use sarcasm/withdrawal instead of stating the issue?","variable":"Execution","weight":1.1,"reverse":True},
        {"id":"i20","text":"How often do you feel you must perform to be valued?","variable":"Clarity","weight":1.0,"reverse":True},
        {"id":"i21","text":"How often do you choose timing/location to improve the odds of a good talk?","variable":"Execution","weight":1.0,"reverse":False},
        {"id":"i22","text":"How often do you communicate expectations before frustration builds?","variable":"Execution","weight":1.1,"reverse":False},
        {"id":"i23","text":"How often do you recover quickly after conflict?","variable":"Baseline","weight":1.1,"reverse":False},
        {"id":"i24","text":"How often do you ask clarifying questions instead of assuming intent?","variable":"Feedback","weight":1.0,"reverse":False},
        {"id":"i25","text":"How often do you feel you’re walking on eggshells?","variable":"Baseline","weight":1.3,"reverse":True},
        {"id":"i51","text":"How often do you notice resentment building before you name it?","variable":"Feedback","weight":1.2,"reverse":True},
        {"id":"i52","text":"How often do you recover quickly after interpersonal strain?","variable":"Baseline","weight":1.1,"reverse":False},
        {"id":"i53","text":"How often do you feel conversations require translation instead of clarity?","variable":"Clarity","weight":1.2,"reverse":True},
        {"id":"i54","text":"How often do you address tone instead of content when tension arises?","variable":"Execution","weight":1.0,"reverse":False},
        {"id":"i55","text":"How often do you feel relational effort is uneven?","variable":"Resources","weight":1.2,"reverse":True},
        {"id":"i56","text":"How often do you say no without justification?","variable":"Boundaries","weight":1.3,"reverse":False},
        {"id":"i57","text":"How often do misunderstandings persist longer than necessary?","variable":"Feedback","weight":1.1,"reverse":True},
        {"id":"i58","text":"How often do you revisit unresolved conversations?","variable":"Execution","weight":1.1,"reverse":True},
        {"id":"i59","text":"How often do you feel relationally resourced rather than depleted?","variable":"Resources","weight":1.3,"reverse":False},
        {"id":"i60","text":"How often do you check assumptions before reacting?","variable":"Feedback","weight":1.0,"reverse":False},
        {"id":"i61","text":"How often do you feel pressure to maintain harmony at your expense?","variable":"Boundaries","weight":1.2,"reverse":True},
        {"id":"i62","text":"How often do you name patterns instead of incidents?","variable":"Clarity","weight":1.2,"reverse":False},
        {"id":"i63","text":"How often do you feel conversations reset rather than compound?","variable":"Baseline","weight":1.1,"reverse":False},
        {"id":"i64","text":"How often do you feel safe disagreeing?","variable":"Resources","weight":1.2,"reverse":False},
        {"id":"i65","text":"How often do you delay resolution due to emotional fatigue?","variable":"Baseline","weight":1.1,"reverse":True},
        {"id":"i66","text":"How often do you follow through on relational agreements?","variable":"Execution","weight":1.2,"reverse":False},
        {"id":"i67","text":"How often do you feel conversations end cleanly?","variable":"Clarity","weight":1.1,"reverse":False},
        {"id":"i68","text":"How often do you absorb blame to keep peace?","variable":"Boundaries","weight":1.2,"reverse":True},
        {"id":"i69","text":"How often do you experience mutual accountability?","variable":"Feedback","weight":1.2,"reverse":False},
        {"id":"i70","text":"How often do you exit interactions with increased trust?","variable":"Resources","weight":1.3,"reverse":False},
        {"id":"i71","text":"How often do you recognize emotional debt accumulating?","variable":"Feedback","weight":1.1,"reverse":False},
        {"id":"i72","text":"How often do you state needs without apology?","variable":"Boundaries","weight":1.2,"reverse":False},
        {"id":"i73","text":"How often do you feel relational stability across time?","variable":"Baseline","weight":1.2,"reverse":False},
        {"id":"i74","text":"How often do you resolve issues before they resurface?","variable":"Execution","weight":1.2,"reverse":False},
        {"id":"i75","text":"How often do relationships feel directionally improving?","variable":"Resources","weight":1.3,"reverse":False},
    ],
    
    "Financial": [
        {"id":"f01","text":"How often do you know your exact cash position (today) without guessing?","variable":"Clarity","weight":1.3,"reverse":False},
        {"id":"f02","text":"How often do bills/fees surprise you?","variable":"Clarity","weight":1.2,"reverse":True},
        {"id":"f03","text":"How often do you feel like you’re one emergency away from collapse?","variable":"Baseline","weight":1.3,"reverse":True},
        {"id":"f04","text":"How often do you have a buffer (even small) after essentials?","variable":"Resources","weight":1.3,"reverse":False},
        {"id":"f05","text":"How often do you spend to regulate mood/stress?","variable":"Feedback","weight":1.1,"reverse":True},
        {"id":"f06","text":"How consistently do you track spending (even roughly)?","variable":"Execution","weight":1.2,"reverse":False},
        {"id":"f07","text":"How often do you miss due dates?","variable":"Execution","weight":1.2,"reverse":True},
        {"id":"f08","text":"How often do you avoid opening financial mail/notifications?","variable":"Boundaries","weight":1.1,"reverse":True},
        {"id":"f09","text":"How often do you negotiate rates, call providers, or challenge charges?","variable":"Execution","weight":1.0,"reverse":False},
        {"id":"f10","text":"How clear are you on your top 3 financial priorities this month?","variable":"Clarity","weight":1.2,"reverse":False},
        {"id":"f11","text":"How often do impulse purchases break your plan?","variable":"Boundaries","weight":1.2,"reverse":True},
        {"id":"f12","text":"How often do you review recurring subscriptions/auto-pay items?","variable":"Feedback","weight":1.0,"reverse":False},
        {"id":"f13","text":"How often do you make a simple plan before spending (need vs want)?","variable":"Boundaries","weight":1.1,"reverse":False},
        {"id":"f14","text":"How often does financial stress disrupt sleep/focus?","variable":"Baseline","weight":1.2,"reverse":True},
        {"id":"f15","text":"How often do you feel your income is stable/predictable?","variable":"Resources","weight":1.2,"reverse":False},
        {"id":"f16","text":"How often do you know your minimum survival number per month?","variable":"Clarity","weight":1.1,"reverse":False},
        {"id":"f17","text":"How often do you take one concrete financial action per week?","variable":"Execution","weight":1.1,"reverse":False},
        {"id":"f18","text":"How often do you use a system (notes/app/spreadsheet) to reduce chaos?","variable":"Execution","weight":1.1,"reverse":False},
        {"id":"f19","text":"How often do you borrow/advance money to get through the month?","variable":"Resources","weight":1.1,"reverse":True},
        {"id":"f20","text":"How often do you postpone decisions until they become emergencies?","variable":"Execution","weight":1.2,"reverse":True},
        {"id":"f21","text":"How often do you set boundaries with others about money (loans, favors, guilt)?","variable":"Boundaries","weight":1.0,"reverse":False},
        {"id":"f22","text":"How often do you feel ashamed about money (and hide it)?","variable":"Feedback","weight":1.0,"reverse":True},
        {"id":"f23","text":"How often do you have a realistic plan for the next 30 days?","variable":"Clarity","weight":1.2,"reverse":False},
        {"id":"f24","text":"How often do you follow that plan when stress hits?","variable":"Boundaries","weight":1.1,"reverse":False},
        {"id":"f25","text":"How often do you recover quickly after a financial hit?","variable":"Baseline","weight":1.1,"reverse":False},
    
        # ── Additional Financial questions (f26–f45) ──
        {"id":"f26","text":"How often do you feel anxious or braced when checking your bank balance?","variable":"Baseline","weight":1.2,"reverse":True},
        {"id":"f27","text":"How frequently do you delay looking at statements or bills you suspect are bad?","variable":"Feedback","weight":1.1,"reverse":True},
        {"id":"f28","text":"How often do you know exactly where your next income payment is coming from?","variable":"Resources","weight":1.3,"reverse":False},
        {"id":"f29","text":"How often do you plan major spending before the money actually arrives?","variable":"Clarity","weight":1.2,"reverse":False},
        {"id":"f30","text":"How often do you spend reactively/defensively instead of intentionally?","variable":"Boundaries","weight":1.2,"reverse":True},
        {"id":"f31","text":"How quickly do you adjust habits after noticing a bad financial week/month?","variable":"Feedback","weight":1.1,"reverse":False},
        {"id":"f32","text":"How clearly do you know which one expense category is creating the most pressure?","variable":"Clarity","weight":1.3,"reverse":False},
        {"id":"f33","text":"How often do you knowingly choose convenience over cost savings?","variable":"Boundaries","weight":1.1,"reverse":True},
        {"id":"f34","text":"How often do you make money decisions while feeling rushed or panicked?","variable":"Baseline","weight":1.2,"reverse":True},
        {"id":"f35","text":"How regularly do you look back at past financial choices to learn from them?","variable":"Feedback","weight":1.0,"reverse":False},
        {"id":"f36","text":"How good are you at saying no to commitments you can't comfortably afford?","variable":"Boundaries","weight":1.2,"reverse":False},
        {"id":"f37","text":"How fragile does your entire financial setup feel on a typical day?","variable":"Baseline","weight":1.2,"reverse":True},
        {"id":"f38","text":"How often do you consciously decide what NOT to spend money on right now?","variable":"Clarity","weight":1.2,"reverse":False},
        {"id":"f39","text":"How quickly do you act on small wins (e.g., canceling a subscription, negotiating a bill)?","variable":"Execution","weight":1.1,"reverse":False},
        {"id":"f40","text":"How often do you feel stuck or trapped by previous financial decisions?","variable":"Feedback","weight":1.2,"reverse":True},
        {"id":"f41","text":"How deliberately do you reduce financial risk exposure (e.g., insurance, emergency fund)?","variable":"Boundaries","weight":1.2,"reverse":False},
        {"id":"f42","text":"How consistently do you maintain at least one meaningful financial buffer?","variable":"Resources","weight":1.3,"reverse":False},
        {"id":"f43","text":"How often do you delay necessary purchases due to fear or scarcity mindset?","variable":"Baseline","weight":1.1,"reverse":True},
        {"id":"f44","text":"How understandable and transparent do your finances feel to you overall?","variable":"Clarity","weight":1.2,"reverse":False},
        {"id":"f45","text":"How often do you follow through on the boring but essential stabilizing actions?","variable":"Execution","weight":1.2,"reverse":False},
    ],

"Big Picture": [
        {"id": "b01", "text": "How clear is your long-term direction (north star)?", "variable": "Clarity", "weight": 1.3, "reverse": False}, 
        {"id": "b02", "text": "How often do you feel scattered or pulled in too many directions?", "variable": "Baseline", "weight": 1.2, "reverse": True},
        {"id": "b03", "text": "How easily can you name the single smallest next step right now?", "variable": "Clarity", "weight": 1.2, "reverse": False},
        {"id": "b04", "text": "How often do you have enough energy/focus to actually do meaningful work?", "variable": "Resources", "weight": 1.2, "reverse": False},
        {"id": "b05", "text": "How frequently do you spend time on tasks that don't move your main goal forward?", "variable": "Boundaries", "weight": 1.3, "reverse": True},
        {"id": "b06", "text": "How often do you finish and ship things instead of endlessly refining?", "variable": "Execution", "weight": 1.3, "reverse": False},
        {"id": "b07", "text": "How often does your direction or priorities change dramatically week-to-week?", "variable": "Baseline", "weight": 1.2, "reverse": True},
        {"id": "b08", "text": "How consistently do you track real progress with numbers (not just feelings)?", "variable": "Feedback", "weight": 1.2, "reverse": False},
        {"id": "b09", "text": "How often do you actually review what worked and change your approach?", "variable": "Feedback", "weight": 1.2, "reverse": False},
        {"id": "b10", "text": "How often do you ignore clear warning signals because they feel inconvenient?", "variable": "Feedback", "weight": 1.1, "reverse": True},
        {"id": "b11", "text": "How well do you protect deep work time from interruptions and distractions?", "variable": "Boundaries", "weight": 1.3, "reverse": False},
        {"id": "b12", "text": "How often do you feel like you're operating with zero buffer or safety margin?", "variable": "Resources", "weight": 1.2, "reverse": True},
        {"id": "b13", "text": "How realistic and followable is your typical weekly plan?", "variable": "Execution", "weight": 1.2, "reverse": False},
        {"id": "b14", "text": "How often do other people's urgencies derail your own priorities?", "variable": "Boundaries", "weight": 1.3, "reverse": True},
        {"id": "b15", "text": "How clearly can you name the top 3 things you should say 'no' to right now?", "variable": "Clarity", "weight": 1.2, "reverse": False},
        {"id": "b16", "text": "How often do you experience real forward momentum that feels good?", "variable": "Baseline", "weight": 1.1, "reverse": False},
        {"id": "b17", "text": "How frequently do you procrastinate on the one most important/scary task?", "variable": "Execution", "weight": 1.3, "reverse": True},
        {"id": "b18", "text": "How easy is it for you to get help, advice, or tools when you're stuck?", "variable": "Resources", "weight": 1.1, "reverse": False},
        {"id": "b19", "text": "How often do you document important decisions so you don't re-debate them?", "variable": "Feedback", "weight": 1.1, "reverse": False},
        {"id": "b20", "text": "How well does your current environment (physical + digital) support your goals?", "variable": "Resources", "weight": 1.2, "reverse": False0},
        {"id": "b21", "text": "How quickly do you simplify things when they start becoming too complicated?", "variable": "Feedback", "weight": 1.2, "reverse": False},
        {"id": "b22", "text": "How often do you actually complete the things you start?", "variable": "Execution", "weight": 1.3, "reverse": False},
        {"id": "b23", "text": "How often do you experience mission drift after a setback or criticism?", "variable": "Baseline", "weight": 1.2, "reverse": True},
        {"id": "b24", "text": "How good are you at picking one important lever and pushing it hard for a week?", "variable": "Execution", "weight": 1.2, "reverse": False},
        {"id": "b25", "text": "How real and reachable does your main goal actually feel right now?", "variable": "Clarity", "weight": 1.3, "reverse": False},
        {"id": "b26", "text": "How often does your mission feel like it pulls you forward instead of you pushing?", "variable": "Baseline", "weight": 1.2, "reverse": False},
        {"id": "b27", "text": "How clearly can you name what you should definitely NOT be working on right now?", "variable": "Clarity", "weight": 1.3, "reverse": False},
        {"id": "b28", "text": "How frequently does your whole system feel overloaded and fragile?", "variable": "Baseline", "weight": 1.3, "reverse": True},
        {"id": "b29", "text": "How intentionally do you prune or simplify when complexity increases?", "variable": "Execution", "weight": 1.2, "reverse": False},
        {"id": "b30", "text": "How often do you feel genuinely supported by your current setup/structure?", "variable": "Resources", "weight": 1.2, "reverse": False},
        {"id": "b31", "text": "How often do you complete full cycles of work instead of abandoning projects halfway?", "variable": "Execution", "weight": 1.2, "reverse": False},
        {"id": "b32", "text": "How frequently do external notifications or requests pull you off your intended path?", "variable": "Boundaries", "weight": 1.2, "reverse": True},
        {"id": "b33", "text": "How quickly can you identify the true bottleneck when progress feels stuck?", "variable": "Clarity", "weight": 1.3, "reverse": False},
        {"id": "b34", "text": "How comfortable are you taking action without having all the information first?", "variable": "Execution", "weight": 1.2, "reverse": False},
        {"id": "b35", "text": "How often do you revisit and challenge assumptions that might no longer be true?", "variable": "Feedback", "weight": 1.1, "reverse": False},
        {"id": "b36", "text": "How deliberately do you protect and manage your energy as a strategic resource?", "variable": "Resources", "weight": 1.2, "reverse": False},
        {"id": "b37", "text": "How often do you find yourself reacting to events instead of acting deliberately?", "variable": "Baseline", "weight": 1.2, "reverse": True},
        {"id": "b38", "text": "How willing are you to reduce scope or simplify when things get overwhelming?", "variable": "Boundaries", "weight": 1.2, "reverse": False},
        {"id": "b39", "text": "How often do you fall for false urgency created by others or yourself?", "variable": "Feedback", "weight": 1.1, "reverse": True},
        {"id": "b40", "text": "How easily can you identify the single most stabilizing move in chaotic times?", "variable": "Clarity", "weight": 1.2, "reverse": False},
        {"id": "b41", "text": "How often do you ship something useful even when the information is incomplete?", "variable": "Execution", "weight": 1.2, "reverse": False},
        {"id": "b42", "text": "How constrained do you feel by your current systems, tools, or environment?", "variable": "Resources", "weight": 1.1, "reverse": True},
        {"id": "b43", "text": "How early do you usually notice when you're drifting off course?", "variable": "Feedback", "weight": 1.1, "reverse": False},
        {"id": "b44", "text": "How intentionally do you slow everything down when speed creates more chaos?", "variable": "Boundaries", "weight": 1.2, "reverse": False},
        {"id": "b45", "text": "How aligned does your current direction still feel with what matters most to you?", "variable": "Baseline", "weight": 1.2, "reverse": False},
        {"id": "b46", "text": "How willing are you to cut losses on things that clearly aren't working?", "variable": "Feedback", "weight": 1.2, "reverse": False},
        {"id": "b47", "text": "How often do you choose high-leverage actions over high-effort ones?", "variable": "Clarity", "weight": 1.3, "reverse": False},
        {"id": "b48", "text": "How well do you maintain steady momentum without burning out?", "variable": "Resources", "weight": 1.2, "reverse": False},
        {"id": "b49", "text": "How good are you at executing the smallest possible viable step forward?", "variable": "Execution", "weight": 1.2, "reverse": False},
        {"id": "b50", "text": "Overall, how directionally sound and self-correcting does your system feel?", "variable": "Baseline", "weight": 1.3, "reverse": False}, 
    ], }


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
0

# ──────────────────────────────────────────────────────────────
# Scoring & Analysis Functions
# ──────────────────────────────────────────────────────────────
  # Calculate final means (rounded to 3 decimals)
    means = {}
    for var in sums:
        if total_weights[var] > 0:
            means[var] = round(sums[vafrom collections import defaultdict

def compute_scores(questions, answers):
    """
    Computes weighted subscale means, raw item scores, and detailed scoring info.
    Skips invalid/missing answers silently.
    
    Returns:
        dict with keys:
        - 'means':       {variable: weighted_mean_score}
        - 'raw_scores':  {variable: [list of individual 0-4 scores]}
        - 'items':       list of (var, score, weight, question_dict, original_answer)
    """
    sums = defaultdict(float)          # weighted sum
    total_weights = defaultdict(float) # sum of weights per variable
    raw_scores = defaultdict(list)     # unweighted item scores (0-4)
    items = []

    for q in questions:
        qid = q["id"]
        if qid not in answers:
            continue

        # Safe integer conversion
        try:
            a = int(answers[qid])
            if not (0 <= a <= 4):
                continue  # or log warning
        except (ValueError, TypeError):
            continue  # skip bad data (empty string, float, None, text...)

        # Apply reverse scoring if needed
        score = (4 - a) if q.get("reverse", False) else a

        var = q["variable"]
        w = float(q.get("weight", 1.0))

        sums[var] += score * w
        total_weights[var] += w
        raw_scores[var].append(score)

        items.append((var, score, w, q, a))

    # Calculate final means (rounded to 3 decimals)
    means = {}
    for var in sums:
        if total_weights[var] > 0:
            means[var] = round(sums[var] / total_weights[var], 3)
        else:
            means[var] = None

    return {
        "means": means,
        "raw_scores": dict(raw_scores),
        "items": items
    }from collections import defaultdict

def compute_scores(questions, answers):
    """
    Computes weighted subscale means, raw item scores, and detailed scoring info.
    Skips invalid/missing answers silently.
    
    Returns:
        dict with keys:
        - 'means':       {variable: weighted_mean_score}
        - 'raw_scores':  {variable: [list of individual 0-4 scores]}
        - 'items':       list of (var, score, weight, question_dict, original_answer)
    """
    sums = defaultdict(float)          # weighted sum
    total_weights = defaultdict(float) # sum of weights per variable
    raw_scores = defaultdict(list)     # unweighted item scores (0-4)
    items = []

    for q in questions:
        qid = q["id"]
        if qid not in answers:
            continue

        # Safe integer conversion
        try:
            a = int(answers[qid])
            if not (0 <= a <= 4):
                continue  # or log warning
        except (ValueError, TypeError):
            continue  # skip bad data (empty string, float, None, text...)

        # Apply reverse scoring if needed
        score = (4 - a) if q.get("reverse", False) else a

        var = q["variable"]
        w = float(q.get("weight", 1.0))

        sums[var] += score * w
        total_weights[var] += w
        raw_scores[var].append(score)

        items.append((var, score, w, q, a))

    # Calculate final means (rounded to 3 decimals)
    means = {}
    for var in sums:
        if total_weights[var] > 0:
            means[var] = round(sums[var] / total_weights[var], 3)
        else:
            means[var] = None

    return {
        "means": means,
        "raw_scores": dict(raw_scores),
        "items": items
    }r] / total_weights[var], 3)
        else:
            means[var] = None

    return {
        "means": means,
        "raw_scores": dict(raw_scores),
        "items": items
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
