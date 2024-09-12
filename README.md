# bachelorThesis

# GRIM Test

The GRIM Test (Granularity-Related Inconsistency of Means) is a tool for detecting inconsistencies in reported statistical means within scientific texts. This code automates this test by using the `GPT-4o-mini` AI model to automatically extract reported means and sample sizes from a provided file. The code then uses the `grim_test` method to perform calculations using Python, ensuring that  the calculations are done correctly, since AI models are still prone to making errors when it comes to mathematics.

> [!IMPORTANT]
> The test only works for means that are composed of integer data, since the calculation relies on the granularity of whole numbers to determine whether the mean is mathematically possible given the sample size. 

## Installation

First, download the source code from this repository. Make sure Python 3.9.7 is installed, using which you can install all dependencies by executing `pip install -r requirements.txt` in the root directory of this project. After all dependencies have successfully installed, create a `.env` file in the root directory of the project. This file should contain your environment variables. For this project, only the OpenAI API key is relevant. The `.env` file should be formattted as follows:

`OPENAI_API_KEY = "your_openai_api_key_here"`


Once this is done, everything should be installed and ready for use.


## How it Works

1. **Central Class**: The `GRIMTester` class contains all methods for reading context from files, extracting reported means, conducting the GRIM test, and presenting results.
   
3. **Extract Data**: The `extract_data_from_text` method uses the `GPT-4o-mini` AI model to identify and extract reported means and sample sizes from the text. The model is inscructed to only extract means that are composed of integer data. The output is formatted according to the specified requirements, so it can be used by other methods in the class.

4. **GRIM Test**: The `grim_test` method checks if the reported mean is mathematically possible based on the sample size and the specified number of decimal places. 

5. **Processing Results**: After extraction and testing, the results are added into a DataFrame and printed. Each test is displayed in a separate row with the following columns headers:

    `Consistent`: Displays whether the reported mean passed the GRIM test (Yes for consistent, No for inconsistent).
    
    `Reported Mean`: Displays the original mean value as extracted from the text, including any trailing zeros.
    
    `Sample Size`: The corresponding sample size used for each reported mean.
    
    `Decimals`: Displays the number of decimal places in the reported mean.

## Important Tips

- **API Key**: Ensure that you have an OpenAI API key stored in your `.env` file under the variable `OPENAI_API_KEY` for the code to work. Without an OpenAI API key, the code cannot use the `extract_data_from_text` method, which means the code cannot extract the relevant data from the context. 

- **File Formats**: The code supports `.txt` and `.pdf` files. Make sure your input file is in one of these formats.

- **Decimal Places**: The GRIM test respects the number of decimal places in the reported means. Keep this in mind when interpreting the results.

- **Error Handling**: The script includes basic error handling for file formats and extraction issues. Make sure to check the console for any error messages if something goes wrong.

## Usage

To use this automated version of the GRIM Test, run the script and provide the path to your text or PDF file when prompted. The script will read the file, extract the relevant data, perform the GRIM test, and output the results in a pandas DataFrame. Use the following command in your terminal to run the script:


`python GRIM-gpt4o-mini.py`

# Known Issues
- The AI integration in the script has issues in correctly identifying when a mean is composed of integer values or floating-point values. This means that it is likely that certain mean values get analysed by the script, even though they do not qualify for GRIM analysis, as they are not derived from integer data. 
- The AI integration in the script has issues correctly correlating the correct sample size to the according mean value when there is (quite) some context between the two mentions in the text.
