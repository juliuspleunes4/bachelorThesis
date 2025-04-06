# bachelorThesis
This project contains two AI-powered Python scripts which can be used for automated statistical error detection. The following tests are included: the **GRIM Test** & **Statcheck**. Both scripts leverage AI to extract data from provided files and then use Python to perfrom the necessary calculations. This is to ensure that the calculations are done correctly, since AI models are still prone to making errors when it comes to mathematics.

# Credits
The creation of the code for the GRIM test has been inspired by the paper "_The GRIM Test: A Simple Technique Detects Numerous Anomalies in the Reporting of Results in Psychology_", `(Brown & Heathers, 2016)`. DOI: `10.1177/1948550616673876`.

The creation of the code for Statcheck has been inspired by the paper "_The prevalence of statistical reporting errors in psychology (1985-2013)_", `(Nuijten et al., 2016)`. DOI: `10.3758/s13428-015-0664-2`.

The GitHub page for the R package of `statcheck` created by Michèle Nuijten can be found [here](https://github.com/MicheleNuijten/statcheck). 

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
First, download the source code from this repository. Make sure Python 3.10.11 is installed, using which you can install all dependencies by executing `pip install -r requirements.txt` in the root directory of this project. After all dependencies have successfully installed, create a `.env` file in the root directory of the project. This file should contain your environment variables. For this project, only the OpenAI API key is relevant. The `.env` file should be formattted as follows:

`OPENAI_API_KEY = "your_openai_api_key_here"`


Once this is done, everything should be installed and ready for use.

## Running the Tests
You can run the GRIM Test and Statcheck scripts by executing their corresponding Python file and providing the path to your `.txt` or `.pdf` file when prompted.

 - To run the **GRIM Test**:
   
   Execute `python GRIM_gpt4o_mini.py`
    
   Execute `python GRIM_gpt4o_mini_segmentation.py`if you want to divide the file contents into segments of 500 words each with an overlap of 8 words per segment.
 - To run **Statcheck**:

   Execute `python statcheck_gpt4o_mini.py`
   
   Execute `python statcheck_multiple_runs.py`if you want to automatically analyse the provided file three times. This improves consistency but increases runtime and costs.

# GRIM Test

The GRIM Test (Granularity-Related Inconsistency of Means) is a tool for detecting inconsistencies in reported statistical means within scientific texts. This code automates this test by using the `GPT-4o-mini` AI model to automatically extract reported means and sample sizes from a provided file. The code then uses the `grim_test` method to perform calculations using Python.

> [!IMPORTANT]
> The test only works for means that are composed of integer data, since the calculation relies on the granularity of whole numbers to determine whether the mean is mathematically possible given the sample size. 


## How it Works

1. **Central class**: The `GRIMTester` class contains all methods for reading context from files, extracting reported means, conducting the GRIM test, and presenting results.
2. **Convert**: The `.pdf`, `.htm` or `.html` file gets converted into plain text. `.txt` files are already in plain text.
   
3. **Extract data**: The `extract_data_from_text` method uses the `GPT-4o-mini` AI model to identify and extract reported means and sample sizes from the text. The model is inscructed to only extract means that are composed of integer data. The output is formatted according to the specified requirements, so it can be used by other methods in the class.

4. **GRIM test**: The `grim_test` method checks if the reported mean is mathematically possible based on the sample size and the specified number of decimal places. 

5. **Processing results**: After extraction and testing, the results are added into a DataFrame and printed. Each test is displayed in a separate row with the following column headers:

    - `Consistent`: Displays whether the reported mean passed the GRIM test (`Yes` for consistent, `No` for inconsistent).
    - `Reported Mean`: Displays the original mean value as extracted from the text, including any trailing zeros.
    - `Sample Size`: The corresponding sample size used for each reported mean.
    - `Decimals`: Displays the number of decimal places in the reported mean.



# Statcheck
Statcheck is a tool for checking the consistency of reported statistical test results in scientific texts. It works as a "spellchecker" for statistics. It recalculates a valid p-value range based on the corresponding test statistic and degree(s) of freedom (a z-test only requires a test statistic). If the reported p-value falls within this valid range of p-values, the test is considered to be consistent. If the reported p-value does not fall within this range of valid p-values, the test is considered to be inconsistent. This script can recognise the following NHST results: t-tests, F-tests, correlations (r), z-tests & $\chi^2$ -tests.

> [!IMPORTANT]
> The script calculates a valid range of p-values, and the reported p-value must fall within this range to be considered consistent. There are two types of inconsistencies in which the script makes a distinction: _regular_ and _gross inconsistencies_. A _gross inconsistency_ occurs when a reported p-value indicates statistical significance, but the recalculated p-values show otherwise, or vice versa. A _regular inconsistency_ occurs when the reported p-value does not fall within the valid p-value range, but the (in)significance remains unchanged. 

### Example:

For a reported t-test with `t(30) = 1.96` and `p = 0.059`, the script calulates a valid p-value range between the largest and the smallest possible numbers that still round to `1.96`.

- Lower bound: `t = 1.964999...` gives a p-value of `0.05873`.
- Upper bound: `t = 1.955` gives a p-value of `0.05996`.

Since the reported p-value of `0.059` falls between the recalculated range `0.05873 to 0.05996`, the test is consistent.

## How It Works
1. **Central class**: The `StatcheckTester` class contains all methods for reading context from files, extracting reported  statistical tests, recalculating a valid p-value range, comparison and presenting results.
2. **Convert**: The `.pdf`, `.htm` or `.html` file gets converted into plain text. `.txt` files are already in plain text.

3. **Segmentation and overlap**: The plain text is then split into segments of 500 words each, with an overlap of 8 words between consecutive segments. Using segmentation, the script does a much better job at correctly identifying all statistical tests in the entire context. The overlap ensures that each statistical test is detected, even if the test spans multiple segments (`test X` starts at the end of segment `n`, it ends at the begin of segment `n + 1`).

   
4. **Extract data**: The `extract_data_from_text` method uses the `GPT-4o-mini` AI model to identify and extract reported statistical tests from the text. This method transforms unstructured data (tests found in the text) into structured data: a Python list of dictionaries. Each extracted test is represented as a dictionary with the following keys:

    - `test_type`: One of `'r'`, `'t'`, `'f'`, `'chi2'`, `'z'`.
    - `df1`: First degree of freedom (float or integer). If not applicable, set to `None`.
    - `df2`: Second degree of freedom (float or integer). If not applicable, set to `None`.
    - `test_value`: The test statistic value (float).
    - `operator`: The operator used in the reported p-value (`=`, `<`, `>`).
    - `reported_p_value`: The numerical value of the reported p-value (float).
    - `epsilon`: Only applicable for Huynh-Feldt corrections (float). If not applicable, set to `None`.
    - `tail`: `'one'` or `'two'`. Assume `'two'` unless explicitly stated.

5. **Apply statistical correction (if applicable)**: Currently, the script can only account for Huynh-Feldt corrections. It automatically applies this correction when the following conditions apply:
    - `test_type` == `f`.
    - `epsilon` is not `None`.
    - `df1` & `df2` are `integers`.
  
    If there is an `epsilon` value reported, but `df1` & `df2` are not `integers`, this may imply the degrees of freedom have already been adjusted by the the `epsilon` value. In this case, the script does not reapply the correction.

10. **p-Value calculation**: The `calculate_p_value` method calculates a valid range of p-values (lower, upper) for each extracted test based on its parameters.

11. **Consistency checking**: The `compare_p_value` method checks the reported p-value falls within the range of the valid p-values (lower, upper). The script also makes a distinction between _gross inconsistencies_ and _regular inconsistencies_.

12. **Processing results**: After extraction and testing, the results are added into a DataFrame and printed. Each test is displayed in a separate row with the following column headers:

   - `Consistent`: Indicates whether the reported p-value falls within the valid recalculated range (`Yes` for consistent, `No` for inconsistent).
   - `APA Reporting`: Displays the correct APA reporting of the detected test, regardless of how the test is reported in the context.
   - `Reported P-value`: The p-value as originally reported in the text.
   - `Valid P-value Range`: The range of valid p-values (lower, upper) based on the test type, test value and degrees of freedom.
   - `Notes`: Any additional information regarding the result, such as the presence of gross or regular inconsistencies or the usage of a statistical correction.


# Important Tips

- **API Key**: Ensure that you have an OpenAI API key stored in your `.env` file under the variable `OPENAI_API_KEY` for the code to work. Without an OpenAI API key, the code cannot use the `extract_data_from_text` method, which means the code cannot extract the relevant data from the context. 

- **Decimal Places**: Both the GRIM test and Statcheck respect the number of decimal places in the reported data. Keep this in mind when interpreting the results.

- **Decimal Separator**: Both the GRIM test and Statcheck only recognize a dot `.` as a valid decimal separator. A comma `,` is regarded as thousand separator. For example, `'10,159'` is interpreted as 'ten thousand one hundred fifty-nine', not 'ten point one five nine'.

- **Error Handling**: The script includes basic error handling for file formats and extraction issues. Make sure to check the console for any error messages if something goes wrong.


# Known Issues
## GRIM-Related Issues
- The AI integration in the script has issues in correctly identifying when a mean is composed of integer values or floating-point values. This means that it is likely that certain mean values get analysed by the script, even though they do not qualify for GRIM analysis, as they are not derived from integer data. 
- The AI integration in the script has issues correctly correlating the correct sample size to the according mean value when there is (quite) some context between the two mentions in the text. Both GRIM-related files, `GRIM_gpt4o_mini.py` and `GRIM_gpt4o_mini_segmentation.py`struggle with this. When no segmentation is used, i.e., `GRIM_gpt4o_mini.py` is used, the context window usually becomes too large for the script to properly function. When segmentation is used, another problem occurs: sample size and mean values are often not reported in the same (relatively small) segment. That means it becomes impossible to properly link the sample size to its corresponding mean value.

## Statcheck-Related Issues
- **Typesetting issues**: In some journals, mathematical symbols such as `<` are replaced by an image of this symbol, which can’t be converted to plain text. This means that the correct operator cannot be extracted, meaning the script has to fill in an operator itself. Usually, the script fills in the `=` operator, which is likely to be incorrect.
- **Statistical corrections**: The script does not take statistical corrections (described in the context) into account. The script only tries to identify which tail to use (`'one'` or `'two'`) based on the context. A feature which tries to correct for statistical corrections could be implemented at a later stage, but is currently not in place. 

# Code Quality
All code is compliant with the [Ruff linter](https://docs.astral.sh/ruff/).


