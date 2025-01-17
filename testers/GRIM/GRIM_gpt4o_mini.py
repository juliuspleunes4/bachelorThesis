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
        """Function to calculate the number of decimal places in a reported mean, including trailing zeros.

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
            {{"reported_mean": "<mean>", "sample_size": <size>}},
            ...
        ]

        :param context: The scientific text containing reported means and sample sizes.
        :return: The extracted test data as a string.
        """
        prompt = f"""
        Extract ALL relevant reported means and sample sizes from the following text. Ensure that each extracted mean is based on integer data (e.g., Likert scale responses or other whole-number responses). Do not extract means that are based on continuous or floating-point data such as mean differences, survey completion times, or medians. **NEVER consider medians or other central tendencies, only means.**
        Again, only consider means that are COMPOSED OF INTEGER DATA. This has to be explicitly stated in the text.
        **IMPORTANT: Do NOT extract any statistical test values such as t-values, F-values, chi-square values (χ²), z-values, correlation coefficients (r-values), or any other test statistics. These are not means and should be ignored.**
        Do not perform any calculations. Simply identify and extract means that are composed of integer data, such as Likert-scale responses where individual responses are whole numbers, but keep the mean values exactly as reported (with decimal points if applicable). **NEVER CONSIDER MEDIANS OR OTHER CENTRAL TENDENCIES!**
        At every mean found, check again what the correlating sample size is. If not directly apparent, check if the sample size was mentioned earlier. Check if the initial sample size was split into groups, and if so, how many groups there were. For instance, check if there is an experimental condition and a control condition, and if so, how many participants were in each group.
        Extract ONLY the reported means and their corresponding sample sizes from the following text. **Do NOT extract medians, mean differences, survey completion times, statistical test values (like t-values, F-values, etc.), or any other central tendencies like median, mode, or ranges. Focus only on the values explicitly described as MEAN.**
        Make sure you extract every relevant mean down to the last decimal place, ALWAYS INCLUDE TRAILING ZEROS. If a mean is reported as 6.60, make sure to extract it as 6.60, not 6.6.
        A sample size is never 0!

        Format the result EXACTLY like this:
        tests = [
            {{"reported_mean": "<mean>", "sample_size": <size>}},
            ...
        ]

        {context}
        For every mean value found, ask yourself once again, is this mean value composed of integer data? Is it explicitly described as a mean (not a test statistic)? If the answer to both is yes, extract it.

        After you have read the text above, read it again to ensure you understand the instructions. Then, extract the reported means and sample sizes as requested.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                    "content": "You are an assistant that extracts mean values from scientific text.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        response_content = response.choices[0].message.content
        response_content = (response_content.replace("```python", "").replace("```", "").strip())

        if response_content.startswith("tests ="):
            response_content = response_content[len("tests = ") :].strip()
        else:
            print("Error: The response does not contain the expected format.")
            return None

        return response_content

    def read_context_from_file(self, file_path) -> str:
        """
        Reads the context from a .txt, .pdf, .html, or .htm file.

        :param file_path: The path to the file containing the context.
        :return: The entire context as a string.
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
                return ""

            return text
        except FileNotFoundError:
            print("The file was not found. Please provide a valid file path.")
            return ""


    def perform_grim_test(self, context) -> None:
        """Extract test data and perform GRIM testing.

        :param context: The scientific context, potentially containing reported means and sample sizes.
        :return: None, prints the results of the GRIM test.
        """
        test_data = self.extract_data_from_text(context)

        if test_data is None:
            print("No valid test data found.")
            return

        try:
            # Convert the extracted data from a string to a list of dictionaries
            tests = ast.literal_eval(test_data)
        except (ValueError, SyntaxError) as Error:
            print(f"Error processing the extracted data: {Error}")
            return

        if tests:
            grim_test_results = []

            for test in tests:
                reported_mean_str = test["reported_mean"]  # Keep the string with trailing zeros
                reported_mean_float = float(reported_mean_str)  # Convert to float for calculation
                sample_size = test["sample_size"]

                decimals = max(self.get_decimal_places(reported_mean_str), 2)  # Ensure at least 2 decimal places
                passed_grim_test = self.grim_test(reported_mean_float, sample_size, decimals)

                grim_test_results.append(
                    {
                        "Consistent": "Yes" if passed_grim_test else "No",
                        "Reported Mean": reported_mean_str,  # Use original string to show correct decimals
                        "Sample Size": sample_size,
                        "Decimals": decimals,
                    }
                )

            df_grim_results = pd.DataFrame(grim_test_results)
            df_grim_results = df_grim_results[["Consistent", "Reported Mean", "Sample Size", "Decimals"]]

            print(df_grim_results)
        else:
            print("No valid test data to process.")


# Usage:
if __name__ == "__main__":
    tester = GRIMTester()

    # Prompt the user to provide the file path
    file_path = input("Please provide the file path to the context you want to analyse:\n")

    # Read the context from the provided file path
    context = tester.read_context_from_file(file_path)

    # If the context was successfully read, extract the data and perform the GRIM test
    if context:
        tester.perform_grim_test(context)