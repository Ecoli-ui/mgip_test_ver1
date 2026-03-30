import csv
import numpy as np

# Read the data
data = {}
with open('synthetic_patient_cohort.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    
# Extract columns
params = ['Gb', 'Ib', 'p1', 'p2', 'p3', 'tau_meal', 'Vg', 'insulin_clearance_rate']
for param in params:
    data[param] = np.array([float(row[param]) for row in rows])

phenotypes = [row['phenotype'] for row in rows]

print("=" * 70)
print("EMPIRICAL DISTRIBUTION ANALYSIS (n=8 patients)")
print("=" * 70)

# Count phenotypes
print("\nPhenotype composition:")
from collections import Counter
phenotype_counts = Counter(phenotypes)
for phenotype, count in phenotype_counts.items():
    print(f"  {phenotype}: {count}")

print("\n" + "=" * 70)
print("DISTRIBUTIONAL CLUES FROM DATA")
print("=" * 70)

for param in params:
    values = data[param]
    
    print(f"\n{param}:")
    print(f"  Range: [{values.min():.6f}, {values.max():.6f}]")
    print(f"  Mean: {values.mean():.6f}, Median: {np.median(values):.6f}")
    std = values.std(ddof=1)
    cv = std / values.mean()
    print(f"  Std: {std:.6f}, CV: {cv:.3f}")
    
    # Skewness (manual calculation)
    n = len(values)
    mean = values.mean()
    m3 = ((values - mean)**3).sum() / n
    m2 = ((values - mean)**2).sum() / n
    skew = m3 / (m2**1.5) if m2 > 0 else 0
    
    print(f"  Skewness: {skew:.3f}", end="")
    if abs(skew) < 0.5:
        print(" (roughly symmetric -> normal-like)")
    elif skew > 0:
        print(" (right-skewed -> log-normal-like)")
    else:
        print(" (left-skewed)")
    
    # Check log-transform skewness
    log_values = np.log(values)
    log_mean = log_values.mean()
    log_m3 = ((log_values - log_mean)**3).sum() / n
    log_m2 = ((log_values - log_mean)**2).sum() / n
    log_skew = log_m3 / (log_m2**1.5) if log_m2 > 0 else 0
    print(f"  Log-space skewness: {log_skew:.3f}", end="")
    if abs(log_skew) < abs(skew):
        print(" (more symmetric in log-space -> log-normal likely)")
    else:
        print("")

print("\n" + "=" * 70)
print("DISTRIBUTION HYPOTHESES:")
print("=" * 70)

for param in params:
    values = data[param]
    cv = values.std(ddof=1) / values.mean()
    
    n = len(values)
    mean = values.mean()
    m3 = ((values - mean)**3).sum() / n
    m2 = ((values - mean)**2).sum() / n
    skew = m3 / (m2**1.5) if m2 > 0 else 0
    
    log_values = np.log(values)
    log_mean = log_values.mean()
    log_m3 = ((log_values - log_mean)**3).sum() / n
    log_m2 = ((log_values - log_mean)**2).sum() / n
    log_skew = log_m3 / (log_m2**1.5) if log_m2 > 0 else 0
    
    print(f"\n{param}:", end=" ")
    if cv < 0.12 and abs(skew) < 0.5:
        print("TRUNCATED NORMAL (low CV, symmetric)")
    elif cv > 0.15 and skew > 0.3 and abs(log_skew) < abs(skew):
        print("BOUNDED LOG-NORMAL (higher CV, right-skewed, symmetric in log-space)")
    elif cv > 0.15 and skew > 0.3:
        print("BOUNDED LOG-NORMAL (higher CV, right-skewed)")
    else:
        print("MIXED/UNCERTAIN (small sample)")
        
print("\n" + "=" * 70)
