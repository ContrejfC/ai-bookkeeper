"""
Synthetic Bank Statement Generator
===================================

Generates realistic bank statement PDFs using ReportLab from YAML style definitions.

Supports:
- Multiple statement types (checking, credit card, account analysis)
- Customizable layouts and styles
- Running balance calculations
- Multi-page rendering
- Noise/scan simulation
"""

from scripts.synth_statements.generator import generate_statement, StatementGenerator

__all__ = ["generate_statement", "StatementGenerator"]



