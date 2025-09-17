#!/bin/bash
# Test script to verify valid diagnosis values

echo "Testing various diagnosis values to find valid ones..."
echo "============================================================"

# Test simple values first
echo "Testing simple age query:"
isic metadata download -s 'age_approx:50' --limit 1

echo
echo "Testing diagnosis_3 with melanoma:"
isic metadata download -s 'diagnosis_3:melanoma' --limit 1

echo
echo "Testing diagnosis_3 with quotes around melanoma:"
isic metadata download -s 'diagnosis_3:"melanoma"' --limit 1

echo
echo "Testing if 'Squamous cell carcinoma in situ' is valid:"
isic metadata download -s 'diagnosis_3:"Squamous cell carcinoma in situ"' --limit 1

echo
echo "Testing a different approach with diagnosis_2:"
isic metadata download -s 'diagnosis_2:"Malignant melanocytic proliferations (Melanoma)"' --limit 1

echo
echo "Getting help to see example queries:"
isic metadata download --help | grep -A 10 -B 10 diagnosis