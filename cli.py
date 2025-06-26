"""
@author         : J.J.G. Pleunes
@file           : cli.py
@brief          : Command-line interface for Statistical Error Detection Tools
@description    : This script provides a command-line interface for running the GRIM test and Statcheck functionality.
                  It allows users to specify input files, output formats, and verbosity levels for detailed logging.
@date           : 26-06-2025
@version        : 1.0.0
@license        : MIT License

    Copyright (c) 2025 Julius Pleunes

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

    © 2025 bachelorThesis. All rights reserved.
"""

# Importing necessary libraries
import argparse
import sys
import time
from pathlib import Path
from typing import Optional

# Importing custom modules for GRIM and Statcheck testers
from testers.GRIM.pipeline import GRIMTester
from testers.statcheck.pipeline import StatcheckTester

def create_parser() -> argparse.ArgumentParser:
    """
    @function       : create_parser
    @description    : Creates and returns the command-line argument parser for the CLI.
    @return         : argparse.ArgumentParser instance
    @raises         : None
    @example        :
    >>> parser = create_parser()
    >>> args = parser.parse_args(['grim', 'paper.pdf', '--output', 'results.csv'])
    >>> print(args.tool)  # Output: 'grim'
    """
    
    parser = argparse.ArgumentParser(
        description="AI-powered Statistical Error Detection Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=
        
        """
        Examples:
        %(prog)s grim paper.pdf --output results.csv
        %(prog)s statcheck paper.pdf --format json --verbose
        %(prog)s statcheck paper.pdf --runs 3 --output results.xlsx
        """
    )
    
    # Subcommands for different tools
    subparsers = parser.add_subparsers(dest='tool', help='Statistical test to run')
    
    # GRIM Test subcommand
    grim_parser = subparsers.add_parser('grim', help='Run GRIM test')
    grim_parser.add_argument('file_path', help='Path to input file (.pdf, .html, .htm, .txt)')
    grim_parser.add_argument('--output', '-o', help='Output file path')
    grim_parser.add_argument('--format', '-f', choices=['csv', 'json', 'excel'], 
                           default='csv', help='Output format (default: csv)')
    grim_parser.add_argument('--verbose', '-v', action='store_true', 
                           help='Enable verbose output')
    
    # Statcheck subcommand
    statcheck_parser = subparsers.add_parser('statcheck', help='Run Statcheck')
    statcheck_parser.add_argument('file_path', help='Path to input file (.pdf, .html, .htm, .txt)')
    statcheck_parser.add_argument('--output', '-o', help='Output file path')
    statcheck_parser.add_argument('--format', '-f', choices=['csv', 'json', 'excel'], 
                                default='csv', help='Output format (default: csv)')
    statcheck_parser.add_argument('--runs', '-r', type=int, default=1, 
                                help='Number of analysis runs (default: 1, max: 5)')
    statcheck_parser.add_argument('--verbose', '-v', action='store_true', 
                                help='Enable verbose output')
    
    return parser


def export_results(df, output_path: str, format_type: str) -> None:
    """
    @function           : export_results
    @description        : Exports the results DataFrame to the specified output path in the given format.
    @param df           : DataFrame containing the results to export
    @param output_path  : Path to save the exported results
    @param format_type  : Format to export the results ('csv', 'json', 'excel')
    @return             : None
    """
    
    output_path = Path(output_path)
    
    try:
        if format_type == 'csv':
            df.to_csv(output_path, index=False)
        elif format_type == 'json':
            df.to_json(output_path, orient='records', indent=2)
        elif format_type == 'excel':
            df.to_excel(output_path, index=False)
        
        print(f"✅ Results exported to: {output_path}")
    except Exception as e:
        print(f"❌ Error exporting results: {e}")


