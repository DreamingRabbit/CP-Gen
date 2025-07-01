import os
import re
import json
import random
import subprocess
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI
from problem import parse_problem_from_string, Problem

# -------------------
# Configuration
# -------------------

DEEPSEEK_API_KEY = "sk-2b35461ec6914f93a9c7fa345a5b7cce"
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

INPUT_JSONL = "input.jsonl"
PROBLEM_TEXT_FILE = "generated_problem_statement.txt"
STRUCTURED_JSON = "problem_structured.json"
SAMPLE_IN = "sample.in"
SAMPLE_OUT = "sample.out"
SOLUTION_CPP = "solution.cpp"
SOLUTION_BIN = "solution"
GENERATOR_CPP = "test_case_generator.cpp"
GENERATOR_BIN = "test_case_generator"
EXAMPLE_GENERATOR_CPP = "generator_example.cpp"
ID_FILE = "ID.txt"

# -------------------
# Helper Functions
# -------------------

def get_idea(filepath: str) -> str:
    """Fetch a random idea from a JSONL file."""
    ideas = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line.strip())
                text = item.get("problem_text", "").strip()
                if text:
                    ideas.append(text)
            except json.JSONDecodeError:
                continue
    if not ideas:
        raise ValueError(f"No valid 'problem_text' found in {filepath}")
    return random.choice(ideas)


def generate_problem_statement(idea: str) -> str:
    """Generate a full problem statement using DeepSeek."""
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert competitive programming problem setter. "
                    "Create a complete, structured problem statement based on the provided idea. "
                    "Include a story, background, and characters to make it engaging. "
                    "Include a clear description, input and output formats, constraints, "
                    "sample input/output cases, time limit, and memory limit. "
                    "Do not include any commentary or explanations that hint at the solution."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Generate a full competitive programming problem based on this idea:\n\n"
                    f"{idea}\n\n"
                    "Use this structure:\n"
                    "1. **Problem Statement**: A clear, engaging description.\n"
                    "2. **Input Format**: Specify input structure.\n"
                    "3. **Output Format**: Specify output structure.\n"
                    "4. **Constraints**: List numerical constraints.\n"
                    "5. **Sample Input**: Provide one sample input.\n"
                    "6. **Sample Output**: Provide the corresponding sample output.\n"
                    "7. **Time Limit**: e.g., 1 second.\n"
                    "8. **Memory Limit**: e.g., 256 MB.\n"
                    "Start each section with a ### heading and do not add anything else between them. "
                    "Ensure the problem is well-defined and solvable."
                )
            }
        ],
        temperature=0,
        stream=False
    )
    return response.choices[0].message.content.strip()


def solve_problem(problem: Problem) -> str:
    """Generate a C++ solution for the given Problem using DeepSeek."""
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert competitive programmer. "
                    "Analyze the provided problem statement and generate a C++ solution. "
                    "Ensure the solution is efficient and adheres to constraints. "
                    "Do not include commentary or explanations."
                )
            },
            {
                "role": "user",
                "content": (
                    "Given the following problem statement, generate a C++ solution:\n\n"
                    f"{problem.to_string()}\n\n"
                    "Provide the code in a single ```cpp code block``` without additional comments."
                )
            }
        ],
        temperature=0,
        stream=False
    )
    raw = response.choices[0].message.content.strip()
    # Extract code inside ```cpp ... ```
    match = re.search(r"```cpp\n(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def generate_test_case_generator(problem: Problem, standard_solution: str) -> str:
    """Generate C++ code for a test case generator based on the problem and solution."""
    if not Path(EXAMPLE_GENERATOR_CPP).exists():
        raise FileNotFoundError(f"{EXAMPLE_GENERATOR_CPP} not found.")

    with open(EXAMPLE_GENERATOR_CPP, "r", encoding="utf-8") as f:
        example_code = f.read().strip()

    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert competitive programmer. "
                    "Given the problem statement from problem_structured.json and a standard C++ solution from the file solution.cpp, "
                    "modify the provided generator code to produce comprehensive test cases. "
                    "follow the naming scheme and structure of the provided example code. "
                    "Ensure the generator produces a variety of test cases, including edge cases, typical cases, and large inputs. "
                    "Do not include any commentary or explanations in the generated code."
                    "Save the test cases generated by the generator in a folder named 'test_cases' "
                )
            },
            {
                "role": "user",
                "content": (
                    "Problem Statement:\n\n"
                    f"{problem.to_string()}\n\n"
                    "Standard Solution:\n\n"
                    f"{standard_solution}\n\n"
                    "Example generator code:\n```cpp\n"
                    f"{example_code}\n```"
                )
            }
        ],
        temperature=0,
        stream=False
    )
    raw = response.choices[0].message.content.strip()
    match = re.search(r"```cpp\n(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def generate_report(problem: Problem, standard_solution: str) -> str:
    """Generate a report analyzing the problem and solution using DeepSeek."""

    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert competitive programmer. "
                    "Given the problem statement from problem_structured.json and a standard C++ solution from the file solution.cpp, "
                    "analyze the problem and solution. "
                    "Provide a detailed report that includes:\n"
                    "1. Problem Analysis: Key challenges and insights.\n"
                    "2. Solution Analysis: Efficiency, complexity, and correctness.\n"
                    "3. Edge Cases: Discuss any edge cases considered in the solution.\n"
                    "4. Improvements: Suggestions for optimizing the solution or alternative approaches.\n"
                    "5. Test Cases: Describe the test cases used to validate the solution.\n"
                    "Ensure the report is clear, concise, and well-structured. "
                    "Give your answer in markdown format with appropriate headings and sections."
                )
            },
            {
                "role": "user",
                "content": (
                    "Problem Statement:\n\n"
                    f"{problem.to_string()}\n\n"
                    "Standard Solution:\n\n"
                    f"{standard_solution}\n\n"
                )
            }
        ],
        temperature=0,
        stream=False
    )

    return response.choices[0].message.content.strip()

