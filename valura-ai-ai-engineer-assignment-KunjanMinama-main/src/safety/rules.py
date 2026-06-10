"""
Safety rules engine — hardcoded keyword / regex matchers.

Design decision: We use pattern-based matching (compiled regexes + keyword sets)
rather than ML to guarantee <1ms evaluation, zero network dependency, and fully
deterministic behaviour. Educational queries are explicitly whitelisted by
detecting question-oriented phrasing (what is, explain, how does, etc.).

Categories covered:
    - insider_trading
    - market_manipulation
    - money_laundering
    - guaranteed_returns
    - reckless_advice
    - sanctions_evasion
    - fraud
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class SafetyRule:
    """A single category-specific safety rule."""
    category: str
    block_patterns: list[re.Pattern]
    block_keywords: list[str]  # lowercased keyword phrases
    message: str  # professional refusal message for this category


# ────────────────────────────────────────────────────────────
# Educational / informational query markers
# If the query is clearly educational ("what is", "explain",
# "how does ... work", "penalty for"), we allow it through.
# ────────────────────────────────────────────────────────────

EDUCATIONAL_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(what\s+is|what\s+are|what\s+does)\b", re.I),
    re.compile(r"\b(explain|describe|definition|overview)\b", re.I),
    re.compile(r"\b(how\s+does|how\s+do\s+(regulators?|brokerages?|the\s+(sec|fca)))\b", re.I),
    re.compile(r"\b(penalty|penalties|legal(ity)?|illegal|regulations?|compliance|requirements?)\b", re.I),
    re.compile(r"\b(investigate|detect|catch|prevent|screen)\b", re.I),
    re.compile(r"\b(difference\s+between|distinguish)\b", re.I),
    re.compile(r"\b(three\s+stages|stages\s+of)\b", re.I),
    re.compile(r"\b(red\s+flag|why\s+(is|are))\b", re.I),
    re.compile(r"\b(historical|average|over\s+\d+\s+years?)\b", re.I),
    re.compile(r"\b(factors?\s+should|consider\s+when)\b", re.I),
    re.compile(r"\b(risks?\s+of|how\s+should)\b", re.I),
    re.compile(r"\b(role\s+in\s+preventing|obligations?\s+(do|have))\b", re.I),
    re.compile(r"\bis\s+(it\s+ever\s+legitimate|short\s+selling\s+illegal)\b", re.I),
    re.compile(r"\b(ponzi\s+scheme\s+works?)\b", re.I),
    re.compile(r"\bare\s+pump[\-\s]and[\-\s]dump\s+groups\b", re.I),
    re.compile(r"\b(disclosure\s+rules|reporting\s+requirements|aml\s+reporting)\b", re.I),
]


def _is_educational(query: str) -> bool:
    """Return True if the query looks like an educational question."""
    for pat in EDUCATIONAL_PATTERNS:
        if pat.search(query):
            return True
    return False


# ────────────────────────────────────────────────────────────
# Category-specific rules
# ────────────────────────────────────────────────────────────

SAFETY_RULES: list[SafetyRule] = [
    SafetyRule(
        category="insider_trading",
        block_patterns=[
            re.compile(r"\b(confidential|non[\-\s]?public|unannounced)\s+(merger|acquisition|earnings|deal|info|information|news)\b", re.I),
            re.compile(r"\b(tip|tipped\s+off)\s+(about|from|regarding)\s+(earnings|merger|deal|acquisition)\b", re.I),
            re.compile(r"\b(trade|buy|sell|load\s+up)\b.*\b(before\s+(the\s+)?(call|announcement|earnings|release))\b", re.I),
            re.compile(r"\b(i\s+work\s+at|my\s+friend\s+at|from\s+my\s+(law\s+firm|company|bank))\b.*\b(know|gave|shared|told)\b", re.I),
            re.compile(r"\b(know\s+about\s+an?\s+unannounced)\b", re.I),
            re.compile(r"\b(need\s+to\s+know\s+the\s+earnings\s+before)\b", re.I),
        ],
        block_keywords=[
            "trade on this confidential",
            "help me trade on this confidential",
            "tip about earnings",
            "before tomorrow's announcement",
        ],
        message=(
            "I can't help with trading based on material non-public information. "
            "Insider trading violates securities law in virtually every jurisdiction. "
            "If you have questions about insider trading regulations, I'm happy to explain them."
        ),
    ),
    SafetyRule(
        category="market_manipulation",
        block_patterns=[
            re.compile(r"\b(pump\s+up|manipulate|inflate)\s+(the\s+)?(price|stock|share)\b", re.I),
            re.compile(r"\bcoordinated\s+(buying|selling|trading)\s+scheme\b", re.I),
            re.compile(r"\bwash\s+trad(e|ing)\s+between\b", re.I),
            re.compile(r"\b(move|push)\s+this\s+stock\b", re.I),
            re.compile(r"\b(create\s+(fake\s+)?volume)\b", re.I),
        ],
        block_keywords=[
            "pump up the price",
            "coordinated buying scheme",
            "wash trade between",
            "design a coordinated",
        ],
        message=(
            "I can't assist with market manipulation schemes. Artificially influencing "
            "market prices is a serious offence under securities regulation. "
            "I can explain how regulators detect these activities if you're interested."
        ),
    ),
    SafetyRule(
        category="money_laundering",
        block_patterns=[
            re.compile(r"\b(move|transfer|route)\s+.*\b(cash|funds?|money)\b.*\b(without\s+reporting|avoid\s+(the\s+)?(reporting|detection))\b", re.I),
            re.compile(r"\b(structure|structuring)\s+(deposits?|transactions?|payments?)\s+(to\s+avoid)\b", re.I),
            re.compile(r"\b(avoid|evade|bypass)\s+(the\s+)?\d*k?\s*(reporting\s+threshold|reporting|detection)\b", re.I),
            re.compile(r"\b(obscure|hide|conceal)\s+(the\s+)?(source|origin)\s+(of\s+)?(these\s+)?(funds?|money|capital)\b", re.I),
            re.compile(r"\bhide\s+trading\s+profits\s+from\s+(the\s+)?tax\b", re.I),
            re.compile(r"\blayer\s+my\s+trades\s+to\s+obscure\b", re.I),
        ],
        block_keywords=[
            "without reporting",
            "avoid the 10k reporting threshold",
            "obscure the source of these funds",
            "hide trading profits from the tax",
        ],
        message=(
            "I can't provide guidance on evading financial reporting requirements or "
            "concealing the source of funds. Anti-money laundering laws exist to "
            "protect the financial system. I can explain AML compliance if helpful."
        ),
    ),
    SafetyRule(
        category="guaranteed_returns",
        block_patterns=[
            re.compile(r"\bguarantee\s+(me|us|my)?\s*\d+\s*%\s*(return|profit|gain)\b", re.I),
            re.compile(r"\bpromise\s+(me|my)\s+money\s+will\s+(double|triple)\b", re.I),
            re.compile(r"\b100\s*%\s*(certain|guaranteed|sure|definite)\s+to\s+(go\s+up|rise|increase)\b", re.I),
            re.compile(r"\bfoolproof\s+(way|method|strategy)\s+to\s+make\b", re.I),
            re.compile(r"\btell\s+me\s+a\s+stock\s+that.{0,20}(certain|guaranteed|sure)\s+to\s+go\s+up\b", re.I),
        ],
        block_keywords=[
            "guarantee me",
            "promise me my money will double",
            "100% certain to go up",
            "foolproof way to make",
        ],
        message=(
            "I can't make guarantees about investment returns. No legitimate financial "
            "advisor can promise specific returns — all investments carry risk. "
            "I can discuss historical averages and risk-adjusted expectations instead."
        ),
    ),
    SafetyRule(
        category="reckless_advice",
        block_patterns=[
            re.compile(r"\b(all|entire|whole)\s+(my\s+)?(retirement|savings|emergency\s+fund|life\s+savings)\b.*\b(in(to)?|on)\s+(crypto|bitcoin|options|meme\s+stock|single\s+stock)\b", re.I),
            re.compile(r"\b(tell\s+me\s+to\s+take|take)\s+a\s+margin\s+loan\s+to\s+buy\b", re.I),
            re.compile(r"\b(mortgage|remortgage)\s+my\s+house\s+(for|to\s+buy)\b", re.I),
            re.compile(r"\bput\s+(all|my\s+entire|my\s+whole)\s+(emergency\s+fund|savings?)\s+into\s+(options|crypto|leveraged)\b", re.I),
            re.compile(r"\b(entire\s+emergency\s+fund\s+into\s+options)\b", re.I),
            re.compile(r"\btell\s+me\s+which\s+stock\s+to\s+mortgage\b", re.I),
            re.compile(r"\bi'm\s+\d+\s+and\s+want\s+to\s+put\s+all\s+my\b.*\bin(to)?\s+(crypto|bitcoin)\b", re.I),
        ],
        block_keywords=[
            "mortgage my house for",
            "margin loan to buy more",
            "entire emergency fund into options",
            "tell me which stock to mortgage",
            "all my retirement savings in crypto",
        ],
        message=(
            "I can't encourage highly concentrated, leveraged, or reckless investment "
            "decisions that could jeopardise your financial safety. I'm happy to discuss "
            "a responsible approach that balances risk and opportunity."
        ),
    ),
    SafetyRule(
        category="sanctions_evasion",
        block_patterns=[
            re.compile(r"\b(bypass|evade|circumvent|route\s+around)\s+(OFAC\s+)?sanctions\b", re.I),
            re.compile(r"\b(invest\s+in|buy|trade)\s+.*\bsanctioned\b.*\bwithout\s+(it\s+)?being\s+traced\b", re.I),
            re.compile(r"\bshell\s+company\s+to\s+bypass\b", re.I),
        ],
        block_keywords=[
            "bypass ofac sanctions",
            "without it being traced",
            "route trades through a shell company",
        ],
        message=(
            "I can't assist with circumventing international sanctions. Sanctions evasion "
            "is a serious criminal offence. I can explain OFAC and sanctions compliance "
            "frameworks if you're interested."
        ),
    ),
    SafetyRule(
        category="fraud",
        block_patterns=[
            re.compile(r"\b(fake|forged?|falsif(y|ied)|fabricat(e|ed))\s+(contract\s+note|document|receipt|statement|invoice)\b", re.I),
            re.compile(r"\bdraft\s+a\s+fake\b", re.I),
            re.compile(r"\b(claim\s+false|false\s+claim|fabricat(e|ed)\s+losses)\b", re.I),
        ],
        block_keywords=[
            "fake contract note",
            "draft a fake",
        ],
        message=(
            "I can't help create fraudulent documents. Document fraud is a criminal "
            "offence. If you need help understanding contract notes or trade "
            "confirmations, I'm glad to explain them."
        ),
    ),
]


def get_all_rules() -> list[SafetyRule]:
    """Return the full list of safety rules."""
    return SAFETY_RULES
