"""
Reader Evaluation Launch Check
==============================

Runs a subset of the reader evaluation harness as a pre-deployment gate.
Tests standards parsers and CSV normalization with synthetic fixtures.

Returns SKIP if reader_eval is disabled in config.
Returns FAIL if evaluation score is below threshold.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Tuple


def run_reader_eval(config: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    """
    Run reader evaluation harness.
    
    Args:
        config: Launch checks configuration
        
    Returns:
        Tuple of (status, message, evidence)
        - status: "PASS" | "FAIL" | "SKIP"
        - message: Human-readable result
        - evidence: Dict with details
    """
    # Check if reader_eval is enabled
    reader_eval_config = config.get('checks', {}).get('reader_eval', {})
    enabled = reader_eval_config.get('enabled', False)
    
    if not enabled:
        return (
            "SKIP",
            "Reader evaluation disabled in config",
            {"enabled": False}
        )
    
    # Get thresholds
    min_pass_rate = reader_eval_config.get('min_pass_rate', 0.95)
    subset_datasets = reader_eval_config.get('subset_datasets', [
        'camt053_min',
        'mt940_min',
        'bai2_min',
        'ofx_min'
    ])
    
    # Run evaluation harness
    try:
        eval_config_path = Path("ops/reader_eval/config.yaml")
        output_dir = Path("out/reader_eval_launch_check")
        
        if not eval_config_path.exists():
            return (
                "FAIL",
                f"Reader eval config not found: {eval_config_path}",
                {"config_path": str(eval_config_path)}
            )
        
        # Run eval
        result = subprocess.run(
            [
                sys.executable,
                "ops/reader_eval/run_eval.py",
                "--config", str(eval_config_path),
                "--out", str(output_dir)
            ],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        # Find latest report
        report_dirs = sorted(output_dir.glob("*"), key=lambda p: p.name, reverse=True)
        if not report_dirs:
            return (
                "FAIL",
                "No evaluation report generated",
                {"stdout": result.stdout, "stderr": result.stderr}
            )
        
        report_path = report_dirs[0] / "report.json"
        
        if not report_path.exists():
            return (
                "FAIL",
                f"Report file not found: {report_path}",
                {"report_path": str(report_path)}
            )
        
        # Load report
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Extract metrics
        summary = report.get('summary', {})
        total = summary.get('datasets', 0)
        passed = summary.get('pass', 0)
        failed = summary.get('fail', 0)
        
        if total == 0:
            return (
                "FAIL",
                "No datasets evaluated",
                {"report": report}
            )
        
        pass_rate = passed / total
        
        # Check threshold
        if pass_rate >= min_pass_rate:
            return (
                "PASS",
                f"Reader evaluation passed: {passed}/{total} datasets passed ({pass_rate:.1%})",
                {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": pass_rate,
                    "threshold": min_pass_rate,
                    "metrics": report.get('metrics', {})
                }
            )
        else:
            return (
                "FAIL",
                f"Reader evaluation failed: {passed}/{total} passed ({pass_rate:.1%}), threshold is {min_pass_rate:.1%}",
                {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": pass_rate,
                    "threshold": min_pass_rate,
                    "failed_datasets": [
                        d['name'] for d in report.get('datasets', [])
                        if d.get('status') == 'FAIL'
                    ]
                }
            )
    
    except subprocess.TimeoutExpired:
        return (
            "FAIL",
            "Reader evaluation timed out (>2 minutes)",
            {"timeout": 120}
        )
    
    except Exception as e:
        return (
            "FAIL",
            f"Reader evaluation error: {str(e)}",
            {"error": str(e), "error_type": type(e).__name__}
        )


if __name__ == '__main__':
    # Standalone test
    import yaml
    
    config_path = Path("ops/launch_checks/config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {
            'checks': {
                'reader_eval': {
                    'enabled': True,
                    'min_pass_rate': 0.95
                }
            }
        }
    
    status, message, evidence = run_reader_eval(config)
    
    print(f"Status: {status}")
    print(f"Message: {message}")
    print(f"Evidence: {json.dumps(evidence, indent=2)}")
    
    sys.exit(0 if status == "PASS" else 1)



