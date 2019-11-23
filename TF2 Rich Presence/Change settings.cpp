#include <iostream>
#include <string>
#include <windows.h>
using namespace std;

void run(string);

int main() {
    char buf[256];
    GetCurrentDirectoryA(256, buf);
    string cwd = string(buf);
    
    run("start \"\" \"" + cwd + "\\resources\\python\\pythonw.exe\" -OO \"" + cwd + "\\resources\\launcher.py\" --m settings");
    
    return 0;
}

void run(string cmd) {
    string full_cmd = "\"" + cmd + "\"";
    system(full_cmd.c_str());
}
