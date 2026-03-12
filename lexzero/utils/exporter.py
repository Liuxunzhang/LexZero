"""Export functionality for results"""

import csv
import json
from pathlib import Path
from typing import List, Tuple
from datetime import datetime


class ResultExporter:
    """Export table results to various formats"""

    @staticmethod
    def export_csv(columns: List[str], rows: List[Tuple], filepath: str) -> bool:
        """Export results to CSV file"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)
            return True
        except Exception as e:
            print(f"CSV export failed: {e}")
            return False

    @staticmethod
    def export_json(columns: List[str], rows: List[Tuple], filepath: str) -> bool:
        """Export results to JSON file"""
        try:
            data = []
            for row in rows:
                row_dict = {col: val for col, val in zip(columns, row)}
                data.append(row_dict)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"JSON export failed: {e}")
            return False

    @staticmethod
    def export_txt(columns: List[str], rows: List[Tuple], filepath: str) -> bool:
        """Export results to plain text file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write(" | ".join(columns) + "\n")
                f.write("-" * (sum(len(c) for c in columns) + len(columns) * 3) + "\n")

                # Write rows
                for row in rows:
                    f.write(" | ".join(str(cell) for cell in row) + "\n")
            return True
        except Exception as e:
            print(f"TXT export failed: {e}")
            return False

    @staticmethod
    def auto_export(columns: List[str], rows: List[Tuple], plugin_name: str, format: str = "csv") -> str:
        """Auto-generate filename and export"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{plugin_name}_{timestamp}.{format}"

        export_dir = Path.home() / "lexzero_exports"
        export_dir.mkdir(exist_ok=True)

        filepath = export_dir / filename

        if format == "csv":
            success = ResultExporter.export_csv(columns, rows, str(filepath))
        elif format == "json":
            success = ResultExporter.export_json(columns, rows, str(filepath))
        elif format == "txt":
            success = ResultExporter.export_txt(columns, rows, str(filepath))
        else:
            return None

        return str(filepath) if success else None
