"""
Core logic for extracting statistical tests and running AI-powered statcheck.
Use AI to automatically extract reported statistical tests from scientific text and perform the statcheck to check for inconsistencies.

Credits
-------
Functionality is heavlity inspired by the original statcheck tool, created by Michèle Nuijten.
(https://github.com/MicheleNuijten/statcheck)
(https://michelenuijten.shinyapps.io/statcheck-web/)
"""

import ast
import os

import fitz  # PyMuPDF
import openai
import pandas as pd
import scipy.stats as stats
from bs4 import BeautifulSoup

# Local imports
from config import (
    API_KEY,
    MAX_WORDS,
    OVERLAP_WORDS,
    SIGNIFICANCE_LEVEL,
    STATCHECK_PROMPT,
    apply_pandas_display_options,
)
from openai import OpenAI

# ------------------------------------------------------------------------- 
# Pandas display options
# -------------------------------------------------------------------------
apply_pandas_display_options() # Applies pandas display options for better readability

# ------------------------------------------------------------------------- 
# Main class, StatcheckTester
# -------------------------------------------------------------------------
class StatcheckTester:
    """
    Extracts NHST tests from scientific text using AI and checks their consistency using Python.
    """

    # Initialization
    def __init__(self) -> None:
        self.api_key = API_KEY # Get the API key from the config file
        openai.api_key = self.api_key
        self.client = OpenAI() # Initialize the OpenAI client

    def calculate_p_value(self, test_type, df1, df2, test_value, operator, reported_p_value, epsilon, tail="two") -> tuple:
        """
        Calculate the valid p-value range for different statistical tests.

        :param test_type: The type of statistical test ('r', 't', 'f', 'chi2', 'z').
        :param df1: The first degree of freedom.
        :param df2: The second degree of freedom (use None for tests that only need one df).
        :param test_value: The test statistic value.
        :param operator: The operator used in the reported p-value ('=', '<', '>').
        :param reported_p_value: The numerical value of the reported p-value.
        :param epsilon: The epsilon value for Huynh-Feldt correction (use None if not applicable).
        :param tail: Specify 'one' for one-tailed test or 'two' for two-tailed test (default is 'two').
        :return: Tuple containing:
            - Consistency (True if reported p-value falls within recalculated p-value range, False otherwise).
            - Recalculated valid p-value range (lower, upper).
        """
        # Check if any critical parameter is None
        if (test_value is None
            or (test_type in ["t", "r", "chi2"] and df1 is None)
            or (test_type == "f" and (df1 is None or df2 is None))):
            return False, (None, None)

        # Calculate the rounding boundaries for the test statistic
        decimal_places = max(self.get_decimal_places(str(test_value)), 2)  # Treat 1 decimal as 2
        rounding_increment = 0.5 * 10 ** (-decimal_places)
        lower_test_value = test_value - rounding_increment
        upper_test_value = test_value + rounding_increment - 1e-10

        # For t-tests and similar, calculate p-values at the lower and upper test_value bounds
        if test_type == "r":
            # Correlation test (r)
            # Convert to t-values
            t_lower = (lower_test_value * ((df1) ** 0.5) / ((1 - lower_test_value**2) ** 0.5))
            t_upper = (upper_test_value * ((df1) ** 0.5) / ((1 - upper_test_value**2) ** 0.5))

            # Calculate p-values at lower and upper test_value bounds
            p_lower = stats.t.sf(abs(t_lower), df1)
            p_upper = stats.t.sf(abs(t_upper), df1)

        elif test_type == "t":
            # t-test
            # Calculate p-values at lower and upper test_value bounds
            p_lower = stats.t.sf(abs(lower_test_value), df1)
            p_upper = stats.t.sf(abs(upper_test_value), df1)

        elif test_type == "f":
            # Only apply the Huynh-Feldt correction if epsilon is not None and df1, df2 are both integers
            if epsilon is not None and isinstance(df1, int) and isinstance(df2, int):
                corrected_df1 = epsilon * df1
                corrected_df2 = epsilon * df2
                p_lower = stats.f.sf(lower_test_value, corrected_df1, corrected_df2)
                p_upper = stats.f.sf(upper_test_value, corrected_df1, corrected_df2)
            else:
                # Standard F-test (or df1/df2 are already floats, implying correction was applied previously)
                p_lower = stats.f.sf(lower_test_value, df1, df2)
                p_upper = stats.f.sf(upper_test_value, df1, df2)


        elif test_type == "chi2":
            # Chi-square test
            # Calculate p-values at lower and upper test_value bounds
            p_lower = stats.chi2.sf(lower_test_value, df1)
            p_upper = stats.chi2.sf(upper_test_value, df1)

        elif test_type == "z":
            # Z-test (does not require degrees of freedom)
            # Calculate p-values at lower and upper test_value bounds
            p_lower = stats.norm.sf(abs(lower_test_value))
            p_upper = stats.norm.sf(abs(upper_test_value))

        else:
            # Unknown test type
            return False, (None, None)

        # Adjust for one-tailed or two-tailed tests where applicable (not for chi2 and f)
        if test_type not in ["chi2", "f"]:
            if tail == "two":
                # For two-tailed tests, double the one-tailed p-value
                p_lower = min(p_lower * 2, 1)
                p_upper = min(p_upper * 2, 1)
            elif tail != "one":
                return False, (None, None)

        # Ensure p_lower is the smaller p-value
        p_value_lower = min(p_lower, p_upper)
        p_value_upper = max(p_lower, p_upper)

        # Handle reported_p_value being 'ns'
        if reported_p_value == "ns":
            return False, (p_value_lower, p_value_upper)

        # Convert reported_p_value to numeric if possible
        try:
            reported_p_value = float(reported_p_value)
        except ValueError:
            # Cannot convert to numeric
            return False, (None, None)

        consistent = self.compare_p_values(
            (p_value_lower, p_value_upper), operator, reported_p_value
        )


        return consistent, (p_value_lower, p_value_upper)

    def get_decimal_places(self, value_str) -> int:
        """
        Function to calculate the number of decimal places in a value, including trailing zeros.

        :param value_str: The string representation of the value.
        :return: The number of decimal places in the value.
        """
        # Base case: if there is no decimal point, return 0
        if "." not in value_str:
            return 0
        if "." in value_str:
            return len(value_str.split(".")[1])

        else:
            return 0

    def compare_p_values(self, recalculated_p_value_range, operator, reported_value) -> bool:
        """
        Compare recalculated valid p-value range with reported p-value.

        :param recalculated_p_value_range: Tuple (p_value_lower, p_value_upper).
        :param operator: The operator used in the reported p-value ('=', '<', '>').
        :param reported_value: The numerical value of the reported p-value.
        :return: True if consistent, False otherwise.
        """
        # Unpack the recalculated p-value range from the tuple
        p_value_lower, p_value_upper = recalculated_p_value_range

        if operator == "<":
            # Return True if lower bound is less than reported value
            if p_value_lower < reported_value:
                return True

        elif operator == ">":
            # Return True if upper bound is greater than reported value
            if p_value_upper > reported_value:
                return True

        elif operator == "=":
            # Determine the rounding boundaries for the reported p-value
            if "." in str(reported_value):
                decimal_places = self.get_decimal_places(str(reported_value))
            else:
                decimal_places = 0

            rounding_increment = 0.5 * 10 ** (-decimal_places)
            reported_p_lower = reported_value - rounding_increment
            reported_p_upper = reported_value + rounding_increment - 1e-10

            # Check if the reported p-value falls within the recalculated range
            if reported_p_upper >= p_value_lower and reported_p_lower <= p_value_upper:
                return True

            else:
                return False

    def extract_data_from_text(self, context) -> str:
        """
        Send context to the gpt-4o-mini model to extract reported statistical tests.
        The model will return the extracted statistical tests as a list of dictionaries (still in string format).
        The list of dictionaries will look like this:
        tests = [
            {"test_type": "<test_type>", "df1": <df1>, "df2": <df2>, "test_value": <test_value>, "operator": "<operator>", "reported_p_value": <reported_p_value>, "tail": "<tail>"},
            ...
        ]

        :param context: The scientific text containing reported statistical tests.
        :return: The extracted test data as a string.
        """
        prompt = STATCHECK_PROMPT.format(context=context)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system",
                    "content": "You are an assistant that extracts statistical test values from scientific text.",},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )

        response_content = response.choices[0].message.content  # Choose the first response from the OpenAI API
        response_content = (response_content.replace("```python", "").replace("```", "").strip())  # Clean up the response

        # Check if the response contains the expected format
        if response_content.startswith("tests ="):
            # Remove the 'tests =' part, only the list of dictionaries is preserved, still in string format
            response_content = response_content[len("tests = ") :].strip()
        else:
            print("Error: The response does not contain the expected format.")
            return None

        # List of dictionaries (in string format)
        return response_content

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
            max_words = MAX_WORDS # Get the max words from the config file
            # Number of words to overlap between segments
            overlap = OVERLAP_WORDS # Get the overlap from the config file
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

    def determine_reported_significance(self, operator, reported_p_value, significance_level) -> bool:
        """
        Determine the significance of the REPORTED p-value based on the provided operator and significance level.

        :param operator: The operator used in the reported p-value ('=', '<', '>').
        :param reported_p_value: The numerical value of the reported p-value.
        :return: True if significant, False if not significant.
        """
        if operator == "=" or operator == "<":
            if reported_p_value <= significance_level:
                return True
            else:
                return False
        elif operator == ">":
            if reported_p_value >= significance_level:
                return False
            else:
                return True
        else:
            return False  # Invalid operator

    def determine_recalculated_significance(self, p_value_range, significance_level) -> bool:
        """
        Determine the significance of the RECALCULATED p-value range based on the significance level.

        :param p_value_range: Tuple (lower, upper) of the recalculated p-value range.
        :param significance_level: The significance level (set at 0.05 in cofig file).
        :return: True if significant, False if not significant.
        """
        if p_value_range[1] < significance_level:
            return True

        elif p_value_range[0] > significance_level:
            return False

        else:
            return None

    def perform_statcheck_test(self, file_context) -> None:
        """
        Extract test data from context segment(s) and perform statcheck.

        :param file_context: A list of context segments.
        :return: A pandas DataFrame containing the statcheck results (or None if no results).
        """
        significance_level = SIGNIFICANCE_LEVEL  # Get the significance level from the config file
        all_tests = []

        # Use enumerate to get the index of the segment
        # Iterate over each segment in the file_context
        for idx, context in enumerate(file_context):
            print(f"Processing segment {idx + 1}/{len(file_context)}...")
            test_data = self.extract_data_from_text(context)

            if test_data is not None:  # Valid test data is found
                # Convert the extracted data from a string to a list of dictionaries
                tests = ast.literal_eval(test_data)
                for test in tests:
                    # Check if all_tests is not empty and the last test is the same as the current test
                    # This is to avoid adding duplicate tests that span multiple segments due to overlap
                    if all_tests and test == all_tests[-1]:
                        continue  # Skip adding the duplicate test
                    all_tests.append(test)
            else:
                # No valid test data found in the segment
                continue

        # Perform the statcheck test for each extracted test
        if all_tests:
            statcheck_results = []

            for test in all_tests:
                test_type = test.get("test_type")
                df1 = test.get("df1")
                df2 = test.get("df2")
                test_value = test.get("test_value")
                operator = test.get("operator")
                reported_p_value = test.get("reported_p_value")
                epsilon = test.get("epsilon")
                tail = test.get("tail")

                # skip if reported p-value is None
                if reported_p_value is None or test_value is None:
                    continue

                # Check if "ns" was reported
                if reported_p_value == "ns":
                    # Initialize notes_list
                    notes_list = ["Reported as ns"]

                    # Handle 'ns' case by skipping calculation
                    apa_reporting = f"{test_type}({df1}{', ' + str(df2) if df2 is not None else ''}) = {test_value}, ns"
                    consistent_str = "N/A"  # No consistency check
                    valid_p_value_range_str = "N/A"

                else:
                    # Consistency check and recalculation code
                    consistent, p_value_range = self.calculate_p_value(
                        test_type,
                        df1,
                        df2,
                        test_value,
                        operator,
                        reported_p_value,
                        epsilon if (test_type == "f" and epsilon is not None and isinstance(df1, int) and isinstance(df2, int)) else None,
                        tail,
                    )

                    # Skip the test if valid p-value range could not be calculated
                    if p_value_range[0] is None and p_value_range[1] is None:
                        continue

                    # Format Valid P-value Range
                    valid_p_value_range_str = (
                        f"{p_value_range[0]:.5f} to {p_value_range[1]:.5f}"
                        if all(p_value_range)
                        else "N/A"
                    )

                    # Determine if reported p-value indicates significance at the 0.05 level
                    reported_significant = self.determine_reported_significance(operator, reported_p_value, significance_level)

                    # Determine if recalculated p-value range indicates significance at the 0.05 level
                    if p_value_range[0] is not None and p_value_range[1] is not None:
                        recalculated_significant = self.determine_recalculated_significance(p_value_range, significance_level)
                    else:
                        recalculated_significant = None

                    # Determine if there is a gross inconsistency (difference in significance)
                    gross_inconsistency = False
                    if (reported_significant is not None and recalculated_significant is not None):
                        if reported_significant != recalculated_significant:
                            gross_inconsistency = True  # Difference in significance

                    # Set empty notes based on consistency and gross inconsistency
                    notes_list = []

                    if reported_p_value == 0:
                        notes_list.append("A p-value is never exactly 0.")
                        consistent = False

                    if p_value_range[0] is None and test_type == "f" and df2 is None:
                        notes_list.append("F-test requires two DF. Only one DF provided.")
                        consistent_str = "Cannot determine"
                    else:
                        if not consistent:
                            if gross_inconsistency:
                                notes_list.append("Gross inconsistency: reported p-value and recalculated p-value differ in significance.")
                            else:
                                notes_list.append("Recalculated p-value does not match the reported p-value.")
                        consistent_str = "Yes" if consistent else "No"

                    # Add note for one-tailed consistency
                    if test_type in ["t", "z", "r"] and not consistent:
                        if tail == "two":
                            # Recalculate consistency assuming tail='one'
                            consistent_one_tailed, _ = self.calculate_p_value(
                                test_type,
                                df1,
                                df2,
                                test_value,
                                operator,
                                reported_p_value,
                                None,  # No epsilon for t, z, or r
                                tail="one",
                            )
                            if consistent_one_tailed:
                                notes_list.append("Consistent for one-tailed, inconsistent for two-tailed")

                # Format APA Reporting
                if (
                    test_type == "f"
                    and epsilon is not None
                    and isinstance(df1, int)
                    and isinstance(df2, int)
                ):
                    # Round new df values to 2 decimals
                    corrected_df1 = round(epsilon * df1, 2)
                    corrected_df2 = round(epsilon * df2, 2)
                    apa_reporting = f"{test_type}({corrected_df1}, {corrected_df2}) = {test_value:.2f}"
                    notes_list.append(f"Degrees of freedom were adjusted due to a Huynh-Feldt correction. Epsilon = {epsilon}")
                elif df1 is not None:
                    apa_reporting = f"{test_type}({df1}{', ' + str(df2) if df2 is not None else ''}) = {test_value:.2f}"
                else:
                    # For z-tests or any test not requiring df
                    apa_reporting = f"{test_type} = {test_value:.2f}"

                notes = "-" if not notes_list else " ".join(notes_list)

                # Add the test to statcheck_results
                statcheck_results.append(
                    {
                        "Consistent": consistent_str,
                        "APA Reporting": apa_reporting,
                        "Reported P-value": (
                            f"{operator} {reported_p_value}"
                            if reported_p_value != "ns"
                            else "ns"
                        ),
                        "Valid P-value Range": valid_p_value_range_str,
                        "Notes": notes,
                    }
                )

            # Display the results in a DataFrame
            if statcheck_results:
                df_statcheck_results = pd.DataFrame(statcheck_results)
                df_statcheck_results = df_statcheck_results[
                    [
                        "Consistent",
                        "APA Reporting",
                        "Reported P-value",
                        "Valid P-value Range",
                        "Notes",
                    ]
                ]

                # Set display options for better readability
                pd.set_option("display.max_colwidth", None)

                # Return instead of printing so the results can be compared
                return df_statcheck_results
            else:
                return None