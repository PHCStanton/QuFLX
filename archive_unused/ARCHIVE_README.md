# Archive of Unused/Redundant Files

**Archived Date**: October 4, 2025

This directory contains files and folders that are not used in the current QuantumFlux architecture but are preserved for reference.

## Archived Items:

### 1. src_new/ - Empty DDD Architecture Skeleton
- Never implemented Domain-Driven Design structure
- All files are empty __init__.py files
- Was a planning exercise that went unused

### 2. tests_new/ - Empty Test Structure
- Skeleton for new test architecture
- Never implemented
- Current tests in tests/ are used instead

### 3. src/ - Adapter Layer
- capabilities_adapter.py and related code
- Simplified away in current architecture
- Backend now uses capabilities directly without adapter

### 4. strategies/strategy_calibration/ - Offline Testing Scripts
- Used for strategy development and analysis
- Not part of runtime system
- Contains: performance_analysis/, summary_reports/, testing_scripts/, validation_reports/

### 5. strategies_misc/ - Alternative Strategy Implementations
- Experimental strategy code not used in GUI
- enhanced_strategy_engine.py, indicators.py, strata.py, etc.

### 6. config_new/ - Unused Configuration Structure
- Planned configuration system that wasn't implemented

### 7. docs_new/ - Superseded Documentation
- Old architecture and development guidelines
- Replaced by current documentation

### 8. AGENT_docs/ - Old Agent Documentation
- Superseded by .agent-memory/project-status.md
- Previous task messages and memory system setup

### 9. capabilities/original_*.py - Old Capability Versions
- original_favorite_select.py
- original_topdown_select.py
- Kept current versions only

### 10. GUI Documentation Duplicates
- Various markdown files in gui/ that are redundant

## Current Active Architecture:

- **Backend**: gui/Data-Visualizer-React/streaming_server.py (Flask-SocketIO)
- **Frontend**: gui/Data-Visualizer-React/src/ (React)
- **Strategies**: strategies/quantum_flux_strategy.py (active)
- **Capabilities**: capabilities/*.py (direct usage, no adapter)
- **CLI**: qf.py
- **Main Backend**: backend.py (FastAPI)

## Restore Instructions:

If any archived file is needed, simply copy it back to its original location in the project root.
