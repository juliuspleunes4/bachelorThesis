import scipy.stats as stats

def calculate_p_value(test_type, df1, df2, test_value, reported_p_value, tail='two'):
    """
    Calculate the p-value for different statistical tests and compare with the reported p-value.
    
    Parameters:
    test_type (str): The type of statistical test (e.g., 'r', 't', 'f', 'chi2', 'z')
    df1 (int): The first degree of freedom (for tests with one df, set df2 to None)
    df2 (int or None): The second degree of freedom (use None for tests that only need one df)
    test_value (float): The test statistic value
    reported_p_value (float): The p-value reported in the study
    tail (str): Specify 'one' for one-tailed test or 'two' for two-tailed test. Default is 'two'.
    
    Returns:
    bool: True if the recalculated p-value is consistent with the reported p-value, False otherwise
    float: The recalculated p-value
    """

    if test_type == 'r':
        # Correlation test (r), convert to t value and calculate p-value
        t_value = test_value * ((df1) ** 0.5) / ((1 - test_value ** 2) ** 0.5)
        p_value = stats.t.sf(abs(t_value), df1)
        
    elif test_type == 't':
        # t-test
        p_value = stats.t.sf(abs(test_value), df1)
        
    elif test_type == 'f':
        # F-test
        if df2 is None:
            raise ValueError("F-test requires two degrees of freedom (df1, df2).")
        p_value = stats.f.sf(test_value, df1, df2)
        
    elif test_type == 'chi2':
        # Chi-square test (χ2) is inherently one-tailed, so tail argument is ignored
        p_value = stats.chi2.sf(test_value, df1)
        
    elif test_type == 'z':
        # Z-test
        p_value = stats.norm.sf(abs(test_value))
        
    else:
        raise ValueError(f"Unknown test type: {test_type}. Use 'r', 't', 'f', 'chi2' or 'z'.")
    
    # Adjust for one-tailed or two-tailed tests where applicable (not for chi2)
    if test_type != 'chi2':  # Only apply tail logic for tests that can be one- or two-tailed
        if tail == 'two':
            p_value = min(p_value * 2, 1)  # For two-tailed tests, double the one-tailed p-value
        elif tail != 'one':
            raise ValueError(f"Invalid tail specification: {tail}. Use 'one' or 'two'.")

    # Compare recalculated p-value with the reported p-value, rounded to 3 decimal places
    return round(p_value, 3) == round(reported_p_value, 3), p_value


