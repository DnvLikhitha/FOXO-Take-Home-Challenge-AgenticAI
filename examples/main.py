import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from solution import reconstruct_traces  # pyrefly: ignore [missing-import]
import json
import sys

def main():
    # Did the user pass an input file via command line?
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        try:
            with open(input_file, 'r') as f:
                log = json.load(f)
            print(f"Loaded input from {input_file}")
        except FileNotFoundError:
            print(f"Error: File '{input_file}' not found.")
            return
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in '{input_file}': {e}")
            return
    else:
        # No file provided, let's read from standard input interactively
        print("Enter JSON log events (press Ctrl+D or Ctrl+Z when done):")
        print('Example: [{"correlation_id": "A1", "agent": "Planner", "event": "start", "ts_ms": 100}]')
        try:
            lines = []
            while True:
                try:
                    line = input()
                    lines.append(line)
                except EOFError:
                    break
            log_input = '\n'.join(lines)
            log = json.loads(log_input)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON input: {e}")
            return

    # Run the core logic to reconstruct the timelines
    result = reconstruct_traces(log)

    # Show them what we got
    print("\nInput:")
    print(json.dumps(log, indent=2))
    print("\nOutput:")
    print(json.dumps(result, indent=2))

    # If they gave us an expected output file, let's verify our result against it
    if len(sys.argv) > 2:
        expected_file = sys.argv[2]
        try:
            with open(expected_file, 'r') as f:
                expected = json.load(f)

            if result == expected:
                print("\nPASS: Output matches expected result!")
            else:
                print("\nFAIL: Output does NOT match expected result!")
                print("Expected:")
                print(json.dumps(expected, indent=2))
        except FileNotFoundError:
            print(f"\nWarning: Expected file '{expected_file}' not found - skipping verification")
        except json.JSONDecodeError as e:
            print(f"\nWarning: Invalid JSON in expected file '{expected_file}': {e} - skipping verification")

if __name__ == "__main__":
    main()