def compile_cpp(source: str, binary: str) -> bool:
    """Compile a C++ source file into an executable."""
    try:
        subprocess.run(
            ["g++", "-O2", "-std=c++17", source, "-o", binary],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False


def run_cpp(binary: str, input_path: str) -> str:
    """Run a compiled C++ binary with stdin from input_path, return stdout."""
    try:
        res = subprocess.run(
            [f"./{binary}"],
            stdin=open(input_path, "r", encoding="utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        return res.stdout.strip()
    except Exception:
        return ""

def get_and_increment_problem_id(id_file: str) -> int:
    if not Path(id_file).exists():
        with open(id_file, "w", encoding="utf-8") as f:
            f.write("1")
        return 1
    with open(id_file, "r", encoding="utf-8") as f:
        problem_id = int(f.read().strip())
    with open(id_file, "w", encoding="utf-8") as f:
        f.write(str(problem_id + 1))
    return problem_id

# -------------------
# Main Pipeline
# -------------------

def main():
    # Get current problem ID and create directory
    problem_id = get_and_increment_problem_id(ID_FILE)
    output_dir = Path(str(problem_id))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define output paths
    PROBLEM_TEXT_FILE = output_dir / "generated_problem_statement.txt"
    STRUCTURED_JSON = output_dir / "problem_structured.json"
    SAMPLE_IN = output_dir / "sample.in"
    SAMPLE_OUT = output_dir / "sample.out"
    SOLUTION_CPP = output_dir / "solution.cpp"
    SOLUTION_BIN = output_dir / "solution"
    GENERATOR_CPP = output_dir / "test_case_generator.cpp"
    GENERATOR_BIN = output_dir / "test_case_generator"

    # Define total stages for the progress bar
    total_stages = 9
    bar = tqdm(total=total_stages, desc="Pipeline Progress", ncols=80)

    # Stage 1: Fetch a random idea
    idea = get_idea(INPUT_JSONL)
    bar.update(1)

    # Stage 2: Generate full problem statement
    statement = generate_problem_statement(idea)
    with open(PROBLEM_TEXT_FILE, "w", encoding="utf-8") as f:
        f.write(statement)
    bar.update(1)

    # Stage 3: Parse problem into structured data
    problem = parse_problem_from_string(statement)
    with open(STRUCTURED_JSON, "w", encoding="utf-8") as out_f:
        json.dump(problem.to_dict(), out_f, indent=4, ensure_ascii=False)
    bar.update(1)

    # Stage 4: Save sample input/output to files
    if problem.samples:
        sample = problem.samples[0]
        with open(SAMPLE_IN, "w", encoding="utf-8") as f_in, open(SAMPLE_OUT, "w", encoding="utf-8") as f_out:
            f_in.write(sample["input"])
            f_out.write(sample["output"])
    bar.update(1)

    # Stage 5: Generate solution code
    code = solve_problem(problem)
    if code:
        with open(SOLUTION_CPP, "w", encoding="utf-8") as f:
            f.write(code)
    bar.update(1)

    # Stage 6: Compile solution.cpp
    compiled = compile_cpp(str(SOLUTION_CPP), str(SOLUTION_BIN))
    bar.update(1)

    # Stage 7: Run solution with sample input, compare output
    if compiled:
        actual = run_cpp(str(SOLUTION_BIN), str(SAMPLE_IN))
        with open(SAMPLE_OUT, "r", encoding="utf-8") as f:
            expected = f.read().strip()
        if actual == expected:
            bar.write("✅ Sample test passed.")
        else:
            bar.write("❌ Sample test failed.")
    else:
        bar.write("❌ Compilation of solution.cpp failed.")
    bar.update(1)

    # Stage 8: Generate test case generator code
    if compiled:
        gen_code = generate_test_case_generator(problem, code)
        if gen_code:
            with open(GENERATOR_CPP, "w", encoding="utf-8") as f:
                f.write(gen_code)
    bar.update(1)

    # Stage 9: Compile and run test-case generator
    if GENERATOR_CPP.exists():
        if compile_cpp(str(GENERATOR_CPP), str(GENERATOR_BIN)):
            subprocess.run([str(GENERATOR_BIN)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            bar.write("✅ Test-case generator ran successfully.")
        else:
            bar.write("❌ Compilation of test-case generator failed.")
    else:
        bar.write("⚠️ No test-case generator code to compile.")
    bar.update(1)

    bar.close()
    print(f"🎉 Pipeline complete. Problem ID: {problem_id}")

    # Stage 10: Generate Report Analysing the Problem and code
    report = generate_report(problem, code)
    report_file = output_dir / "report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📄 Report generated at {report_file}")

if __name__ == "__main__":
    main()
