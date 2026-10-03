PLAN_QUERIES_PROMPT = """You are a research assistant.
The user wants to research this topic: {topic}

Write {n} different web search queries that together cover the topic well.
Each query should look at a different angle (for example: basics, latest news, examples, problems).
Keep each query short, like something a person would type into Google.
If you include a year in a query, use the current year from the date above. Never use older years."""


JUDGE_PROMPT = """You are a strict research reviewer.
Topic: {topic}

Here is everything the searches found so far:
{sources}

Decide if this is enough to write a good, accurate report on the topic.
- Say is_enough = true only if the sources clearly cover the main parts of the topic.
- Say is_enough = false if important parts are missing, the sources are off-topic, or there is almost nothing.
Explain your decision briefly in the reason."""


REFINE_PROMPT = """You are a research assistant.
Topic: {topic}

These searches were already done:
{old_queries}

The reviewer said the evidence is not enough because: {reason}

Write {n} NEW search queries that fill the missing gaps.
Do not repeat the old queries.
If you include a year in a query, use the current year from the date above. Never use older years."""


WRITE_REPORT_PROMPT = """You are a careful research writer.
Topic: {topic}

{coverage_note}
Use ONLY the numbered sources below. Do not use outside knowledge.
{sources}

Write a clear report in Markdown with:
1. A title that repeats the exact topic: {topic}
2. A short summary (3 to 4 sentences)
3. Key findings as bullet points
4. A section called What Could Not Be Verified, listing anything the sources did not cover

Do NOT write a Sources section. It is added automatically.

Rules:
- After each claim, add the source number like [1] or [2].
- Only include a finding if a source directly states it about THIS exact topic. Never use "suggests", "may", or "could" to connect a source to the topic.
- Never replace the topic with a broader or neighboring topic.
- If the sources are weak or missing, say clearly what could not be found.
- Prefer reliable sources (research papers, established news outlets, official announcements).
- Treat marketing blogs and hype as unverified: write "X claims..." instead of stating it as fact, and never copy hype words.
- Put a normal space between every pair of words. Use only normal spaces and hyphens."""