# Example usage
if __name__ == '__main__':
    # Correlation Test (r) - Consistent
    print("Correlation Test (r):")
    test_type = 'r'
    df1 = 30                 # Degrees of freedom 1 (df = n - 2)
    df2 = None               # Not applicable for r
    test_value = 0.4         # Correlation coefficient
    reported_p_value = 0.023  # Reported p-value
    tail = 'two'
    is_consistent, recalculated_p_value = calculate_p_value(test_type, df1, df2, test_value, reported_p_value, tail)
    if is_consistent:
        print(f"Consistent. Got p-value: {recalculated_p_value:.5f}")
    else:
        print(f"Inconsistent, expected: {recalculated_p_value:.5f}, got: {reported_p_value}.")

    # Correlation Test (r) - Inconsistent
    print("Correlation Test (r):")
    test_type = 'r'
    reported_p_value = 0.10  # Reported p-value (inconsistent)
    is_consistent, recalculated_p_value = calculate_p_value(test_type, df1, df2, test_value, reported_p_value, tail)
    if is_consistent:
        print("Consistent.")
    else:
        print(f"Inconsistent, expected: {recalculated_p_value:.5f}, got: {reported_p_value}.")

    # T-Test (t) - Consistent
    print("T-Test (t):")
    test_type = 't'
    df1 = 20                 # Degrees of freedom
    test_value = 2.1         # Test statistic value
    reported_p_value = 0.0489  # Reported p-value
    tail = 'two'
    is_consistent, recalculated_p_value = calculate_p_value(test_type, df1, df2, test_value, reported_p_value, tail)
    if is_consistent:
        print(f"Consistent. Got p-value: {recalculated_p_value:.5f}")
    else:
        print(f"Inconsistent, expected: {recalculated_p_value:.5f}, got: {reported_p_value}.")

    # T-Test (t) - Inconsistent
    print("T-Test (t):")
    test_type = 't'
    reported_p_value = 0.08  # Reported p-value (inconsistent)
    is_consistent, recalculated_p_value = calculate_p_value(test_type, df1, df2, test_value, reported_p_value, tail)
    if is_consistent:
        print("Consistent.")
    else:
        print(f"Inconsistent, expected: {recalculated_p_value:.5f}, got: {reported_p_value}.")

    # F-Test (f) - Consistent
    print("F-Test (f):")
    test_type = 'f'
    df1 = 3                 # Numerator degrees of freedom
    df2 = 15                # Denominator degrees of freedom
    test_value = 4.5        # Test statistic value
    reported_p_value = 0.019  # Reported p-value
    tail = 'one'
    is_consistent, recalculated_p_value = calculate_p_value(test_type, df1, df2, test_value, reported_p_value, tail)
    if is_consistent:
        print(f"Consistent. Got p-value: {recalculated_p_value:.5f}")
    else:
        print(f"Inconsistent, expected: {recalculated_p_value:.5f}, got: {reported_p_value}.")

    # F-Test (f) - Inconsistent
    print("F-Test (f):")
    test_type = 'f'
    reported_p_value = 0.05  # Reported p-value (inconsistent)
    is_consistent, recalculated_p_value = calculate_p_value(test_type, df1, df2, test_value, reported_p_value, tail)
    if is_consistent:
        print("Consistent.")
    else:
        print(f"Inconsistent, expected: {recalculated_p_value:.5f}, got: {reported_p_value}.")

    # Chi-Square Test (chi2) - Consistent
    print("Chi-Square Test (chi2):")
    test_type = 'chi2'
    df1 = 4                 # Degrees of freedom
    test_value = 7.15       # Test statistic value
    reported_p_value = 0.128  # Reported p-value
    tail = 'one'            # Chi-square is inherently one-tailed
    is_consistent, recalculated_p_value = calculate_p_value(test_type, df1, df2, test_value, reported_p_value, tail)
    if is_consistent:
        print(f"Consistent. Got p-value: {recalculated_p_value:.5f}")
    else:
        print(f"Inconsistent, expected: {recalculated_p_value:.5f}, got: {reported_p_value}.")

    # Chi-Square Test (chi2) - Inconsistent
    print("Chi-Square Test (chi2):")
    test_type = 'chi2'
    reported_p_value = 0.20  # Reported p-value (inconsistent)
    is_consistent, recalculated_p_value = calculate_p_value(test_type, df1, df2, test_value, reported_p_value, tail)
    if is_consistent:
        print("Consistent.")
    else:
        print(f"Inconsistent, expected: {recalculated_p_value:.5f}, got: {reported_p_value}.")

    # Z-Test (z) - Consistent
    print("Z-Test (z):")
    test_type = 'z'
    df1 = None              # Not applicable for z-test
    df2 = None              # Not applicable for z-test
    test_value = 1.96       # Test statistic value (common critical value)
    reported_p_value = 0.050  # Reported p-value
    tail = 'two'
    is_consistent, recalculated_p_value = calculate_p_value(test_type, df1, df2, test_value, reported_p_value, tail)
    if is_consistent:
        print(f"Consistent. Got p-value: {recalculated_p_value:.5f}")
    else:
        print(f"Inconsistent, expected: {recalculated_p_value:.5f}, got: {reported_p_value}.")

    # Z-Test (z) - Inconsistent
    print("Z-Test (z):")
    test_type = 'z'
    reported_p_value = 0.10  # Reported p-value (inconsistent)
    is_consistent, recalculated_p_value = calculate_p_value(test_type, df1, df2, test_value, reported_p_value, tail)
    if is_consistent:
        print("Consistent.")
    else:
        print(f"Inconsistent, expected: {recalculated_p_value:.5f}, got: {reported_p_value}.")
