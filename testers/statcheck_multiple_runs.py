"""
statcheck Tester.
Use AI to automatically extract reported statistical tests from scientific text and perform the statcheck to check for inconsistencies.
"""

import ast
import os
import time
from collections import Counter
from io import StringIO

import fitz  # PyMuPDF
import openai
import pandas as pd
import scipy.stats as stats
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Set pandas display options for better readability
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 10000)
pd.set_option("display.colheader_justify", "center")
pd.set_option("display.max_rows", None)

# Load environment variables from the .env file
load_dotenv()


class StatcheckTester:
    def __init__(self):
        # Retrieve the OpenAI API key from the .env file
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.Client()  # Initialize the OpenAI client
        openai.api_key = self.api_key  # Set the OpenAI API key

    def calculate_p_value(
        self, test_type, df1, df2, test_value, operator, reported_p_value, tail="two"
    ) -> tuple:
        """
        Calculate the valid p-value range for different statistical tests.

        :param test_type: The type of statistical test ('r', 't', 'f', 'chi2', 'z').
        :param df1: The first degree of freedom.
        :param df2: The second degree of freedom (use None for tests that only need one df).
        :param test_value: The test statistic value.
        :param operator: The operator used in the reported p-value ('=', '<', '>').
        :param reported_p_value: The numerical value of the reported p-value.
        :param tail: Specify 'one' for one-tailed test or 'two' for two-tailed test (default is 'two').
        :return: Tuple containing:
            - Consistency (True if reported p-value falls within recalculated p-value range, False otherwise).
            - Recalculated valid p-value range (lower, upper).
        """
        # Check if any critical parameter is None
        if (
            test_value is None
            or (test_type in ["t", "r", "chi2"] and df1 is None)
            or (test_type == "f" and (df1 is None or df2 is None))
        ):
            return False, (None, None)

        # Calculate the rounding boundaries for the test statistic
        decimal_places = max(
            self.get_decimal_places(str(test_value)), 2
        )  # Treat 1 decimal as 2
        rounding_increment = 0.5 * 10 ** (-decimal_places)
        lower_test_value = test_value - rounding_increment
        upper_test_value = test_value + rounding_increment - 1e-10

        # For t-tests and similar, calculate p-values at the lower and upper test_value bounds
        if test_type == "r":
            # Correlation test (r)
            # Convert to t-values
            t_lower = (
                lower_test_value * ((df1) ** 0.5) / ((1 - lower_test_value**2) ** 0.5)
            )
            t_upper = (
                upper_test_value * ((df1) ** 0.5) / ((1 - upper_test_value**2) ** 0.5)
            )

            # Calculate p-values at lower and upper test_value bounds
            p_lower = stats.t.sf(abs(t_lower), df1)
            p_upper = stats.t.sf(abs(t_upper), df1)

        elif test_type == "t":
            # t-test
            # Calculate p-values at lower and upper test_value bounds
            p_lower = stats.t.sf(abs(lower_test_value), df1)
            p_upper = stats.t.sf(abs(upper_test_value), df1)

        elif test_type == "f":
            # F-test
            # Calculate p-values at lower and upper test_value bounds
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

        # Compare recalculated p-values with the reported p-value
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
        if "." in value_str:
            return len(value_str.split(".")[1])

        else:
            return 0

    def compare_p_values(
        self, recalculated_p_value_range, operator, reported_value
    ) -> bool:
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
        prompt = f"""
        You are an AI assistant that extracts statistical test results from scientific text.

        Please extract ALL statistical tests reported in the following text. For each test, extract the following components:

        - test_type: one of 'r', 't', 'f', 'chi2', 'z'.
        - df1: First degree of freedom (float or integer). If not applicable, set to None.
        - df2: Second degree of freedom (float or integer). If not applicable, set to None.
        - test_value: The test statistic value (float).
        - operator: The operator used in the reported p-value ('=', '<', '>').
        - reported_p_value: The numerical value of the reported p-value (float) if available, or 'ns' if reported as not significant.
        - tail: 'one' or 'two'. Assume 'two' unless explicitly stated.

        Guidelines:

        - Be tolerant of minor typos or variations in reporting.
        - Recognize tests even if they are embedded in sentences or reported in a non-standard way.
        - **Pay special attention to distinguishing between chi-square tests (often denoted as 'χ²' or 'chi2') and F-tests. Example: "𝜒2 (df =97)=80.12, p=.893"**
        - A chi-sqaure test can also be reported as "G-square", "G^2", or "G2". Example: G2(18) = 17.50, p =.489, is a chi2 test. The test type should still be chi2.
        - **IMPORTANT: "rho" is not the same as "r". Do not interpret "rho" as an "r" test.**
        - Extract the correct operator from the p-value (e.g., '=', '<', '>').
        - For p-values reported with inequality signs (e.g., p < 0.05), extract both the operator ('<') and the numerical value (0.05). This goes for all operators.
        - Do not perform any calculations or inferences beyond what's explicitly stated.
        - It can occur that a test is split over multiple sentences. Example: "F"(1, 25) = 11.36, MSE = .040, ηp
        2 =
        .312, p = .002". Make sure to extract the test correctly, pay close attention to the operator.
        - If ANY of the components are missing or unclear, skip that test, especially the test_value.
        - Treat commas in numbers as thousand separators, not decimal points. Remove commas from numbers before extracting them. For example, '16,107' should be extracted as '16107' (sixteen thousand one hundred seven), not '16.107'.
        - Regarding chi2 tests: do not extract the sample size (N).
        - Only an F-test requires two degrees of freedom (df1, df2). For all other tests, only extract df1.
        - It can occur that a thousand separator (,) is used in the degree(s) of freedom. Example: "r(31,724) = -0.02" has df1 = 31724.
        - Do not extract tests that have not been described in this prompt before. Example: "B(31,801) = -.030, p <.001" should not be extracted, since the test type 'B' has not been described in the prompt.
        - Again, never extract other tests than the ones described in this prompt!

        Format the result EXACTLY like this:

        tests = [
            {{"test_type": "<test_type>", "df1": <df1>, "df2": <df2>, "test_value": <test_value>, "operator": "<operator>", "reported_p_value": <reported_p_value>, "tail": "<tail>"}},
            ...
        ]

        Now, extract the tests from the following text:

        {context}

        After you have read the text above, read it again to ensure you understand the instructions. Then, extract the reported statistical tests as requested.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that extracts statistical test values from scientific text.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )

        response_content = response.choices[
            0
        ].message.content  # Choose the first response from the OpenAI API
        response_content = (
            response_content.replace("```python", "").replace("```", "").strip()
        )  # Clean up the response

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
                print(
                    "Unsupported file format. Please provide a .txt, .pdf, .html, or .htm file."
                )
                return []

            # Split the text into words
            words = text.split()
            # Maximum words per segment
            max_words = 500
            # Number of words to overlap between segments
            overlap = 8
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

    def determine_reported_significance(
        self, operator, reported_p_value, significance_level
    ) -> bool:
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

    def determine_recalculated_significance(
        self, p_value_range, significance_level
    ) -> bool:
        """
        Determine the significance of the RECALCULATED p-value range based on the significance level.

        :param p_value_range: Tuple (lower, upper) of the recalculated p-value range.
        :param significance_level: The significance level (now hardcoded at 0.05).
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

        :param context_segments: A list of context segments.
        :return: None, prints the results of the statcheck test.
        """
        significance_level = 0.05  # Hardcode the significance level at 0.05
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
                tail = test.get("tail")

                # skip if reported p-value is None
                if reported_p_value is None:
                    continue

                # Check if "ns" was reported
                if reported_p_value == "ns":
                    # Handle 'ns' case by skipping calculation
                    apa_reporting = f"{test_type}({df1}{', ' + str(df2) if df2 is not None else ''}) = {test_value}, ns"
                    notes = "Reported as ns"
                    consistent_str = "N/A"  # No consistency check
                    valid_p_value_range_str = "N/A"

                else:
                    # Existing consistency check and recalculation code
                    consistent, p_value_range = self.calculate_p_value(
                        test_type,
                        df1,
                        df2,
                        test_value,
                        operator,
                        reported_p_value,
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
                    reported_significant = self.determine_reported_significance(
                        operator, reported_p_value, significance_level
                    )

                    # Determine if recalculated p-value range indicates significance at the 0.05 level
                    if p_value_range[0] is not None and p_value_range[1] is not None:
                        recalculated_significant = (
                            self.determine_recalculated_significance(
                                p_value_range, significance_level
                            )
                        )
                    else:
                        recalculated_significant = None

                    # Determine if there is a gross inconsistency (difference in significance)
                    gross_inconsistency = False
                    if (
                        reported_significant is not None
                        and recalculated_significant is not None
                    ):
                        if reported_significant != recalculated_significant:
                            gross_inconsistency = True  # Difference in significance

                    # Set empty notes based on consistency and gross inconsistency
                    notes_list = []

                    if reported_p_value == 0:
                        notes_list.append("A p-value is never exactly 0.")
                        consistent = False

                    if p_value_range[0] is None and test_type == "f" and df2 is None:
                        notes_list.append(
                            "F-test requires two DF. Only one DF provided."
                        )
                        consistent_str = "Cannot determine"
                    else:
                        if not consistent:
                            if gross_inconsistency:
                                notes_list.append(
                                    "Gross inconsistency: reported p-value and recalculated p-value differ in significance."
                                )
                            else:
                                notes_list.append(
                                    "Recalculated p-value does not match the reported p-value."
                                )
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
                                tail="one",
                            )
                            if consistent_one_tailed:
                                notes_list.append(
                                    "Consistent for one-tailed, inconsistent for two-tailed"
                                )

                    notes = "-" if not notes_list else " ".join(notes_list)

                # Format APA Reporting
                if df1 is not None:
                    apa_reporting = f"{test_type}({df1}{', ' + str(df2) if df2 is not None else ''}) = {test_value:.2f}"
                else:
                    # For z-tests
                    apa_reporting = f"{test_type} = {test_value:.2f}"

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


# Usage:
if __name__ == "__main__":
    # Record the start time
    start_time = time.time()

    tester = StatcheckTester()

    # Prompt the user to provide the file path
    file_path = input(
        "Please provide the file path to the context you want to analyse:\n"
    )

    # Read the context segments from the provided file path
    file_context = tester.read_context_from_file(file_path)

    # If context segments were successfully read, extract the data and perform the statcheck test
    if file_context:
        #  Perform the statcheck test multiple times (in this case 3) to find the most consistent result
        results_list = []
        for i in range(1):
            print(f"Run {i+1} of 3")
            result_df = tester.perform_statcheck_test(file_context)
            if result_df is not None:
                results_list.append(result_df)
            else:
                print("No results in this run.")

        # Compare the results and find the most frequent one
        # Convert each DataFrame to a string representation
        results_str_list = [df.to_csv(index=False) for df in results_list]
        # Count the frequencies
        counts = Counter(results_str_list)
        # Find the most common result
        if counts:
            most_common_result_str, frequency = counts.most_common(1)[0]
            # Convert the string back to a DataFrame
            most_common_df = pd.read_csv(StringIO(most_common_result_str))
            # Display the most frequent result
            print("\nMost frequent result:")
            print(most_common_df)
        else:
            print("Inconsistent results, please run the test again.")

    # Calculate and print the total running time
    total_time = time.time() - start_time
    print(f"\nTotal running time: {total_time:.2f} seconds")
