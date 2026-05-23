#  Dockerized CI/CD Build Tool for C++

A lightweight, Python-based Continuous Integration pipeline that automates the building, testing, and coverage analysis of C++ (CMake) projects inside isolated Docker environments. 


## Features

* **Automated CMake Integration:** Seamlessly generates and builds Makefiles based on the selected mode.
* **Multiple Build Profiles:**
  * `release`: Optimized (`-O3`), stripped binary for production.
  * `debug`: Includes debug symbols (`-g`) for stepping through code with GDB.
  * `coverage`: Injects coverage flags, runs tests, and generates detailed `lcov` statistics.
* **Log Parsing:** Uses Python regular expressions to extract exact test coverage percentages directly from the tool's stdout.
* **Artifact Management:** Automatically generates timestamped build reports and saves them in an isolated `reports/` directory (ignored via `.gitignore`).
* **Idempotent Docker Handling:** Automatically checks for the existence of the required Docker image and builds it only if necessary.

## Tech Stack

* **Scripting:** Python 3
* **Containerization:** Docker 
* **Build System:** CMake, Make, GCC/G++
* **Testing & Metrics:** LCOV, gcov

## Usage

The pipeline is controlled via a single Python CLI script `builder.py`.

### Basic Syntax
```bash
python3 builder.py <mode> [--logs]