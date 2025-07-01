#include <cstdio>
#include <random>
#include <string>
#include <vector>
#include <iostream>
#include <filesystem>
#include <cstdlib>
#include <chrono>

namespace fs = std::filesystem;

std::mt19937 rnd(std::chrono::steady_clock::now().time_since_epoch().count());

int random(int l, int r) {
    return rnd() % (r - l + 1) + l;
}

void generate_test(const std::string& filename, int n, int value_range) {
    std::string in_file = filename + ".in";
    FILE* f = fopen(in_file.c_str(), "w");
    if (!f) {
        perror(("❌ Failed to open " + in_file).c_str());
        exit(EXIT_FAILURE);
    }

    fprintf(f, "%d\n", n);
    std::vector<std::string> operations;
    int inserted = 0;
    int queries = 0;

    for (int i = 0; i < n; ++i) {
        bool do_query = (inserted > 0 && random(0, 1));
        if (do_query) {
            operations.push_back("QUERY");
            ++queries;
        } else {
            int x = random(-value_range, value_range);
            operations.push_back("INSERT " + std::to_string(x));
            ++inserted;
        }
    }

    if (queries == 0) {
        operations[random(0, n - 1)] = "QUERY";
    }

    for (const auto& op : operations) {
        fprintf(f, "%s\n", op.c_str());
    }

    fclose(f);
}

bool run_standard_solution(const std::string& binary, const std::string& in_file, const std::string& out_file) {
    std::string cmd = "./" + binary + " < " + in_file + " > " + out_file;
    return std::system(cmd.c_str()) == 0;
}

int main() {
    std::string solution_source = "gpt4o.cpp";
    std::string solution_binary = "standard_solution";

    // Compile the standard solution
    std::string compile_cmd = "g++ -O2 -std=c++17 " + solution_source + " -o " + solution_binary;
    std::cout << "🔧 Compiling standard solution...\n";
    if (std::system(compile_cmd.c_str()) != 0) {
        std::cerr << "❌ Compilation failed for " << solution_source << "\n";
        return 1;
    }
    std::cout << "✅ Compilation complete.\n";

    // Generate subtasks
    std::vector<std::tuple<std::string, int, int>> subtasks = {
        {"subtask1", 2, 100},
        {"subtask2", 10, 1000},
        {"subtask3", 100, 10000},
        {"subtask4", 1000, 1000000},
        {"subtask5", 10000, 1000000000},
        {"subtask6", 50000, 1000000000},
        {"subtask7", 100000, 1000000000}
    };

    for (const auto& [name, n, range] : subtasks) {
        generate_test(name, n, range);
        if (run_standard_solution(solution_binary, name + ".in", name + ".out")) {
            std::cout << "✅ " << name << ".out generated\n";
        } else {
            std::cerr << "❌ Runtime error on: " << name << "\n";
        }
    }

    // Create folder for test cases
    fs::create_directory("test_cases");

    // Generate 100 random test cases
    for (int i = 0; i < 100; ++i) {
        std::string base = "test_cases/test_case_" + std::to_string(i);
        int n = random(1, 1000);
        int value_range = random(1, 1000000);
        generate_test(base, n, value_range);
        if (run_standard_solution(solution_binary, base + ".in", base + ".out")) {
            std::cout << "✅ " << base << ".out generated\n";
        } else {
            std::cerr << "❌ Runtime error on: " << base << "\n";
        }
    }

    std::cout << "\n🎉 All .in and .out files generated using " << solution_source << ".\n";
    return 0;
}