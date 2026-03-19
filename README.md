simple wget tool 

Usage
1. Run the Python Script Directly
Execute the full-featured Stage 9 script with your target download URL and parameters:
# Basic resumable download with optimized 64KB buffer
python stage9.py https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.tar.xz --resume -o linux-6.6.tar.xz --buf-size 65536

# Full example with authentication and custom headers
python stage9.py http://httpbin.org/basic-auth/testuser/testpass --resume -o auth_download.bin --user testuser --password testpass --header "User-Agent: MyWgetTool/1.0" --timeout 20

2. Build the Binary Executable
Generate the standalone .exe file using the provided setup.py configuration:
# Navigate to the script directory
cd D:\python learn

# Build the executable
python setup.py build

3. Run the Executable (Windows Only)
The compiled executable will be located in the build/exe.win-amd64-3.9 directory (version number may vary):

# Navigate to the executable directory
cd build/exe.win-amd64-3.9

# Run the executable (same parameters as the Python script)
my_wget.exe https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.tar.xz --resume -o linux-6.6.tar.xz --buf-size 65536
