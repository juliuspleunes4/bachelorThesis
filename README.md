# bachelorThesis
This project contains two AI-powered Python scripts which can be used for automated statistical error detection. The following tests are included: the **GRIM Test** & **Statcheck**. Both scripts leverage AI to extract data from provided files and then use Python to perfrom the necessary calculations. This is to ensure that the calculations are done correctly, since AI models are still prone to making errors when it comes to mathematics.

# Contents

- [Getting Started](#getting-started)
    - [Installation](#installation)
    - [Running the Tests](#running-the-tests)
- [GRIM Test](#grim-test)
    - [How It Works](#how-it-works)
- [Statcheck](#statcheck)
    - [How It Works](#how-it-works)
- [Important Tips](#important-tips)
- [Known issues](#known-issues)
    - [GRIM-Related Issues](#grim-related-issues)
    - [Statcheck-Related Issues](#statcheck-related-issues)

# Getting Started

## Installation
First, download the source code from this repository. Make sure Python 3.9.7 is installed, using which you can install all dependencies by executing `pip install -r requirements.txt` in the root directory of this project. After all dependencies have successfully installed, create a `.env` file in the root directory of the project. This file should contain your environment variables. For this project, only the OpenAI API key is relevant. The `.env` file should be formattted as follows:

`OPENAI_API_KEY = "your_openai_api_key_here"`


Once this is done, everything should be installed and ready for use.

## Running the Tests
You can run the GRIM Test and StatCheck scripts by executing their corresponding Python file and providing the path to your `.txt` or `.pdf` file when prompted.

 - To run the **GRIM Test**:
   
   Execute `python GRIM-gpt4o-mini.py`
 - To run **Statcheck**:

   Execute `python statcheck-gpt4o-mini.py`


# GRIM Test

The GRIM Test (Granularity-Related Inconsistency of Means) is a tool for detecting inconsistencies in reported statistical means within scientific texts. This code automates this test by using the `GPT-4o-mini` AI model to automatically extract reported means and sample sizes from a provided file. The code then uses the `grim_test` method to perform calculations using Python.

> [!IMPORTANT]
> The test only works for means that are composed of integer data, since the calculation relies on the granularity of whole numbers to determine whether the mean is mathematically possible given the sample size. 


## How it Works

1. **Central Class**: The `GRIMTester` class contains all methods for reading context from files, extracting reported means, conducting the GRIM test, and presenting results.
2. **Convert**: The `.txt` or `.pdf` file gets converted into plain text.
   
3. **Extract Data**: The `extract_data_from_text` method uses the `GPT-4o-mini` AI model to identify and extract reported means and sample sizes from the text. The model is inscructed to only extract means that are composed of integer data. The output is formatted according to the specified requirements, so it can be used by other methods in the class.

4. **GRIM Test**: The `grim_test` method checks if the reported mean is mathematically possible based on the sample size and the specified number of decimal places. 

5. **Processing Results**: After extraction and testing, the results are added into a DataFrame and printed. Each test is displayed in a separate row with the following column headers:

    - `Consistent`: Displays whether the reported mean passed the GRIM test (`Yes` for consistent, `No` for inconsistent).
    - `Reported Mean`: Displays the original mean value as extracted from the text, including any trailing zeros.
    - `Sample Size`: The corresponding sample size used for each reported mean.
    - `Decimals`: Displays the number of decimal places in the reported mean.



# Statcheck
Statcheck is a tool for checking the consistency of reported statistical test results in scientific texts. It works as a "spellchecker" for statistics. It recalculates a valid p-value range based on the corresponding test statistic and degree(s) of freedom. If the reported p-value falls within this valid range of p-values, the test is considered to be consistent. If the reported p-value does not fall within this range of valid p-values, the test is considered to be inconsistent. This script can recognise the following NHST results: t-tests, F-tests, correlations (r), z-tests & $\chi^2$ -tests.

> [!IMPORTANT]
> The script calculates a valid range of p-values, and the reported p-value must fall within this range to be considered consistent. There are two types of inconsistencies in which the script makes a distinction: _regular_ and _gross inconsistencies_. A _gross inconsistency_ occurs when a reported p-value indicates statistical significance, but the recalculated p-values show otherwise, or vice versa. A _regular inconsistency_ occurs when the reported p-value does not fall within the valid p-value range, but the (in)significance remains unchanged. 

### Example:

For a reported t-test with `t(30) = 1.96` and `p = 0.0587`, the script calulates a valid p-value range between the largest and the smallest possible numbers that still round to `1.96`.

- Lower bound: `t = 1.964999...` gives a p-value of `0.05873`.
- Upper bound: `t = 1.955` gives a p-value of `0.05996`.

Since the reported p-value of `0.0587` falls between the recalculated range `0.05873 to 0.05996`, the test is consistent:

## How It Works
1. **Central Class**: The `StatcheckTester` class contains all methods for reading context from files, extracting reported  statistical tests, recalculating a valid p-value range, comparison and presenting results.
2. **Convert**: The `.txt` or `.pdf` file gets converted into plain text.
   
3. **Extract Data**: The `extract_data_from_text` method uses the `GPT-4o-mini` AI model to identify and extract reported statistical tests from the text. The output is formatted according to the specified requirements, so it can be used by other methods in the class. The model can extract the following parameters:

    - `test_type`: One of `'r'`, `'t'`, `'f'`, `'chi2'`, `'z'`.
    - `df1`: First degree of freedom (integer). If not applicable, set to `None`.
    - `df2`: Second degree of freedom (integer). If not applicable, set to `None`.
    - `test_value`: The test statistic value (float).
    - `operator`: The operator used in the reported p-value (`=`, `<`, `>`).
    - `reported_p_value`: The numerical value of the reported p-value (float).
    - `tail`: `'one'` or `'two'`. Assume `'two'` unless explicitly stated.

5. **p-Value Calculation**: The `calculate_p_value` method calculates a valid range of p-values (lower, upper).

7. **Consistency Checking**: The `compare_p_value` method checks the reported p-value falls within the range of the valid p-values (lower, upper). The script also makes a distinction between _gross inconsistencies_ and _regular inconsistencies_.

8. **Processing Results**: After extraction and testing, the results are added into a DataFrame and printed. Each test is displayed in a separate row with the following column headers:

   - `Consistent`: Indicates whether the reported p-value falls within the valid recalculated range (`Yes` for consistent, `No` for inconsistent).
   - `APA Reporting`: Displays the correct APA reporting of the detected test, regardless of how the test is reported in the context.
   - `Reported P-value`: The p-value as originally reported in the text.
   - `Valid P-value Range`: The range of valid p-values (upper, lower) based on the test statistic and degrees of freedom.
   - `Notes`: Any additional information regarding the result, such as the presence of gross or regular inconsistencies.


# Important Tips

- **API Key**: Ensure that you have an OpenAI API key stored in your `.env` file under the variable `OPENAI_API_KEY` for the code to work. Without an OpenAI API key, the code cannot use the `extract_data_from_text` method, which means the code cannot extract the relevant data from the context. 

- **File Formats**: The code supports `.txt` and `.pdf` files. Make sure your input file is in one of these formats.

- **Decimal Places**: Both the GRIM test and Statcheck respect the number of decimal places in the reported data. Keep this in mind when interpreting the results.

- **Decimal Separator**: Both the GRIM test and Statcheck only recognize a dot `.` as a valid decimal separator. A comma `,` is regarded as thousand separator. For example, `'10,159'` is interpreted as 'ten thousand one hundred fifty-nine', not 'ten point one five nine'.

- **Error Handling**: The script includes basic error handling for file formats and extraction issues. Make sure to check the console for any error messages if something goes wrong.


# Known Issues
## GRIM-Related Issues
- The AI integration in the script has issues in correctly identifying when a mean is composed of integer values or floating-point values. This means that it is likely that certain mean values get analysed by the script, even though they do not qualify for GRIM analysis, as they are not derived from integer data. 
- The AI integration in the script has issues correctly correlating the correct sample size to the according mean value when there is (quite) some context between the two mentions in the text.

## Statcheck-Related Issues
- **Typesetting issues**: In some journals, mathematical symbols such as `<` are replaced by an image of this symbol, which can’t be converted to plain text. This means that the correct operator cannot be extracted, meaning the script has to fill in an operator itself. Usually, the script fills in the `=` operator, which is likely to be incorrect. 

