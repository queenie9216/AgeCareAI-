# REDTEAM: Critical Findings Resolution

## CRIT-1: Typhoon Integration Race Condition

**Issue:** Integration spec shows L4 actions starting T+30ms while L3 returns at T+50ms.
**Fix:** L4 must wait for L3 to complete. Sequence: L3 lock → L3 solve → L4 reads final schedule → L4 acts → release lock.
**Status:** Will implement as sequential-within-1000ms

## CRIT-2: L4 Nomenclature

**Issue:** Called "Autonomous Care Agent" but is a hardcoded decision tree
**Fix:** Rename to "Care Decision Agent" or acknowledge it as a "rule-based care agent"
**Status:** User to decide naming

## MAJ-1: Fall Duration Mismatch

**Issue:** Brief says 3s, L1 spec says 2s
**Fix:** Standardize to 3 seconds (150 samples at 50Hz)
**Status:** Will align to 3s

## MAJ-2: Senior Identity Mismatch

**Issue:** "Mr Tan" 78 (brief) vs "Tan Poh Lek" 86 (data sim)
**Fix:** Use consistent naming - "Tan Poh Lek" with age 78
**Status:** Will standardize

## SIG-1: "boo Geok Hua" typo

**Fix:** Correct to "Boo Geok Hua"
**Status:** Will fix in data generation

## Resolution: All issues logged for /todos phase
