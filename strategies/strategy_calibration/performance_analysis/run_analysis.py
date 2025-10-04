#!/usr/bin/env python3
"""
Multi-Data Source Analysis Runner
Easy script to test strategies on different data sources.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_analysis(data_source, strategy_config, max_files=10, timeframe="1min"):
    """Run performance analysis on specified data source."""
    
    # Data source mapping
    data_sources = {
        "1min": "data/data_1m",
        "5min": "data/data_5m", 
        "backtest": "data/backtest",
        "live": "data/live",
        "pocket_option": "data/pocket_option",
        "processed": "data/processed",
        "raw": "data/raw",
        "tick": "data/tick_data"
    }
    
    # Strategy config mapping
    strategy_configs = {
        "1min": "config/strategies/quantum_flux_1min.json",
        "5min": "config/strategies/quantum_flux_5min.json",
        "original": "config/strategies/quantum_flux.json",
        "optimized": "config/strategies/quantum_flux_optimized.json"
    }
    
    # Get data directory
    data_dir = data_sources.get(data_source, data_source)
    
    # Get strategy config
    if strategy_config in strategy_configs:
        config_file = strategy_configs[strategy_config]
    else:
        config_file = strategy_config
    
    # Check if data directory exists
    if not os.path.exists(data_dir):
        print(f"❌ Error: Data directory '{data_dir}' does not exist!")
        return False
    
    # Check if config file exists
    if not os.path.exists(config_file):
        print(f"❌ Error: Config file '{config_file}' does not exist!")
        return False
    
    # Count CSV files
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not csv_files:
        print(f"❌ Error: No CSV files found in '{data_dir}'!")
        return False
    
    print(f"🔍 RUNNING ANALYSIS")
    print(f"📂 Data Source: {data_dir} ({len(csv_files)} CSV files)")
    print(f"⚙️  Strategy Config: {config_file}")
    print(f"📊 Max Files: {max_files}")
    print(f"🕐 Timeframe: {timeframe}")
    print("=" * 60)
    
    # Run the analysis
    cmd = [
        "python", 
        "src/quantumflux/strategies/strategy_calibration/performance_analysis/signal_performance_analyzer_optimized.py",
        "--data-dir", data_dir,
        "--config", config_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Multi-Data Source Analysis Runner")
    
    parser.add_argument("--data", "-d", 
                       choices=["1min", "5min", "backtest", "live", "pocket_option", "processed", "raw", "tick"],
                       default="1min",
                       help="Data source to analyze")
    
    parser.add_argument("--strategy", "-s",
                       choices=["1min", "5min", "original", "optimized"],
                       default="1min", 
                       help="Strategy configuration to use")
    
    parser.add_argument("--max-files", "-m", type=int, default=10,
                       help="Maximum number of files to analyze")
    
    parser.add_argument("--list-data", "-l", action="store_true",
                       help="List available data sources")
    
    args = parser.parse_args()
    
    if args.list_data:
        print("📂 AVAILABLE DATA SOURCES:")
        data_dirs = [
            ("1min", "data/data_1m", "1-minute candle data"),
            ("5min", "data/data_5m", "5-minute candle data"),  
            ("backtest", "data/backtest", "Historical backtest data"),
            ("live", "data/live", "Live market data"),
            ("pocket_option", "data/pocket_option", "Pocket Option data"),
            ("processed", "data/processed", "Pre-processed data"),
            ("raw", "data/raw", "Raw market data"),
            ("tick", "data/tick_data", "Tick-level data")
        ]
        
        for key, path, desc in data_dirs:
            exists = "✅" if os.path.exists(path) else "❌"
            csv_count = len([f for f in os.listdir(path) if f.endswith('.csv')]) if os.path.exists(path) else 0
            print(f"  {exists} {key:12} | {path:20} | {desc} ({csv_count} files)")
        
        print(f"\n⚙️  AVAILABLE STRATEGY CONFIGS:")
        configs = [
            ("1min", "config/strategies/quantum_flux_1min.json", "1-min optimized strategy"),
            ("5min", "config/strategies/quantum_flux_5min.json", "5-min optimized strategy"),
            ("original", "config/strategies/quantum_flux.json", "Original strategy"),
            ("optimized", "config/strategies/quantum_flux_optimized.json", "General optimized")
        ]
        
        for key, path, desc in configs:
            exists = "✅" if os.path.exists(path) else "❌"
            print(f"  {exists} {key:12} | {path:35} | {desc}")
        return
    
    # Run the analysis
    success = run_analysis(args.data, args.strategy, args.max_files)
    
    if success:
        print(f"\n✅ Analysis completed successfully!")
    else:
        print(f"\n❌ Analysis failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()