#include <iostream>
#include <string>
#include <windows.h>
using namespace std;

void run(string);

int main() {
    char buf[256];
    GetCurrentDirectoryA(256, buf);
    string cwd = string(buf);
    
    run("start steam://rungameid/440");
    run("\"" + cwd + "\\resources\\python\\python.exe\" -OO \"" + cwd + "\\resources\\welcomer.py\" --v 1");
    run("\"" + cwd + "\\resources\\python\\python.exe\" -OO \"" + cwd + "\\resources\\launcher.py\" --m detect_system_language");
    run("\"" + cwd + "\\resources\\python\\python.exe\" -OO \"" + cwd + "\\resources\\launcher.py\" --m updater");
    
    while (true) {
        run("\"" + cwd + "\\resources\\python\\python.exe\" -OO \"" + cwd + "\\resources\\launcher.py\" --m main");
    }
    
    return 0;
}

void run(string cmd) {
    string full_cmd = "\"" + cmd + "\"";
    system(full_cmd.c_str());
}
