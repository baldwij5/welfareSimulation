"""
Smoke Test: Verify ablation_study.py works

Quick test with 2 iterations to verify the ablation framework runs.

Run: python tests/test_ablation_study_smoke.py
Expected: Completes in ~5 minutes, shows all 6 configs run successfully
"""

import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.insert(0, 'src')

import subprocess
import time
from pathlib import Path

print("="*70)
print("ABLATION STUDY SMOKE TEST")
print("="*70)
print("Running 6 configs × 2 iterations = 12 quick experiments")
print("Expected time: ~3-5 minutes")
print()

# Run ablation with minimal iterations
start = time.time()

result = subprocess.run(
    ['python', 'experiments/ablation_study.py', '--iterations', '2', '--seekers', '100'],
    capture_output=True,
    text=True
)

elapsed = time.time() - start

print(result.stdout)

if result.returncode == 0:
    print(f"\n{'='*70}")
    print("✅ SMOKE TEST PASSED!")
    print("="*70)
    print(f"Completed in {elapsed/60:.1f} minutes")
    print(f"\nAblation framework is working correctly!")
    print(f"Ready to run full study with:")
    print(f"  python experiments/ablation_study.py --iterations 20 --seekers 10000")
else:
    print(f"\n{'='*70}")
    print("❌ SMOKE TEST FAILED")
    print("="*70)
    print(f"Error: {result.stderr}")
    sys.exit(1)

# Verify output files exist
if Path('results/ablation_study_results.csv').exists():
    print(f"✓ Results file created")
else:
    print(f"⚠️  Results file not found")

if Path('results/ablation_checkpoint.csv').exists():
    print(f"✓ Checkpoint file created")
else:
    print(f"⚠️  Checkpoint file not found")