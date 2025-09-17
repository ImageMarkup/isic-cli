#!/bin/bash
# Bash script to test quoting behavior with isic-cli on Unix systems
# Run this in bash/zsh to see how quoting works on Unix

echo "Testing Unix/Linux quoting behavior with isic-cli"
echo "============================================================"

# Test 1: Standard Unix quoting - test with actual API call
echo
echo "Test 1: Standard Unix quoting 'diagnosis_3:\"Squamous cell carcinoma in situ\"'"
echo "Command: isic metadata download -s 'diagnosis_3:\"Squamous cell carcinoma in situ\"' --limit 1"
if isic metadata download -s 'diagnosis_3:"Squamous cell carcinoma in situ"' --limit 1 > /dev/null 2>&1; then
    echo "Result: SUCCESS"
else
    echo "Result: FAILED"
fi

# Test 2: Double-quoted with escaped quotes
echo
echo "Test 2: Double-quoted with escapes \"diagnosis_3:\\\"Squamous cell carcinoma in situ\\\"\""
echo "Command: isic metadata download -s \"diagnosis_3:\\\"Squamous cell carcinoma in situ\\\"\" --limit 1"
if isic metadata download -s "diagnosis_3:\"Squamous cell carcinoma in situ\"" --limit 1 > /dev/null 2>&1; then
    echo "Result: SUCCESS"
else
    echo "Result: FAILED"
fi

# Test 3: Simple query without spaces
echo
echo "Test 3: Simple query 'age_approx:50'"
echo "Command: isic metadata download -s 'age_approx:50' --limit 1"
if isic metadata download -s 'age_approx:50' --limit 1 > /dev/null 2>&1; then
    echo "Result: SUCCESS"
else
    echo "Result: FAILED"
fi

echo
echo "============================================================"
echo "Expected behavior on Unix/Linux:"
echo "- All tests should SUCCESS (standard quoting works fine)"
echo "If any test fails, it may be due to network issues or API availability."