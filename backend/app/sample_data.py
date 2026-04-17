from datetime import datetime, timedelta, timezone


SEED_HEADLINES: list[dict[str, str]] = [
    {
        "headline": "Fed officials signal patience as inflation data cools for a second month",
        "source": "Reuters",
    },
    {
        "headline": "Apple supplier checks improve as iPhone demand holds above seasonal trend",
        "source": "Bloomberg",
    },
    {
        "headline": "Tesla cuts prices in China again as EV competition intensifies",
        "source": "Yahoo Finance",
    },
    {
        "headline": "Oil rises after fresh shipping disruptions in the Red Sea",
        "source": "CNBC",
    },
    {
        "headline": "Nvidia extends rally as hyperscalers raise AI infrastructure budgets",
        "source": "MarketWatch",
    },
    {
        "headline": "Bank stocks slip after treasury yields retreat on soft payroll revisions",
        "source": "Reuters",
    },
    {
        "headline": "Gold firms as traders trim bets on rapid rate cuts",
        "source": "Bloomberg",
    },
    {
        "headline": "Microsoft unveils new enterprise copilots for finance and security teams",
        "source": "Yahoo Finance",
    },
    {
        "headline": "Semiconductor shares climb on renewed optimism around AI server demand",
        "source": "Barron's",
    },
    {
        "headline": "Dollar eases after ECB officials push back on aggressive tightening fears",
        "source": "Reuters",
    },
    {
        "headline": "Meta advertising outlook strengthens as digital ad spending rebounds",
        "source": "The Wall Street Journal",
    },
    {
        "headline": "China property stress pressures global miners and industrial cyclicals",
        "source": "Financial Times",
    },
    {
        "headline": "Amazon logistics expansion boosts confidence in next-day delivery margins",
        "source": "Bloomberg",
    },
    {
        "headline": "Treasury auction demand surprises to the upside, pulling long-end yields lower",
        "source": "Reuters",
    },
    {
        "headline": "Natural gas tumbles as warmer weather outlook hits demand expectations",
        "source": "CNBC",
    },
    {
        "headline": "Intel wins fresh foundry commitment from telecom equipment customer",
        "source": "Yahoo Finance",
    },
    {
        "headline": "Euro zone manufacturing contracts again, keeping recession risks in focus",
        "source": "Bloomberg",
    },
    {
        "headline": "JPMorgan traders flag heavier hedging flows into bank earnings season",
        "source": "Reuters",
    },
    {
        "headline": "Cybersecurity stocks gain as governments warn of elevated election threats",
        "source": "The Information",
    },
    {
        "headline": "OPEC supply discipline keeps energy equities near monthly highs",
        "source": "MarketWatch",
    },
]


MOCK_LIVE_VARIANTS: list[dict[str, str]] = [
    {
        "headline": "Broadcom jumps after AI networking backlog expands into the second half",
        "source": "Bloomberg",
    },
    {
        "headline": "Retail sales miss sparks renewed debate over the odds of a summer rate cut",
        "source": "Reuters",
    },
    {
        "headline": "Crude pulls back as traders weigh ceasefire talks against tight inventories",
        "source": "Yahoo Finance",
    },
    {
        "headline": "Alphabet cloud growth accelerates, lifting sentiment across megacap tech",
        "source": "CNBC",
    },
    {
        "headline": "Defense names outperform as new sanctions package heightens geopolitical tension",
        "source": "Financial Times",
    },
    {
        "headline": "Bank of Japan commentary pushes yen volatility higher into the close",
        "source": "Reuters",
    },
    {
        "headline": "Exxon and Chevron lead energy higher after refinery outage tightens fuel markets",
        "source": "Bloomberg",
    },
    {
        "headline": "Service inflation remains sticky, complicating the policy path for central banks",
        "source": "The Wall Street Journal",
    },
]


def build_seed_rows() -> list[dict[str, str | datetime]]:
    now = datetime.now(timezone.utc)
    rows: list[dict[str, str | datetime]] = []
    for index, item in enumerate(SEED_HEADLINES):
        rows.append(
            {
                **item,
                "timestamp": now - timedelta(minutes=18 * (len(SEED_HEADLINES) - index)),
            }
        )
    return rows

