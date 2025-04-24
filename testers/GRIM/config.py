"""
Configuration file for the GRIM Tester pipeline.
This file contains all the hyper-parameters and prompts used in the pipeline.
"""

import os

import pandas as pd
from dotenv import load_dotenv

# -------------------------------------------------------------------------
# Environment
# -------------------------------------------------------------------------
load_dotenv()
API_KEY: str | None = os.getenv("OPENAI_API_KEY")


# -------------------------------------------------------------------------
# Pipeline hyper-parameters
# -------------------------------------------------------------------------
MAX_WORDS: int = 1000 # Maximum number of words per text segment sent to the AI model
OVERLAP_WORDS: int = 200 # Number of words to overlap between segments


# -------------------------------------------------------------------------
# Prompts
# -------------------------------------------------------------------------
GRIM_PROMPT: str = (
    """
    You are an extraction assistant. Your task is to extract only reported **means and their sample sizes** from the following scientific text. You must follow these rules strictly:

    ---

    **Extract only if ALL of the following are true:**
    - The value is explicitly labeled as a **mean** (e.g., “M = ...”, “mean = ...”).
    - The mean is clearly based on **integer-valued response data** (e.g., responses on Likert-type scales like 1-5, 1-7, etc.).
    - A specific **sample size (N)** is provided in the same sentence, or in a directly connected clause or phrase.
        - IMPORTANT: A SAMPLE SIZE IS ALWAYS AN INTEGER! DO NOT EXTRACT IF THE SAMPLE SIZE IS NOT AN INTEGER!
    - There is a **clear and direct correlation** between the reported mean and its corresponding sample size — do not guess or assume this link.
    - The mean is usable in the **GRIM test** (i.e., based on whole-number responses + a known sample size).
    - The source of the mean is explicitly mentioned (e.g., "mean of Likert-scale responses", "mean of 7-point scale", "mean survey response").
    - Only state that a Likert-scale was used if you see the woard "Likert" or "scale" in the context! If you do not see either of these words, you may not assume that a Likert-scale was used! If this is not clear and there is no other indication that a mean is GRIM-applicable, do not extract it!

    - It is ONLY OKAY to derive sample sizes from other statistics (e.g., t-tests, ANOVA), if the sample size is not clearly mentioned, BUT ONLY IF: it is clear that the mean value is derived from DISCRETE INTEGER-BASED data.
    - t(23) can imply N=24. Keep in mind that for a t-test, the sample size is N = df + 1.
    - f(1, 60) can imply a total of N=62, but two groups of N=31 each. Keep in mind that for an ANOVA, the sample size is N = df + k, where k is the number of groups. So ALWAYS look for the number of groups when you encounter ANOVA.
    - IMPORTANT: when you encounter an ANOVA, check the first degree of freedom (df1) and the second degree of freedom (df2). The first degree of freedom is the number of groups minus 1, and the second degree of freedom is the total sample size minus the number of groups. So if you see f(1, 60), it means that there are 2 groups (1 + 1) and a total sample size of 62 (60 + 2). So never assume the second degree of freedom + 1 is the sample size. Always check the first degree of freedom to see how many groups there are!
    - In your discrete_reasoning, only state that a Likert-scale was used if you see the woard "Likert" or "scale" in the context! If you do not see either of these words, you may not assume that a Likert-scale was used!

    ---

    **NEVER extract if ANY of the following are true:**
    - The sample size is **not clearly linked** to the mean, or could refer to a different statistic or part of the study.
    - It is a **median**, **mode**, **mean difference**, or **range**.
    - It refers to **completion time**, percentages, or **continuous data** (e.g., durations, reaction times).
    - It is a **statistical test value**: t, F, p, r, z, χ², etc.
    - The underlying response scale is not stated as **integer-based** or is ambiguous.

    ---

    Additional rules:
    - If the total sample is split into groups (e.g., experimental/control), extract group-level means and sample sizes separately.
    - NEVER round mean values — extract them **exactly as reported**, preserving **all decimal places and trailing zeros** (e.g., keep `6.60`, not `6.6`).
    - Do **not** perform any calculations. Only extract what is explicitly stated in the text.

    ---
    IMPORTANT: The output must be a JSON-like list of dictionaries, formatted as follows:
    YOU ARE NEVER ALLOWED TO CHANGE THIS FORMAT!
    Output format:

    tests = [
        {{
            "reported_mean": <mean>,
            "sample_size": <sample_size>,
            "discrete_reasoning": "<Why this mean is valid for GRIM (e.g., 'mean of 7-point Likert responses clearly linked to N = 28 in same sentence')>"
        }},
        ...
    ]

    ---

    Text:
    {context}

    Only return the list of tests. Do not explain anything else. Be strict, and only extract what is 100% valid under the criteria above.
    """
)

# -------------------------------------------------------------------------
# Pandas display options
# -------------------------------------------------------------------------
def apply_pandas_display_options() -> None:
    """Standard console-friendly Pandas formatting."""
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 10_000)
    pd.set_option("display.colheader_justify", "center")
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_colwidth", None)
