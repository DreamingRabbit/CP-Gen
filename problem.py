import re
from dataclasses import dataclass, field
from typing import List

@dataclass
class Problem:
    title: str
    description: str
    input_format: str
    output_format: str
    constraints: str
    samples: List[dict]
    time_limit: str
    memory_limit: str

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "constraints": self.constraints,
            "samples": self.samples,
            "time_limit": self.time_limit,
            "memory_limit": self.memory_limit,
        }

    def to_string(self) -> str:
        """
        Serialize all fields back into a single markdown‐style string,
        with headings matching the original format.
        """
        parts = []

        # Problem Statement
        parts.append("### Problem Statement")
        parts.append(self.description)
        parts.append("")  # blank line

        # Input Format
        parts.append("### Input Format")
        parts.append(self.input_format)
        parts.append("")  # blank line

        # Output Format
        parts.append("### Output Format")
        parts.append(self.output_format)
        parts.append("")  # blank line

        # Constraints
        parts.append("### Constraints")
        parts.append(self.constraints)
        parts.append("")  # blank line

        # Samples (one or more)
        for sample in self.samples:
            parts.append("### Sample Input")
            parts.append(sample.get("input", "").strip())
            parts.append("")  # blank line
            parts.append("### Sample Output")
            parts.append(sample.get("output", "").strip())
            parts.append("")  # blank line

        # Time Limit
        parts.append("### Time Limit")
        parts.append(self.time_limit)
        parts.append("")  # blank line

        # Memory Limit
        parts.append("### Memory Limit")
        parts.append(self.memory_limit)

        # Join everything with newline
        return "\n".join(parts)


def parse_problem_from_string(text: str) -> Problem:
    # Remove leading/trailing whitespace
    text = text.strip()

    # Extract the “Problem Statement” description block
    desc_match = re.search(r"### Problem Statement\s*\n(.+?)(?=\n\n### )", text, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""

    # Map section headers to keys
    sections = {
        "Input Format": "input_format",
        "Output Format": "output_format",
        "Constraints": "constraints",
        "Sample Input": "sample_input",
        "Sample Output": "sample_output",
        "Time Limit": "time_limit",
        "Memory Limit": "memory_limit",
    }
    data = {}

    # Find all other sections
    pattern = (
        r"### (Problem Statement|Input Format|Output Format|Constraints|"
        r"Sample Input|Sample Output|Time Limit|Memory Limit)\n+"
        r"((?:.|\n)*?)(?=\n### |\Z)"
    )
    for match in re.finditer(pattern, text, re.DOTALL):
        header = match.group(1)
        content = match.group(2).strip()
        if header == "Problem Statement":
            continue
        data[sections[header]] = content

    # First non-empty line as a placeholder title
    first_nonempty_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    title = first_nonempty_line

    # Build sample list
    samples = [{
        "input": data.get("sample_input", "").strip("` \n"),
        "output": data.get("sample_output", "").strip("` \n"),
    }]

    return Problem(
        title=title,
        description=description,
        input_format=data.get("input_format", ""),
        output_format=data.get("output_format", ""),
        constraints=data.get("constraints", ""),
        samples=samples,
        time_limit=data.get("time_limit", ""),
        memory_limit=data.get("memory_limit", "")
    )


if __name__ == "__main__":
    # Read a multi-section problem from file
    with open("generated_problem_statement.txt", "r", encoding="utf-8") as f:
        problem_string = f.read()

    problem = parse_problem_from_string(problem_string)

    # Convert back to a single string
    reconstructed = problem.to_string()
    print("----- Reconstructed Problem -----\n")
    print(reconstructed)

    # Optionally, save the reconstructed string to a file
    with open("problem_reconstructed.txt", "w", encoding="utf-8") as out_f:
        out_f.write(reconstructed)