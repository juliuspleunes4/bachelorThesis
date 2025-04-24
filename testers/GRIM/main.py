"""
Runs the GRIMTester on a given file.
"""

import time

from pipeline import GRIMTester


def main() -> None:
    tester = GRIMTester()
    file_path = input("Please provide the file path to the context you want to analyse:\n")
    file_context = tester.read_context_from_file(file_path)
    start_time = time.time() # Start time after the file is read
    if not file_context:
        return

    df = tester.perform_grim_test(file_context)

    if df is not None:
        print("\nGRIM result:")
        print(df)
    else:
        print("No GRIM-applicable results were found.")

    elapsed = time.time() - start_time
    print(f"\nTotal running time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
