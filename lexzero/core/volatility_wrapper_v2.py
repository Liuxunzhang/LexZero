"""Volatility3 wrapper using command line interface"""

import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import subprocess
import csv

try:
    from volatility3 import framework
    import volatility3.plugins
    VOLATILITY_AVAILABLE = True
except ImportError:
    VOLATILITY_AVAILABLE = False
    logging.warning("Volatility3 not available")


class VolatilityWrapper:
    """Wrapper class for Volatility3 operations using CLI"""

    def __init__(self, image_path: Optional[str] = None):
        self.image_path = image_path
        self.plugin_list = []
        self._cache = {}  # Cache for plugin results: {plugin_name: (columns, rows)}
        self._init_volatility()

    def _init_volatility(self):
        """Initialize Volatility3 framework to get plugin list"""
        if not VOLATILITY_AVAILABLE:
            logging.error("Volatility3 is not installed")
            return

        try:
            framework.require_interface_version(2, 0, 0)
            framework.import_files(volatility3.plugins, True)
            self.plugin_list = list(framework.list_plugins())
        except Exception as e:
            logging.error(f"Failed to initialize Volatility3: {e}")

    def load_image(self, image_path: str) -> bool:
        """Load a memory image"""
        try:
            img_path = Path(image_path)
            if not img_path.exists():
                logging.error(f"Image file does not exist: {image_path}")
                return False

            self.image_path = str(img_path.absolute())
            # Clear cache when loading new image
            self._cache.clear()
            logging.info(f"Successfully loaded image: {self.image_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to load image: {e}", exc_info=True)
            return False

    def get_available_plugins(self) -> List[Dict[str, str]]:
        """Get list of available Volatility3 plugins"""
        result = []
        for plugin_name in self.plugin_list:
            # plugin_name is a string like "windows.pslist.PsList"
            result.append({
                "name": plugin_name,
                "description": "Volatility3 plugin"
            })
        return result

    def run_plugin(self, plugin_name: str, progress_callback=None, use_cache: bool = True) -> Tuple[List[str], List[Tuple]]:
        """Run a Volatility3 plugin using command line

        Args:
            plugin_name: Name of the plugin to run
            progress_callback: Optional callback for progress updates
            use_cache: If True, return cached results if available

        Returns:
            Tuple of (columns, rows)
        """
        if not self.image_path:
            raise ValueError("No memory image loaded")

        # Check cache first
        if use_cache and plugin_name in self._cache:
            logging.info(f"Returning cached results for {plugin_name}")
            if progress_callback:
                progress_callback("Using cached results")
            return self._cache[plugin_name]

        # Build command: vol -f <image> -r csv <plugin>
        cmd = ["vol", "-f", self.image_path, "-r", "csv", plugin_name]

        logging.info(f"Running command: {' '.join(cmd)}")
        if progress_callback:
            progress_callback(f"Starting: {plugin_name}")

        try:
            import threading
            import queue
            import re

            stderr_lines = []

            def read_stderr(pipe, q):
                """Read stderr in a separate thread"""
                try:
                    for line in iter(pipe.readline, ''):
                        if line:
                            stderr_lines.append(line)
                            # Extract progress percentage
                            match = re.search(r'Progress:\s+([\d.]+)', line)
                            if match:
                                percentage = match.group(1)
                                q.put(f"Progress: {percentage}%")
                except Exception as e:
                    logging.error(f"Error reading stderr: {e}")
                finally:
                    pipe.close()

            # Run vol command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Create queue for progress updates
            output_queue = queue.Queue()

            # Start thread to read stderr
            stderr_thread = threading.Thread(
                target=read_stderr,
                args=(process.stderr, output_queue)
            )
            stderr_thread.daemon = True
            stderr_thread.start()

            # Monitor progress while waiting
            last_progress = None
            while process.poll() is None:
                try:
                    progress_msg = output_queue.get(timeout=0.1)
                    if progress_msg != last_progress and progress_callback:
                        progress_callback(progress_msg)
                        last_progress = progress_msg
                except queue.Empty:
                    pass

            # Wait for stderr thread to finish
            stderr_thread.join(timeout=1.0)

            # Get stdout
            stdout = process.stdout.read()
            process.stdout.close()

            if process.returncode != 0:
                error_msg = ''.join(stderr_lines).strip()
                logging.error(f"Vol command failed: {error_msg}")
                raise ValueError(f"Plugin execution failed: {error_msg[:200]}")

            # Parse CSV output
            output_lines = stdout.strip().split('\n')
            if not output_lines:
                return [], []

            # First line is columns
            reader = csv.reader(output_lines)
            rows_list = list(reader)

            if not rows_list:
                return [], []

            columns = rows_list[0]
            data_rows = [tuple(row) for row in rows_list[1:]]

            logging.info(f"Got {len(data_rows)} rows from vol command")

            # Cache the results
            self._cache[plugin_name] = (columns, data_rows)

            return columns, data_rows

        except subprocess.TimeoutExpired:
            logging.error(f"Plugin {plugin_name} timed out after 120s")
            raise ValueError(f"Plugin execution timed out (>120s)")
        except Exception as e:
            logging.error(f"Error running vol command: {e}", exc_info=True)
            raise

    def clear_cache(self, plugin_name: Optional[str] = None):
        """Clear cached results

        Args:
            plugin_name: If specified, clear only this plugin's cache.
                        If None, clear all cache.
        """
        if plugin_name:
            self._cache.pop(plugin_name, None)
            logging.info(f"Cleared cache for {plugin_name}")
        else:
            self._cache.clear()
            logging.info("Cleared all cache")

    def get_plugin_categories(self) -> Dict[str, List[str]]:
        """Categorize Linux plugins by functionality"""
        categories = {
            "进程相关": [],
            "文件/模块": [],
            "网络相关": [],
            "内存/恶意代码": [],
            "安全检查/Rootkit": [],
            "系统信息/调试": [],
            "追踪/调试": [],
            "Malware专项": [],
        }

        for plugin_name in self.plugin_list:
            # Only process Linux plugins
            if not plugin_name.startswith("linux."):
                continue

            simple_name = plugin_name  # Keep full name like "linux.pslist.PsList"
            name_lower = plugin_name.lower()

            # 进程相关
            if any(x in name_lower for x in ["pslist", "psscan", "pstree", "psaux", "envars", "kthreads"]):
                categories["进程相关"].append(simple_name)
            # 文件/模块
            elif any(x in name_lower for x in ["lsof", "lsmod", "modxview", "hidden_modules", "elfs", "library_list", "mountinfo", "module_extract"]) and "malware" not in name_lower:
                categories["文件/模块"].append(simple_name)
            # 网络相关
            elif any(x in name_lower for x in ["sockstat", "netfilter", "ip.addr", "ip.link"]) and "malware" not in name_lower:
                categories["网络相关"].append(simple_name)
            # 内存/恶意代码
            elif any(x in name_lower for x in ["malfind", "proc.maps", "vmaregexscan", "pagecache"]) and "malware" not in name_lower:
                categories["内存/恶意代码"].append(simple_name)
            # 安全检查/Rootkit
            elif any(x in name_lower for x in ["check_syscall", "check_afinfo", "check_idt", "check_modules", "check_creds", "capabilities", "keyboard_notifiers", "tty_check", "ebpf"]) and "malware" not in name_lower:
                categories["安全检查/Rootkit"].append(simple_name)
            # 系统信息/调试
            elif any(x in name_lower for x in ["bash", "kmsg", "boottime", "kallsyms", "iomem", "vmcoreinfo", "pidhashtable", "fbdev"]):
                categories["系统信息/调试"].append(simple_name)
            # 追踪/调试
            elif any(x in name_lower for x in ["ftrace", "tracepoints", "perf_events", "pscallstack", "ptrace"]):
                categories["追踪/调试"].append(simple_name)
            # Malware专项
            elif "malware" in name_lower:
                categories["Malware专项"].append(simple_name)

        # Sort each category and remove empty ones
        result = {}
        for category, plugins in categories.items():
            if plugins:
                result[category] = sorted(plugins)

        return result
