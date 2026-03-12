"""Demo mode for testing LexZero without a real memory image"""

from typing import List, Dict, Tuple


class DemoDataProvider:
    """Provide demo data for testing"""

    @staticmethod
    def get_demo_data(plugin_name: str) -> Tuple[List[str], List[Tuple]]:
        """Get demo data for a plugin"""

        # Process-related plugins
        if "pslist" in plugin_name.lower():
            columns = ["PID", "PPID", "COMM", "UID", "GID"]
            rows = [
                ("1", "0", "systemd", "0", "0"),
                ("2", "0", "kthreadd", "0", "0"),
                ("100", "1", "sshd", "0", "0"),
                ("256", "1", "nginx", "33", "33"),
                ("512", "1", "mysqld", "27", "27"),
                ("1024", "100", "bash", "1000", "1000"),
                ("2048", "1024", "python3", "1000", "1000"),
            ]
            return columns, rows

        elif "lsmod" in plugin_name.lower():
            columns = ["Module", "Size", "Used By"]
            rows = [
                ("ext4", "737280", "2"),
                ("mbcache", "16384", "1 ext4"),
                ("jbd2", "131072", "1 ext4"),
                ("ip_tables", "32768", "0"),
                ("x_tables", "40960", "1 ip_tables"),
            ]
            return columns, rows

        elif "bash" in plugin_name.lower():
            columns = ["PID", "Command", "Timestamp"]
            rows = [
                ("1024", "ls -la", "2024-03-12 10:30:00"),
                ("1024", "cd /var/log", "2024-03-12 10:31:00"),
                ("1024", "cat syslog", "2024-03-12 10:32:00"),
                ("1024", "ps aux | grep nginx", "2024-03-12 10:33:00"),
            ]
            return columns, rows

        elif "sockstat" in plugin_name.lower() or "net" in plugin_name.lower():
            columns = ["Protocol", "Local Address", "Foreign Address", "State", "PID"]
            rows = [
                ("TCP", "0.0.0.0:22", "0.0.0.0:*", "LISTEN", "100"),
                ("TCP", "0.0.0.0:80", "0.0.0.0:*", "LISTEN", "256"),
                ("TCP", "192.168.1.100:22", "192.168.1.50:54321", "ESTABLISHED", "100"),
                ("TCP", "0.0.0.0:3306", "0.0.0.0:*", "LISTEN", "512"),
            ]
            return columns, rows

        elif "malfind" in plugin_name.lower():
            columns = ["PID", "Process", "Start", "End", "Protection", "Hexdump"]
            rows = [
                ("2048", "python3", "0x7f1234000000", "0x7f1234001000", "PAGE_EXECUTE_READWRITE", "4d 5a 90 00..."),
            ]
            return columns, rows

        elif "check" in plugin_name.lower():
            columns = ["Check", "Status", "Details"]
            rows = [
                ("Syscall Table", "OK", "No hooks detected"),
                ("IDT", "OK", "All entries valid"),
                ("Module List", "OK", "No hidden modules"),
            ]
            return columns, rows

        # Default demo data
        else:
            columns = ["Item", "Value", "Description"]
            rows = [
                ("Demo Mode", "Active", "使用演示数据"),
                ("Plugin", plugin_name, "当前插件"),
                ("Status", "OK", "演示模式正常"),
            ]
            return columns, rows


def is_demo_mode_enabled() -> bool:
    """Check if demo mode should be enabled"""
    import os
    return os.environ.get("LEXZERO_DEMO", "0") == "1"