def run_grim(args) -> None:
    """
    @function       : run_grim
    @description    : Runs the GRIM test using the specified file and arguments.
    @param args     : Parsed command-line arguments
    @return         : None
    @raises         : None
    @example        :
    >>> args = argparse.Namespace(file_path='paper.pdf', output='results.csv', format='csv', verbose=True)
    >>> run_grim(args)
    """
    
    if args.verbose:
        print(f"🔍 Running GRIM test on: {args.file_path}")
    
    tester = GRIMTester()
    file_context = tester.read_context_from_file(args.file_path)
    
    if not file_context:
        print("❌ Failed to read file or file is empty")
        return
    
    start_time = time.time()
    df = tester.perform_grim_test(file_context)
    elapsed = time.time() - start_time
    
    if df is not None:
        print(f"\n📊 GRIM Test Results:")
        print(df)
        
        # Export if output path specified
        if args.output:
            export_results(df, args.output, args.format)
    else:
        print("ℹ️  No GRIM-applicable results were found.")
    
    print(f"\n⏱️  Total running time: {elapsed:.2f} seconds")


def run_statcheck(args) -> None:
    """
    @function       : run_statcheck
    @description    : Runs the Statcheck analysis using the specified file and arguments.
    @param args     : Parsed command-line arguments
    @return         : None
    @raises         : None
    @example        :
    >>> args = argparse.Namespace(file_path='paper.pdf', output='results.csv', format='csv', runs=3, verbose=True)
    >>> run_statcheck(args)
    """
    
    if args.verbose:
        print(f"🔍 Running Statcheck on: {args.file_path}")
        if args.runs > 1:
            print(f"🔄 Running {args.runs} times for consistency")
    
    # Validate runs parameter
    if args.runs < 1 or args.runs > 5:
        print("❌ Number of runs must be between 1 and 5")
        return
    
    tester = StatcheckTester()
    file_context = tester.read_context_from_file(args.file_path)
    
    if not file_context:
        print("❌ Failed to read file or file is empty")
        return
    
    start_time = time.time()
    
    if args.runs == 1:
        # Single run
        df = tester.perform_statcheck_test(file_context)
        results = [df] if df is not None else []
    else:
        # Multiple runs for consistency
        from collections import Counter
        from io import StringIO
        import pandas as pd
        
        results = []
        for i in range(args.runs):
            if args.verbose:
                print(f"Run {i + 1} of {args.runs}")
            df = tester.perform_statcheck_test(file_context)
            if df is not None:
                results.append(df)
        
        if results:
            # Find most common result
            results_csv = [df.to_csv(index=False) for df in results]
            counts = Counter(results_csv)
            most_common_csv, frequency = counts.most_common(1)[0]
            df = pd.read_csv(StringIO(most_common_csv))
            
            if args.verbose:
                print(f"📈 Most frequent result appeared {frequency}/{args.runs} times")
        else:
            df = None
    
    elapsed = time.time() - start_time
    
    if df is not None:
        print(f"\n📊 Statcheck Results:")
        print(df)
        
        # Export if output path specified
        if args.output:
            export_results(df, args.output, args.format)
    else:
        print("ℹ️  No statistical tests were found.")
    
    print(f"\n⏱️  Total running time: {elapsed:.2f} seconds")


def main() -> None:
    """
    @function       : main
    @description    : Main entry point for the CLI. Parses arguments and runs the specified tool
    @return         : None
    @raises         : SystemExit on errors
    @example        :
    >>> main()
    This function is typically called when the script is run directly.
    """
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.tool:
        parser.print_help()
        return
    
    # Check if file exists
    if not Path(args.file_path).exists():
        print(f"❌ File not found: {args.file_path}")
        sys.exit(1)
    
    # Check file extension
    valid_extensions = {'.pdf', '.html', '.htm', '.txt'}
    file_ext = Path(args.file_path).suffix.lower()
    if file_ext not in valid_extensions:
        print(f"❌ Unsupported file type: {file_ext}")
        print(f"Supported formats: {', '.join(valid_extensions)}")
        sys.exit(1)
    
    # Run appropriate tool
    try:
        if args.tool == 'grim':
            run_grim(args)
        elif args.tool == 'statcheck':
            run_statcheck(args)
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
