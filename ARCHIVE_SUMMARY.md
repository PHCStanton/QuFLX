# Archive Summary - October 4, 2025

## Successfully Archived 🗄️

A total of **1.3MB** across **18 items** have been moved to `archive_unused/` directory.

## What Was Archived:

### 1. **src_new/** (389 lines total)
   - Empty Domain-Driven Design architecture skeleton
   - All files were just `__init__.py` placeholders
   - Never implemented beyond planning stage

### 2. **tests_new/** (40 lines total)
   - Empty test structure skeleton
   - Never implemented
   - Current tests in `tests/` directory are active

### 3. **src/** (adapter layer)
   - `capabilities_adapter.py` and supporting files
   - Was used to wrap capabilities for backend
   - **Architecture simplified**: Backend now uses capabilities directly
   - No longer needed in current architecture

### 4. **strategies/strategy_calibration/**
   - Performance analysis scripts
   - Signal performance analyzers
   - Testing and validation scripts
   - JSON reports and summaries
   - **Use case**: Offline strategy development only, not runtime

### 5. **strategies_misc/**
   - Alternative strategy implementations
   - `enhanced_strategy_engine.py`, `indicators.py`, `strata.py`
   - Experimental code not integrated into GUI

### 6. **config_new/** and **docs_new/**
   - Unused configuration and documentation structures
   - Superseded by current implementation

### 7. **AGENT_docs/**
   - Old agent documentation
   - Replaced by `.agent-memory/project-status.md`

### 8. **capabilities/original_*.py**
   - `original_favorite_select.py`
   - `original_topdown_select.py`
   - Old versions kept for reference only

### 9. **GUI Documentation Files**
   - `Markup Visualizer_Extended_Plan.md`
   - `Tradingview-Troubleshooting.md`
   - `TradingVIewCharts_Setup_Installation.md`
   - `Visualizer_TODO.md`
   - `Bug_fixes.md`
   - `gui_agent_memory/` (old agent memory)
   - `gui_MVP_Recommend.md`
   - Superseded by current documentation

## Current Clean Architecture:

```
QuantumFlux/
├── archive_unused/          # Archived files (preserved for reference)
├── capabilities/            # Core trading capabilities
├── gui/                     # React GUI + Flask backend
│   └── Data-Visualizer-React/
├── pipelines/               # JSON pipeline configurations
├── scripts/                 # Utility scripts
├── strategies/              # Active strategies (quantum_flux, etc.)
├── tests/                   # Active test suite
├── utils/                   # Utility functions
├── backend.py               # FastAPI backend
├── qf.py                    # CLI interface
└── start_hybrid_session.py  # Chrome session launcher
```

## Active Components:

✅ **Backend**: `gui/Data-Visualizer-React/streaming_server.py` (Port 3001)  
✅ **Frontend**: `gui/Data-Visualizer-React/src/` (Port 5000)  
✅ **Main Backend**: `backend.py` (Port 8000)  
✅ **Strategies**: `strategies/quantum_flux_strategy.py`  
✅ **Capabilities**: Direct usage, no adapter layer  
✅ **CLI**: `qf.py`  

## Benefits:

1. **Cleaner Project Structure**: Removed 1.3MB of unused code
2. **Reduced Complexity**: No confusion about which files are active
3. **Easier Navigation**: Focus on working components only
4. **Preserved History**: All files still accessible in archive
5. **Better Documentation**: Clear separation of active vs archived

## Restore Instructions:

If any archived file is needed:
```bash
# Example: Restore strategy calibration
cp -r archive_unused/strategy_calibration strategies/

# Example: Restore adapter layer
cp -r archive_unused/src .
```

## Notes:

- All archived code is **preserved and accessible**
- Nothing was deleted permanently
- Archive is documented in `archive_unused/ARCHIVE_README.md`
- LSP may still cache old file paths (will clear on restart)

**Result**: Lean, production-ready codebase focused on current architecture! 🚀
