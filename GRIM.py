def grim_test(reported_mean: float, sample_size: int, decimals: int = 2) -> bool:
    """
    Check if the reported mean is mathematically possible given the sample size and a specified number of decimal places.

    :param reported_mean: The mean value reported in the study.
    :param sample_size: The number of samples in the study.
    :param decimals: The number of decimal places to check against (default is 2).
    :return: True if the reported mean is possible, False if it is impossible.
    """
    # Multiply the reported mean by the sample size
    total_sum = reported_mean * sample_size
    
    # Round the total sum to the nearest whole numbers (both down and up)
    possible_sum_1 = int(total_sum) # Round down
    possible_sum_2 = possible_sum_1 + 1 # Round up
    
    # Check if either of these divided by the sample size gives back the reported mean when rounded to the specified decimal places
    if round(possible_sum_1 / sample_size, decimals) == reported_mean or round(possible_sum_2 / sample_size, decimals) == reported_mean:
        return True
    else:
        return False

# Example usage:
reported_mean = 3.839
sample_size = 27

result = grim_test(reported_mean, sample_size)  # Using the default of 2 decimal places
print(f"Default decimals (2): {result}")

result_with_3_decimals = grim_test(reported_mean, sample_size, decimals=3)  # Specifying 3 decimal places
print(f"With 3 decimals: {result_with_3_decimals}")
