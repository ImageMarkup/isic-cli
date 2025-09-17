# PowerShell script to test quoting behavior with isic-cli
# Run this in PowerShell to see how different quoting styles behave

Write-Host "Testing PowerShell quoting behavior with isic-cli" -ForegroundColor Green
Write-Host "=" * 60

# First test if CLI is accessible
Write-Host "`nTesting CLI accessibility..." -ForegroundColor Cyan
try {
    $null = isic metadata download --help 2>&1
    Write-Host "✅ CLI is accessible" -ForegroundColor Green
} catch {
    Write-Host "❌ CLI not accessible: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 1: Unix-style quoting - show what PowerShell passes to the program
Write-Host "`nTest 1: Unix-style quoting 'diagnosis_3:`"Squamous cell carcinoma in situ`"'" -ForegroundColor Yellow
$query1 = 'diagnosis_3:"Squamous cell carcinoma in situ"'
Write-Host "PowerShell will pass this string to isic: $query1"
Write-Host "Command: isic metadata download --limit 1 (with -s '$query1')"

# Test 2: Incorrect PowerShell quoting
Write-Host "`nTest 2: Incorrect PowerShell quoting `"diagnosis_3:\`"Squamous cell carcinoma in situ\`"`"" -ForegroundColor Yellow
$query2 = "diagnosis_3:`"Squamous cell carcinoma in situ`""
Write-Host "PowerShell will pass this string to isic: $query2"
Write-Host "Command: isic metadata download --limit 1 (with -s `"$query2`")"

# Test 3: Correct PowerShell quoting with doubled quotes
Write-Host "`nTest 3: Correct PowerShell doubled quotes 'diagnosis_3:`"`"Squamous cell carcinoma in situ`"`"'" -ForegroundColor Yellow
$query3 = 'diagnosis_3:""Squamous cell carcinoma in situ""'
Write-Host "PowerShell will pass this string to isic: $query3"
Write-Host "Command: isic metadata download --limit 1 (with -s '$query3')"

# Test 4: Correct PowerShell quoting with backticks
Write-Host "`nTest 4: Correct PowerShell backticks `"diagnosis_3:\`"Squamous cell carcinoma in situ\`"`"" -ForegroundColor Yellow
$query4 = "diagnosis_3:`"Squamous cell carcinoma in situ`""
Write-Host "PowerShell will pass this string to isic: $query4"
Write-Host "Command: isic metadata download --limit 1 (with -s `"$query4`")"

# Test 5: Simple query without spaces
Write-Host "`nTest 5: Simple query 'age_approx:50'" -ForegroundColor Yellow
$query5 = 'age_approx:50'
Write-Host "PowerShell will pass this string to isic: $query5"
Write-Host "Command: isic metadata download --help (with -s '$query5')"

Write-Host "`n" + "=" * 60
Write-Host "Analysis:" -ForegroundColor Cyan
Write-Host "- Test 1 passes: $query1" -ForegroundColor White
Write-Host "- Test 2 passes: $query2" -ForegroundColor White
Write-Host "- Test 3 passes: $query3" -ForegroundColor White
Write-Host "- Test 4 passes: $query4" -ForegroundColor White
Write-Host "- Test 5 passes: $query5" -ForegroundColor White
Write-Host ""
Write-Host "The issue occurs when the CLI validates these strings against the ISIC API." -ForegroundColor Yellow
Write-Host "For actual testing, use the GitHub Actions workflow which connects to the API." -ForegroundColor Yellow