# MineProductivity Release Checklist

Every package implementation MUST satisfy every item in this checklist before merge.

---

# Documentation

□ Design Specification exists
□ Implementation Checklist exists
□ Package README complete
□ API documented
□ Examples documented
□ Architecture unchanged
□ Handbook still valid
□ Cookbook updated if required

---

# Architecture

□ Dependency direction preserved
□ No cyclic imports
□ SOLID maintained
□ Plugin-first maintained
□ Event-first maintained
□ Metadata-first maintained
□ Ontology-first maintained

---

# Quality

□ Ruff passes
□ Mypy strict passes
□ Pytest passes
□ Coverage >=95%
□ Public API tested
□ Serialization tested
□ Error handling tested

---

# Performance

□ Benchmarks updated
□ No regression
□ Memory acceptable
□ Import time acceptable

---

# Examples

□ Quickstart example
□ Beginner example
□ Advanced example
□ Notebook updated

---

# Dataset

□ Sample dataset added
□ Golden dataset updated
□ Benchmark dataset updated

---

# Documentation Sync

□ Architecture Handbook reviewed
□ Blueprint reviewed
□ Cookbook updated
□ Learning Suite updated

---

# Release

□ CHANGELOG updated
□ Version bumped
□ Git tag created
□ GitHub Release created
□ Milestone closed
□ Next milestone opened

---

# Final Approval

□ Documentation complete
□ Tests passing
□ CI passing
□ Ready for merge

Signature

Package:
Version:
Reviewer:
Date:


-------------------

This checklist is mandatory.

No implementation package may be merged into main unless every item above has been satisfied.

If any item cannot be completed, the Pull Request must clearly justify why.

This document is part of the MineProductivity Engineering Governance.

--------------------

