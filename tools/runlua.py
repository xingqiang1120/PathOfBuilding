"""Run a Lua script inside Path of Building's own LuaJIT (runtime/lua51.dll), without the GUI.

Windows only, 64-bit Python. No LuaJIT / busted / Docker installation needed.

    python tools/runlua.py <script.lua> [args...]

The script runs with the working directory set to src/ (like the busted test setup), so it can
start with dofile("HeadlessWrapper.lua"). Arguments are available as the global SCRIPT_ARGS.
"""
import ctypes
import os
import sys

if len(sys.argv) < 2:
    sys.exit(__doc__)

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
script = os.path.abspath(sys.argv[1])
args = [os.path.abspath(a) if os.path.exists(a) else a for a in sys.argv[2:]]
runtime = os.path.join(root, "runtime")
os.add_dll_directory(runtime)
os.environ["PATH"] = runtime + os.pathsep + os.environ["PATH"]

lua = ctypes.CDLL(os.path.join(runtime, "lua51.dll"))
lua.luaL_newstate.restype = ctypes.c_void_p
lua.luaL_openlibs.argtypes = [ctypes.c_void_p]
lua.luaL_loadstring.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
lua.lua_pcall.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
lua.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
lua.lua_tolstring.restype = ctypes.c_char_p


def lua_string(value):
    return "[==[" + value + "]==]"


os.chdir(os.path.join(root, "src"))
L = lua.luaL_newstate()
lua.luaL_openlibs(L)
boot = "\n".join([
    "package.path = '../runtime/lua/?.lua;../runtime/lua/?/init.lua;' .. package.path",
    "package.cpath = " + lua_string(runtime.replace("\\", "/") + "/?.dll;") + " .. package.cpath",
    "SCRIPT_ARGS = { " + ", ".join(lua_string(a.replace("\\", "/")) for a in args) + " }",
    "arg = { }",
    "io.stdout:setvbuf('no')",
    "dofile(" + lua_string(script.replace("\\", "/")) + ")",
])
if lua.luaL_loadstring(L, boot.encode("utf-8")) != 0 or lua.lua_pcall(L, 0, 0, 0) != 0:
    print("LUA ERROR:", lua.lua_tolstring(L, -1, None).decode(errors="replace"))
    sys.exit(1)
