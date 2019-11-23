REM This will probably not work for you

"C:\Program Files (x86)\Dev-Cpp\MinGW64\bin\g++.exe" "Launch TF2 with Rich Presence.cpp" -o "Launch TF2 with Rich Presence.exe" -lstdc++ -Bdynamic -Os -m32 -s -std=c++11 -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\x86_64-w64-mingw32\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\lib\gcc\x86_64-w64-mingw32\4.9.2\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\lib\gcc\x86_64-w64-mingw32\4.9.2\include\c++" -L"C:\Program Files (x86)\Dev-Cpp\MinGW64\x86_64-w64-mingw32\lib32" -static-libgcc -m32

"C:\Program Files (x86)\Dev-Cpp\MinGW64\bin\g++.exe" "Launch Rich Presence alongside TF2.cpp" -o "Launch Rich Presence alongside TF2.exe" -lstdc++ -Bdynamic -Os -m32 -s -std=c++11 -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\x86_64-w64-mingw32\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\lib\gcc\x86_64-w64-mingw32\4.9.2\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\lib\gcc\x86_64-w64-mingw32\4.9.2\include\c++" -L"C:\Program Files (x86)\Dev-Cpp\MinGW64\x86_64-w64-mingw32\lib32" -static-libgcc -m32

"C:\Program Files (x86)\Dev-Cpp\MinGW64\bin\g++.exe" "Change settings.cpp" -o "Change settings.exe" -lstdc++ -Bdynamic -Os -m32 -mwindows -s -std=c++11 -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\x86_64-w64-mingw32\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\lib\gcc\x86_64-w64-mingw32\4.9.2\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\lib\gcc\x86_64-w64-mingw32\4.9.2\include\c++" -L"C:\Program Files (x86)\Dev-Cpp\MinGW64\x86_64-w64-mingw32\lib32" -static-libgcc -m32 -mwindows

build_tools\rcedit-x86.exe "Launch TF2 with Rich Presence.exe" --set-icon tf2_logo_blurple.ico
build_tools\rcedit-x86.exe "Launch Rich Presence alongside TF2.exe" --set-icon tf2_logo_blurple.ico
build_tools\rcedit-x86.exe "Change settings.exe" --set-icon tf2_logo_blurple_wrench.ico
pause