"""
Core logic for extracting reported means and running the GRIM test.
Use AI to automatically extracted reported means and sample sizes from a given context and perform the GRIM test to check for inconsistencies.

Credits
-------
The functionality is heavily inspired by the paper "The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology", (Brown & Heathers, 2016).
(DOI: 10.1177/1948550616673876)
"""

import ast
import os
from typing import Dict, List

import fitz  # PyMuPDF
import pandas as pd
from bs4 import BeautifulSoup

# Local imports
from config import (
    API_KEY,
    GRIM_PROMPT,
    MAX_WORDS,
    OVERLAP_WORDS,
    apply_pandas_display_options,
)
from openai import OpenAI

# -------------------------------------------------------------------------
# Pandas display options
# -------------------------------------------------------------------------
apply_pandas_display_options()  # Applies pandas display options for better readability

# -------------------------------------------------------------------------
# Main class, GRIMTester
# -------------------------------------------------------------------------
class GRIMTester:
    """
    Extracts reported means from scientific text and checks their consistency
    using the GRIM (Granularity-Related Inconsistency of Means) test.
    """

    # Initialization
    def __init__(self) -> None:
        self.api_key = API_KEY  # Get the API key from the config file
        self.client = OpenAI(api_key=self.api_key)  # Initialize the OpenAI client

    # ------------------------------------------------------------------
    # GRIM core calculations
    # ------------------------------------------------------------------
    @staticmethod
    def grim_test(reported_mean: float, sample_size: int, decimals: int = 2) -> bool:
        """
        Check if the reported mean is mathematically possible given the sample size and a specified number of decimal places.

        :param reported_mean: The mean value reported in the study.
        :param sample_size: The number (N) of samples in the study.
        :param decimals: The number of decimal places to check against (default is 2).
        :return: True if the reported mean is possible, False if it is impossible.
        """
        total_sum = reported_mean * sample_size
        possible_sum_1 = int(total_sum)      # Round down
        possible_sum_2 = possible_sum_1 + 1  # Round up

        return (
            round(possible_sum_1 / sample_size, decimals) == reported_mean
            or round(possible_sum_2 / sample_size, decimals) == reported_mean
        )

    @staticmethod
    def get_decimal_places(value_str: str) -> int:
        """
        Function to calculate the number of decimal places in a reported mean, including trailing zeros.

        :param value_str: The string representation of the reported mean.
        :return: The number of decimal places in the reported mean.
        """
        return len(value_str.split(".")[1]) if "." in value_str else 0

    # ------------------------------------------------------------------
    # OpenAI interaction
    # ------------------------------------------------------------------
    def extract_data_from_text(self, context: str) -> str | None:
        """
        Send context to the gpt-4o-mini model to extract reported means and sample sizes.
        The model will return test entries formatted like:

        tests = [
            {
                "reported_mean": "<mean>",
                "sample_size": <size>,
                "discrete_reasoning": "<justification>"
            },
            ...
        ]

        :param context: The context containing reported means and sample sizes.
        :return: The extracted test data as a string.
        """
        prompt = GRIM_PROMPT.format(context=context)

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that extracts reported means and their sample sizes only when the data are explicitly integer-based.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.01,
        )

        response_content = response.choices[0].message.content.strip()

        # Remove any code blocks that might wrap the response
        response_content = (
            response_content.replace("```python", "")
            .replace("```json", "")
            .replace("```", "").strip()
        )

        # Results must start with 'tests ='
        if response_content.startswith("tests ="):
            return response_content[len("tests = ") :].strip()

        return None

    # ------------------------------------------------------------------
    # File reading
    # ------------------------------------------------------------------
    @staticmethod
    def read_context_from_file(file_path: str) -> List[str]:
        """
        Reads the context from a .txt, .pdf, .html, or .htm file and splits it into segments.

        :param file_path: The path to the file containing the context.
        :return: A list of context segments, each as a string.
        """
        try:
            # Get the lowercase file extension
            extension = os.path.splitext(file_path.strip())[-1].lower()

            # Read file content based on its extension
            if extension == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()

            elif extension == ".pdf":
                text = ""
                with fitz.open(file_path) as doc:
                    for page in doc:
                        text += page.get_text() + "\n"

            elif extension in (".html", ".htm"):
                with open(file_path, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f, "html.parser")
                    text = soup.get_text(separator=" ")

            else:
                print("Unsupported file type. Please supply a .txt, .pdf, .html, or .htm file.")
                return []

            # Split text into overlapping segments
            words = text.split()
            segments = []
            step = MAX_WORDS - OVERLAP_WORDS # Get variables from config.py

            for i in range(0, len(words), step):
                segment = words[i:i + MAX_WORDS]
                segments.append(" ".join(segment))

            return segments

        except FileNotFoundError:
            print("File not found. Please provide a valid path.")
            return []

    # ------------------------------------------------------------------
    # GRIMTester pipeline entry point
    # ------------------------------------------------------------------
    def perform_grim_test(self, file_context: List[str]) -> pd.DataFrame | None:
        """
        Extract test data from context segment(s) and perform the GRIM test.
        Only display results where GRIM is applicable based on decimal resolution.

        :param file_context: A list of context segments.
        :return: None, prints the results of the GRIM test.
        """
        all_tests: List[Dict] = []

        # ------------------------------ Extraction loop ------------------------------
        for idx, context in enumerate(file_context):
            print(f"Processing segment {idx + 1}/{len(file_context)}...")
            test_data = self.extract_data_from_text(context)
            if test_data is None:
                continue

            try:
                tests = ast.literal_eval(test_data)
                if isinstance(tests, list) and all(
                    isinstance(t, dict)
                    and "reported_mean" in t
                    and "sample_size" in t
                    and "discrete_reasoning" in t
                    for t in tests
                ):
                    all_tests.extend(tests)
            except (SyntaxError, ValueError) as err:
                print(f"Error parsing extracted data: {err}")

        # ------------------------------ Run GRIM -------------------------------------
        if not all_tests:
            return None

        results: List[Dict] = []
        for test in all_tests:
            reported_mean_str = str(test["reported_mean"])
            reported_mean_float = float(reported_mean_str)
            sample_size = int(test["sample_size"])
            reasoning = test.get("discrete_reasoning", "")

            if sample_size <= 0:
                continue

            decimals = self.get_decimal_places(reported_mean_str)
            grim_threshold = 10 ** decimals
            is_applicable = sample_size <= grim_threshold
            passed = self.grim_test(reported_mean_float, sample_size, decimals)

            # ------------------ Append result ------------------
            results.append(
                {
                    "Consistent": "Yes" if passed else "No",
                    "Reported Mean": reported_mean_str,
                    "Sample Size": sample_size,
                    "Decimals": decimals,
                    "Reasoning": reasoning,
                    "Applicable": is_applicable,
                }
            )

        # ------------------------------ Return results --------------------------------
        df = pd.DataFrame(results)
        df = df[df["Applicable"]]  # Apply formula: only show GRIM-applicable results (sample size constraint)
        df = df.drop_duplicates(subset=["Reported Mean", "Sample Size"])
        df = df[
            ["Consistent", "Reported Mean", "Sample Size", "Decimals", "Reasoning"]
        ]

        return df if not df.empty else None
