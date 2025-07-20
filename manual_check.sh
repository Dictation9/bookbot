#!/bin/bash
# manual_check.sh - Manually check book_mentions.csv for LGBT books and output a summary CSV with an 'is_lgbt' column.
# This script scans the CSV and marks each row as LGBT (yes/no) based on tags containing lgbt, lgbtq, queer, gay, lesbian, trans, bisexual, or nonbinary (case-insensitive).
# It also prints a count summary at the end.

INPUT="book_mentions.csv"
OUTPUT="book_mentions_manual_check.csv"
LGBT_TAGS="lgbt|lgbtq|queer|gay|lesbian|trans|bisexual|nonbinary"

if [ ! -f "$INPUT" ]; then
  echo "File $INPUT not found!"
  exit 1
fi

# Add is_lgbt column and process rows
awk -F',' -v OFS=',' -v tags="$LGBT_TAGS" 'NR==1 {print $0, "is_lgbt"; next} {
  lgbt="no";
  for (i=1; i<=NF; i++) {
    if (tolower($i) ~ tags) {lgbt="yes"; break}
  }
  print $0, lgbt
}' "$INPUT" > "$OUTPUT"

# Count summary
lgbt_count=$(awk -F',' 'NR>1 && tolower($0) ~ /lgbt|lgbtq|queer|gay|lesbian|trans|bisexual|nonbinary/ {c++} END {print c+0}' "$INPUT")
total_count=$(awk 'END{print NR-1}' "$INPUT")
non_lgbt_count=$((total_count - lgbt_count))
echo "LGBT books: $lgbt_count"
echo "Non-LGBT books: $non_lgbt_count"
echo "Output written to $OUTPUT" 

# Detailed missing information check
missing_info_found=0
awk -F',' 'NR==1 {next} {for(i=1;i<=NF;i++) { field=tolower($i); if($i=="" || field=="n/a") {print "Missing data at line " NR ": "$0; found=1; break}}}' "$INPUT" | while read -r line; do
  if [ $missing_info_found -eq 0 ]; then
    echo "\nRows with missing information:"
    missing_info_found=1
  fi
  echo "$line"
done
if [ $missing_info_found -eq 0 ]; then
  echo "\nNo missing information found in $INPUT."
fi 

# Run manual enrichment and update
python3 manual_enrich.py 