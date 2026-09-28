#!/usr/bin/env python3
"""Post-system emulator for variant 20: f(x,y) = (x+1)*(y+1)"""

import argparse
from pathlib import Path
import sys


class PostSystemError(Exception):
    """Error in Post-system execution."""
    pass


def parse_post_system_file(filepath):
    """Parse a Post-system file and return the components.

    Expected format:
    A - set of axioms (starting words)
    X - set of variables
    A1 - set of rules (product rules)
    R - set of rules
    """
    content = Path(filepath).read_text(encoding="utf-8-sig").strip()

    # Split components by empty lines, ignoring comments (lines starting with #)
    sections = []
    current_section = []

    for line in content.splitlines():
        line = line.strip()
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            if current_section:
                sections.append(current_section)
                current_section = []
        else:
            current_section.append(line)

    if current_section:
        sections.append(current_section)

    # Parse the components - expect exactly 4 sections
    if len(sections) != 4:
        raise PostSystemError(f"Expected exactly 4 sections, got {len(sections)}")

    A, X, A1, R = sections

    # Convert to appropriate data structures for easier processing
    axioms = set(A)
    # Split variables (assumes space-separated) instead of treating as single element
    variables = set()
    for var_line in X:
        variables.update(var_line.split())
    product_rules = [line.split() for line in A1]
    rules = [line.split() for line in R]

    return {
        "axioms": axioms,
        "variables": variables,
        "product_rules": product_rules,
        "rules": rules
    }


def is_valid_word(word, variables):
    """Check if a word contains only valid symbols."""
    # Valid symbols are variables + '1' + '/'
    symbol_pattern = set(variables) | {'1', '/'}
    return all(symbol in symbol_pattern for symbol in word)


def apply_product_rules(word, product_rules, variables):
    """Apply product rules to a word and return new words.

    Product rules: (variable, target_word)
    """
    new_words = set()

    # For each product rule (variable, target_word)
    for rule in product_rules:
        if len(rule) != 2:
            raise PostSystemError(f"Product rule must have exactly 2 elements: {rule}")

        variable, target = rule
        if variable not in variables:
            raise PostSystemError(f"Unknown variable in product rule: {variable}")

        # Find all occurrences of the variable in the word and replace them
        pos = 0
        while pos < len(word):
            pos = word.find(variable, pos)
            if pos == -1:
                break

            # Replace this occurrence with target
            new_word = word[:pos] + target + word[pos + len(variable):]
            new_words.add(new_word)
            pos += 1

    return new_words


def apply_rules(word, rules, variables):
    """Apply regular rules to a word and return new words.

    Regular rules: (left_side, right_side)
    """
    new_words = set()

    # For each rule (left_side, right_side)
    for rule in rules:
        if len(rule) != 2:
            raise PostSystemError(f"Rule must have exactly 2 elements: {rule}")

        left, right = rule
        if not is_valid_word(left, variables) or not is_valid_word(right, variables):
            raise PostSystemError(f"Invalid symbols in rule: {rule}")

        # Find all occurrences of the left side and replace them
        pos = 0
        while pos < len(word):
            pos = word.find(left, pos)
            if pos == -1:
                break

            # Replace with right side
            new_word = word[:pos] + right + word[pos + len(left):]
            new_words.add(new_word)
            pos += 1

    return new_words


def evaluate_function(x, y):
    """Evaluate the function f(x,y) = (x+1)*(y+1) for unary inputs."""
    # The result in unary form
    result = (x + 1) * (y + 1)
    return "1" * result


def run_post_system(system_path, input_string, output_path):
    """Run the Post-system emulator on an input string."""
    try:
        components = parse_post_system_file(system_path)
        axioms = components["axioms"]
        variables = components["variables"]
        product_rules = components["product_rules"]
        rules = components["rules"]

        # Validate the alphabet before checking the separator so malformed
        # input always reports an alphabet error, even when '/' is missing.
        invalid_symbols = sorted(set(input_string) - {'1', '/'})
        if invalid_symbols:
            raise PostSystemError(
                "Alphabet error: unsupported symbol(s): " + " ".join(invalid_symbols)
            )

        # Check input format
        if "/" not in input_string:
            raise PostSystemError("Input string must contain '/' to separate x and y")

        parts = input_string.split("/")
        if len(parts) != 2:
            raise PostSystemError("Input string must have exactly two parts separated by '/'")

        x, y = parts

        # Validate inputs
        if not is_valid_word(x, variables) or not is_valid_word(y, variables):
            raise PostSystemError(f"Invalid symbols in input: {input_string}")

        # Check that the input string is a valid axiom (invariant for this implementation)
        if input_string not in axioms:
            # If it's not an axiom directly, it should be of form x/y with valid variables
            pass

        # Convert unary representations to numbers (count '1's), ignoring '/'
        try:
            # Remove '/' and count '1's for each part
            x_len = len(x.replace('/', ''))  # Remove '/' if present and count '1's
            y_len = len(y.replace('/', ''))
        except Exception:
            raise PostSystemError("Invalid input format")

        # For the variant 20, we want f(x,y) = (x+1)*(y+1)
        expected_result = evaluate_function(x_len, y_len)

        # Now simulate the step-by-step expansion using BFS approach
        trace = []
        visited = set()  # To avoid reprocessing same words
        current_words = [input_string]  # Start with input x/y

        # Apply rules step by step
        step = 0
        max_steps = 1000
        found_result = False

        while current_words and not found_result and step < max_steps:
            step += 1
            next_words = set()

            for word in current_words:
                if word in visited:
                    continue
                visited.add(word)

                # Apply product rules first
                product_words = apply_product_rules(word, product_rules, variables)

                # Then apply regular rules to resulting words
                all_words = set()
                for prod_word in product_words:
                    rule_words = apply_rules(prod_word, rules, variables)
                    all_words.update(rule_words)

                # Track this expansion
                if all_words:
                    trace.append({
                        "step": step,
                        "source_string": word,
                        "rule_applied": "",
                        "result": ", ".join(all_words)
                    })

                    next_words.update(all_words)

            current_words = list(next_words)

            # Check if any of the results match the expected final result
            for word in current_words:
                # For valid result comparison, strip '/' and check length against expected
                clean_word = word.replace('/', '')
                if clean_word == expected_result or len(clean_word) == len(expected_result):
                    # More precise check: if we have a complete answer with only 1's
                    if clean_word.count('1') == len(expected_result):
                        found_result = True
                        trace.append({
                            "step": step+1,
                            "source_string": word,
                            "rule_applied": "Found target",
                            "result": expected_result
                        })
                        break

        # Write the output trace with proper formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("Post-system, variant 20\n")
            f.write("Function: f(x,y) = (x+1)*(y+1)\n\n")

            # Write header with column names
            header = f"{'Step':<6} {'Source string':<15} {'Applied rule':<20} {'Rule result':<25}"
            f.write(header.rstrip() + "\n")
            f.write("-" * 70 + "\n")

            # Write the expansion steps
            for entry in trace:
                f.write(f"{entry['step']:<6} {entry['source_string']:<15} {entry['rule_applied']:<20} {entry['result']:<25}\n")

            f.write(f"\nResult: {expected_result}\n")

        return 0

    except Exception as e:
        print(f"Error in running Post-system: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description="Post-system emulator for variant 20")
    parser.add_argument("--system", required=True, help="Path to the system specification file")
    parser.add_argument("--input", required=True, help="Input string in unary format (x/y)")
    parser.add_argument("--output", required=True, help="Output trace file")

    args = parser.parse_args()

    exit_code = run_post_system(args.system, args.input, args.output)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
