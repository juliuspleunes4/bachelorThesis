"""
GRIM (Granularity-Related Inconsistency of Means) Test.
Use AI to automatically extract reported means and sample sizes from scientific text and perform the GRIM test to check for inconsistencies.
"""

import ast
import os

import fitz  # PyMuPDF
import openai
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Set pandas display options for better readability
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 10000)
pd.set_option("display.colheader_justify", "center")
pd.set_option("display.max_rows", None)
pd.set_option("display.max_colwidth", None)


# Load environment variables from the .env file
load_dotenv()


class GRIMTester:
    def __init__(self):
        # Retrieve the OpenAI API key from the .env file
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.Client()  # Initialize the OpenAI client
        openai.api_key = self.api_key  # Set the OpenAI API key

    def grim_test(self, reported_mean: float, sample_size: int, decimals: int = 2) -> bool:
        """
        Check if the reported mean is mathematically possible given the sample size and a specified number of decimal places.

        :param reported_mean: The mean value reported in the study.
        :param sample_size: The number (N) of samples in the study.
        :param decimals: The number of decimal places to check against (default is 2).
        :return: True if the reported mean is possible, False if it is impossible.
        """
        total_sum = reported_mean * sample_size
        possible_sum_1 = int(total_sum)  # Round down
        possible_sum_2 = possible_sum_1 + 1  # Round up

        if (round(possible_sum_1 / sample_size, decimals) == reported_mean
        or round(possible_sum_2 / sample_size, decimals) == reported_mean):
            return True
        else:
            return False

    def get_decimal_places(self, value_str) -> int:
        """
        Function to calculate the number of decimal places in a reported mean, including trailing zeros.

        :param value_str: The string representation of the reported mean.
        :return: The number of decimal places in the reported mean.
        """
        if "." in value_str:
            return len(value_str.split(".")[1])
        else:
            return 0

    def extract_data_from_text(self, context) -> str:
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

        :param context: The scientific text containing reported means and sample sizes.
        :return: The extracted test data as a string.
        """
        prompt = f"""
        You are an extraction assistant. Your task is to extract only reported **means and their sample sizes** from the following scientific text. You must follow these rules strictly:

        ---

        **Extract only if ALL of the following are true:**
        - The value is explicitly labeled as a **mean** (e.g., “M = ...”, “mean = ...”).
        - The mean is clearly based on **integer-valued response data** (e.g., responses on Likert-type scales like 1–5, 1–7, etc.).
        - A specific **sample size (N)** is provided in the same sentence, or in a directly connected clause or phrase.
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
        - Do not infer sample sizes from statistical test degrees of freedom (e.g., t(28) does not imply N=29).
        - If the total sample is split into groups (e.g., experimental/control), extract group-level means and sample sizes separately.
        - NEVER round mean values — extract them **exactly as reported**, preserving **all decimal places and trailing zeros** (e.g., keep `6.60`, not `6.6`).
        - Do **not** perform any calculations. Only extract what is explicitly stated in the text.

        ---

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

        # Clean up markdown formatting if present
        response_content = response_content.replace("```python", "").replace("```", "").strip()

        if response_content.startswith("json"):
            response_content = response_content[4:].strip()

        # print response_content per segment
        print(f"Response content: {response_content}")

        if response_content.startswith("tests ="):
            return response_content[len("tests = ") :].strip()
        else:
            return None


    def read_context_from_file(self, file_path) -> list:
        """
        Reads the context from a .txt, .pdf, .html, or .htm file and splits it into segments.

        :param file_path: The path to the file containing the context.
        :return: A list of context segments, each as a string.
        """
        try:
            # Remove any extra whitespace and get the file extension in lowercase
            file_extension = os.path.splitext(file_path.strip())[-1].lower()

            if file_extension == ".txt":
                with open(file_path, "r", encoding="utf-8") as file:
                    text = file.read()
            elif file_extension == ".pdf":
                # Use PyMuPDF to extract text from PDF
                text = ""
                with fitz.open(file_path) as doc:
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        page_text = page.get_text()
                        if page_text:
                            text += page_text + "\n"
            elif file_extension in (".html", ".htm"):
                # Use BeautifulSoup to extract text from HTML or HTM
                with open(file_path, "r", encoding="utf-8") as file:
                    soup = BeautifulSoup(file, "html.parser")
                    text = soup.get_text(separator=" ")
            else:
                print("Unsupported file format. Please provide a .txt, .pdf, .html, or .htm file.")
                return []

            # Split the text into words
            words = text.split()
            # Maximum words per segment
            max_words = 1000
            # Number of words to overlap between segments
            overlap = 200
            # Split words into overlapping segments
            segments = []
            i = 0
            while i < len(words):
                # Extract a segment with overlap
                segment = words[i : i + max_words]
                segments.append(" ".join(segment))
                # Move the index forward by max_words minus overlap
                i += max_words - overlap

            return segments
        except FileNotFoundError:
            print("The file was not found. Please provide a valid file path.")
            return []

    def perform_grim_test(self, file_context) -> None:
        """
        Extract test data from context segment(s) and perform the GRIM test.
        Only display results where GRIM is applicable based on decimal resolution.
        :param file_context: A list of context segments.
        :return: None, prints the results of the GRIM test.
        """
        all_tests = []

        for idx, context in enumerate(file_context):
            print(f"Processing segment {idx + 1}/{len(file_context)}...")
            test_data = self.extract_data_from_text(context)

            if test_data is not None:
                # Attempt to safely evaluate the list
                try:
                    tests = ast.literal_eval(test_data)

                    # Validate format
                    if isinstance(tests, list) and all(
                        isinstance(test, dict) and
                        "reported_mean" in test and
                        "sample_size" in test and
                        "discrete_reasoning" in test
                        for test in tests
                    ):
                        all_tests.extend(tests)
                    else:
                        print("Warning: Extracted data is not in the expected format.")
                except (SyntaxError, ValueError) as e:
                    print(f"Error parsing test data: {e}")

        # Perform the GRIM test
        if all_tests:
            grim_test_results = []

            for test in all_tests:
                reported_mean_str = str(test["reported_mean"])
                reported_mean_float = float(reported_mean_str)
                sample_size = test["sample_size"]
                reasoning = test.get("discrete_reasoning", "")

                if sample_size <= 0:
                    print(f"Skipping test with invalid sample size: {sample_size}")
                    continue

                decimals = self.get_decimal_places(reported_mean_str)

                # Determine if GRIM is applicable: sample size must be ≤ 10^decimals
                grim_threshold = 10 ** decimals
                is_grim_applicable = sample_size <= grim_threshold

                # Run GRIM test regardless, but we'll only show applicable results
                passed_grim_test = self.grim_test(reported_mean_float, sample_size, decimals)

                grim_test_results.append({
                    "Consistent": "Yes" if passed_grim_test else "No",
                    "Reported Mean": reported_mean_str,
                    "Sample Size": sample_size,
                    "Decimals": decimals,
                    "Reasoning": reasoning,
                    "Applicable": is_grim_applicable
                })

            # Create DataFrame and filter for GRIM-applicable results
            df = pd.DataFrame(grim_test_results)
            df = df[df["Applicable"]]  # Only show if GRIM can be applied
            df = df.drop_duplicates(subset=["Reported Mean", "Sample Size"])
            df = df[["Consistent", "Reported Mean", "Sample Size", "Decimals", "Reasoning"]]

            if not df.empty:
                print(df)
            else:
                print("No GRIM-applicable results to display.")
        else:
            print("No valid test data to process.")



# Usage:
if __name__ == "__main__":
    tester = GRIMTester()

    # Prompt the user to provide the file path
    file_path = input("Please provide the file path to the context you want to analyse:\n")

    # Read the context segments from the provided file path
    file_context = tester.read_context_from_file(file_path)

    # If context segments were successfully read, extract the data and perform the GRIM test
    if file_context:
        tester.perform_grim_test(file_context)
