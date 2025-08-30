#!/usr/bin/env python3
"""
MT4 Integration Module for MQL-Python Converter
Provides tools for running and integrating with MT4 in WSL/Linux
"""

import os
import sys
import json
import time
import socket
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from converters.mql5_converter import MQL5Converter
except ImportError:
    print("Warning: MQL5Converter not available")
    MQL5Converter = None


@dataclass
class MT4Config:
    """MT4 configuration settings"""
    wine_prefix: Path = Path.home() / ".wine"
    mt4_install_path: Optional[Path] = Path("/home/developer/mql-python-converter/servers/mt-terminal")
    data_bridge_port: int = 9999
    use_wine: bool = True
    terminal_id: Optional[str] = None


class MT4Runner:
    """Manages MT4 execution through Wine"""
    
    def __init__(self, config: MT4Config = None):
        self.config = config or MT4Config()
        self.mt4_path = self._find_mt4_installation()
        self.wine_initialized = self._check_wine()
        
    def _check_wine(self) -> bool:
        """Check if Wine is properly installed and configured"""
        try:
            result = subprocess.run(
                ["wine", "--version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _find_mt4_installation(self) -> Optional[Path]:
        """Find MT4 installation in Wine prefix"""
        if self.config.mt4_install_path and self.config.mt4_install_path.exists():
            return self.config.mt4_install_path
        
        possible_paths = [
            self.config.wine_prefix / "drive_c/Program Files (x86)/MetaTrader 4",
            self.config.wine_prefix / "drive_c/Program Files/MetaTrader 4",
            self.config.wine_prefix / "drive_c/MT4",
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "terminal.exe").exists():
                return path
        
        return None
    
    def install_mt4(self, installer_path: str = None) -> bool:
        """Install MT4 using Wine"""
        if not self.wine_initialized:
            print("Wine is not initialized. Run 'winecfg' first.")
            return False
        
        if not installer_path:
            print("Downloading MT4 installer...")
            # Download a generic MT4 installer
            installer_url = "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt4/mt4setup.exe"
            installer_path = "/tmp/mt4setup.exe"
            
            try:
                subprocess.run(
                    ["wget", "-O", installer_path, installer_url],
                    check=True
                )
            except subprocess.CalledProcessError:
                print("Failed to download MT4 installer")
                return False
        
        print(f"Installing MT4 from {installer_path}...")
        try:
            subprocess.run(
                ["wine", installer_path],
                check=True
            )
            self.mt4_path = self._find_mt4_installation()
            return self.mt4_path is not None
        except subprocess.CalledProcessError:
            print("MT4 installation failed")
            return False
    
    def run_terminal(self, config_file: str = None, portable: bool = False) -> subprocess.Popen:
        """Run MT4 terminal"""
        if not self.mt4_path:
            raise RuntimeError("MT4 is not installed")
        
        terminal_exe = self.mt4_path / "terminal.exe"
        if not terminal_exe.exists():
            raise RuntimeError(f"terminal.exe not found at {terminal_exe}")
        
        cmd = ["wine", str(terminal_exe)]
        
        if portable:
            cmd.append("/portable")
        
        if config_file:
            cmd.extend(["/config", config_file])
        
        print(f"Starting MT4: {' '.join(cmd)}")
        
        # Set display for GUI
        env = os.environ.copy()
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"
        
        return subprocess.Popen(cmd, env=env)
    
    def get_data_folder(self) -> Optional[Path]:
        """Get MT4 data folder path"""
        if not self.mt4_path:
            return None
        
        # Check for MQL4 folder in installation directory (portable mode)
        mql4_folder = self.mt4_path / "MQL4"
        if mql4_folder.exists():
            return mql4_folder
        
        # Check in user's AppData
        appdata_base = self.config.wine_prefix / "drive_c/users" / os.environ.get("USER", "user")
        terminal_data = appdata_base / "AppData/Roaming/MetaQuotes/Terminal"
        
        if terminal_data.exists():
            # Find the terminal ID folder
            for folder in terminal_data.iterdir():
                if folder.is_dir() and (folder / "MQL4").exists():
                    return folder / "MQL4"
        
        return None


class MT4DataBridge:
    """Bridge for real-time data exchange between MT4 and Python"""
    
    def __init__(self, config: MT4Config = None):
        self.config = config or MT4Config()
        self.server_socket = None
        self.is_running = False
        self.data_buffer = []
        
    def start_server(self, callback=None):
        """Start data bridge server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', self.config.data_bridge_port))
        self.server_socket.listen(5)
        self.is_running = True
        
        print(f"Data bridge server started on port {self.config.data_bridge_port}")
        
        def server_loop():
            while self.is_running:
                try:
                    client_socket, address = self.server_socket.accept()
                    data = client_socket.recv(4096).decode('utf-8')
                    
                    if data:
                        parsed_data = self._parse_mt4_data(data)
                        self.data_buffer.append(parsed_data)
                        
                        if callback:
                            callback(parsed_data)
                    
                    # Send acknowledgment
                    client_socket.send(b"OK")
                    client_socket.close()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Server error: {e}")
        
        server_thread = threading.Thread(target=server_loop, daemon=True)
        server_thread.start()
        
        return server_thread
    
    def stop_server(self):
        """Stop data bridge server"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
    
    def _parse_mt4_data(self, data: str) -> Dict:
        """Parse data received from MT4"""
        try:
            # Try JSON format first
            return json.loads(data)
        except json.JSONDecodeError:
            # Fall back to CSV format
            parts = data.strip().split(',')
            if len(parts) >= 4:
                return {
                    'symbol': parts[0],
                    'time': parts[1],
                    'bid': float(parts[2]),
                    'ask': float(parts[3]),
                    'timestamp': datetime.now().isoformat()
                }
            return {'raw_data': data, 'timestamp': datetime.now().isoformat()}
    
    def get_latest_data(self, symbol: str = None) -> Optional[Dict]:
        """Get latest data from buffer"""
        if not self.data_buffer:
            return None
        
        if symbol:
            # Filter by symbol
            symbol_data = [d for d in self.data_buffer if d.get('symbol') == symbol]
            return symbol_data[-1] if symbol_data else None
        
        return self.data_buffer[-1]
    
    def clear_buffer(self):
        """Clear data buffer"""
        self.data_buffer.clear()


class MT4FileExporter:
    """Export and convert MT4 files"""
    
    def __init__(self, mt4_runner: MT4Runner):
        self.mt4_runner = mt4_runner
        self.converter = MQL5Converter() if MQL5Converter else None
        
    def export_experts(self, output_dir: str = "exported_experts") -> List[Path]:
        """Export Expert Advisors from MT4"""
        mql4_folder = self.mt4_runner.get_data_folder()
        if not mql4_folder:
            print("MQL4 folder not found")
            return []
        
        experts_folder = mql4_folder / "Experts"
        if not experts_folder.exists():
            print("Experts folder not found")
            return []
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        exported_files = []
        for ea_file in experts_folder.glob("*.mq4"):
            dest_file = output_path / ea_file.name
            
            # Copy file
            import shutil
            shutil.copy(ea_file, dest_file)
            exported_files.append(dest_file)
            print(f"Exported: {ea_file.name}")
        
        return exported_files
    
    def export_indicators(self, output_dir: str = "exported_indicators") -> List[Path]:
        """Export Indicators from MT4"""
        mql4_folder = self.mt4_runner.get_data_folder()
        if not mql4_folder:
            print("MQL4 folder not found")
            return []
        
        indicators_folder = mql4_folder / "Indicators"
        if not indicators_folder.exists():
            print("Indicators folder not found")
            return []
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        exported_files = []
        for ind_file in indicators_folder.glob("*.mq4"):
            dest_file = output_path / ind_file.name
            
            # Copy file
            import shutil
            shutil.copy(ind_file, dest_file)
            exported_files.append(dest_file)
            print(f"Exported: {ind_file.name}")
        
        return exported_files
    
    def convert_to_python(self, mql_file: Path, output_dir: str = "converted_python") -> Optional[Path]:
        """Convert MQL4 file to Python"""
        if not self.converter:
            print("MQL5Converter not available")
            return None
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        with open(mql_file, 'r', encoding='utf-8', errors='ignore') as f:
            mql_code = f.read()
        
        try:
            python_code = self.converter.convert(mql_code)
            
            output_file = output_path / f"{mql_file.stem}.py"
            with open(output_file, 'w') as f:
                f.write(python_code)
            
            print(f"Converted: {mql_file.name} -> {output_file.name}")
            return output_file
            
        except Exception as e:
            print(f"Conversion failed for {mql_file.name}: {e}")
            return None


def create_mql4_bridge_ea():
    """Create MQL4 Expert Advisor for data bridge"""
    ea_code = """//+------------------------------------------------------------------+
//|                                            PythonDataBridge.mq4 |
//|                        Python Integration Bridge for MT4        |
//+------------------------------------------------------------------+
#property copyright "MQL-Python Converter"
#property version   "1.00"
#property strict

// Input parameters
input string PythonServerIP = "127.0.0.1";
input int    PythonServerPort = 9999;
input int    SendIntervalMs = 1000;

// Global variables
int socket = INVALID_HANDLE;
datetime lastSendTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("Python Data Bridge EA initialized");
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    if(socket != INVALID_HANDLE)
    {
        SocketClose(socket);
    }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check send interval
    if(TimeLocal() - lastSendTime < SendIntervalMs/1000)
        return;
    
    // Prepare data
    string data = StringFormat("{\\"symbol\\":\\"%s\\",\\"time\\":\\"%s\\",\\"bid\\":%f,\\"ask\\":%f,\\"spread\\":%d}",
                              Symbol(),
                              TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS),
                              Bid,
                              Ask,
                              (int)MarketInfo(Symbol(), MODE_SPREAD));
    
    // Send to Python
    if(SendDataToPython(data))
    {
        lastSendTime = TimeLocal();
    }
}

//+------------------------------------------------------------------+
//| Send data to Python server                                      |
//+------------------------------------------------------------------+
bool SendDataToPython(string data)
{
    // Create socket if needed
    if(socket == INVALID_HANDLE)
    {
        socket = SocketCreate();
        if(socket == INVALID_HANDLE)
        {
            Print("Failed to create socket");
            return false;
        }
    }
    
    // Connect to Python server
    if(!SocketConnect(socket, PythonServerIP, PythonServerPort, 1000))
    {
        Print("Failed to connect to Python server");
        SocketClose(socket);
        socket = INVALID_HANDLE;
        return false;
    }
    
    // Send data
    char req[];
    StringToCharArray(data, req);
    int sent = SocketSend(socket, req, ArraySize(req));
    
    if(sent <= 0)
    {
        Print("Failed to send data");
        SocketClose(socket);
        socket = INVALID_HANDLE;
        return false;
    }
    
    // Receive acknowledgment
    char resp[];
    int received = SocketRead(socket, resp, 2, 1000);
    
    // Close connection
    SocketClose(socket);
    socket = INVALID_HANDLE;
    
    return true;
}

//| Alternative: Save data to file for Python to read               |
//+------------------------------------------------------------------+
void SaveDataToFile()
{
    string filename = "python_bridge_data.csv";
    int handle = FileOpen(filename, FILE_WRITE|FILE_CSV);
    
    if(handle != INVALID_HANDLE)
    {
        FileWrite(handle, Symbol(), TimeCurrent(), Bid, Ask, 
                 MarketInfo(Symbol(), MODE_SPREAD),
                 AccountBalance(), AccountEquity());
        FileClose(handle);
    }
}
//+------------------------------------------------------------------+
"""
    
    return ea_code


def main():
    """Main function for testing MT4 integration"""
    print("MT4 Integration Module")
    print("=" * 50)
    
    # Initialize MT4 runner
    config = MT4Config()
    runner = MT4Runner(config)
    
    # Check Wine
    if runner.wine_initialized:
        print(f"✓ Wine is installed and configured")
    else:
        print("✗ Wine is not installed. Install with: sudo apt install wine")
        return
    
    # Check MT4 installation
    if runner.mt4_path:
        print(f"✓ MT4 found at: {runner.mt4_path}")
        
        # Check data folder
        data_folder = runner.get_data_folder()
        if data_folder:
            print(f"✓ MQL4 data folder: {data_folder}")
    else:
        print("✗ MT4 not installed in Wine")
        print("  To install MT4:")
        print("  1. Download MT4 installer from your broker")
        print("  2. Run: wine mt4setup.exe")
        print("  3. Or use: python mt4_integration.py --install")
    
    # Test data bridge
    print("\nData Bridge Status:")
    bridge = MT4DataBridge(config)
    
    def data_callback(data):
        print(f"Received data: {data}")
    
    # Start server (in production)
    # bridge.start_server(callback=data_callback)
    print(f"  Ready to start on port {config.data_bridge_port}")
    
    # Create EA code
    print("\nTo enable MT4-Python bridge:")
    print("1. Copy the generated EA to MT4/MQL4/Experts/")
    print("2. Compile and attach to a chart")
    print("3. Start the Python data bridge server")
    
    # Save EA code
    ea_code = create_mql4_bridge_ea()
    ea_file = Path("PythonDataBridge.mq4")
    with open(ea_file, 'w') as f:
        f.write(ea_code)
    print(f"\n✓ Bridge EA saved to: {ea_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MT4 Integration for MQL-Python Converter")
    parser.add_argument("--install", action="store_true", help="Install MT4")
    parser.add_argument("--run", action="store_true", help="Run MT4 terminal")
    parser.add_argument("--export", action="store_true", help="Export EA/Indicators")
    parser.add_argument("--bridge", action="store_true", help="Start data bridge server")
    
    args = parser.parse_args()
    
    if args.install:
        config = MT4Config()
        runner = MT4Runner(config)
        runner.install_mt4()
    elif args.run:
        config = MT4Config()
        runner = MT4Runner(config)
        process = runner.run_terminal()
        print("MT4 is running. Press Ctrl+C to stop.")
        try:
            process.wait()
        except KeyboardInterrupt:
            process.terminate()
    elif args.export:
        config = MT4Config()
        runner = MT4Runner(config)
        exporter = MT4FileExporter(runner)
        exporter.export_experts()
        exporter.export_indicators()
    elif args.bridge:
        config = MT4Config()
        bridge = MT4DataBridge(config)
        print(f"Starting data bridge on port {config.data_bridge_port}...")
        bridge.start_server(callback=lambda d: print(f"Data: {d}"))
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            bridge.stop_server()
            print("\nBridge stopped.")
    else:
        main()