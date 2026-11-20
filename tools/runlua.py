"""Run a Lua script inside Path of Building's own LuaJIT (runtime/lua51.dll), without the GUI.

Windows only, 64-bit Python. No LuaJIT / busted / Docker installation needed.

    python tools/runlua.py <script.lua> [args...]

The script runs with the working directory set to src/ (like the busted test setup), so it can
start with dofile("HeadlessWrapper.lua"). Arguments are available as the global SCRIPT_ARGS.
"""
import ctypes
import os
import sys
import zlib

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


# Inflate() is a stub in the headless wrapper (returns ""), so data PoB ships compressed - the timeless jewel look-up
# tables - came out empty and those jewels did nothing. PoB's loader prefers an up-to-date uncompressed .bin next to
# the archive, so expand the archives here with zlib and let the loader's NewFileSearch see the .bin files.
def expand_timeless_data(folder):
    mtimes = {}
    if not os.path.isdir(folder):
        return mtimes
    names = sorted({f.split(".zip")[0] for f in os.listdir(folder) if ".zip" in f})
    for name in names:
        single = os.path.join(folder, name + ".zip")
        parts = [single] if os.path.exists(single) else []
        i = 0
        while not os.path.exists(single) and os.path.exists(os.path.join(folder, f"{name}.zip.part{i}")):
            parts.append(os.path.join(folder, f"{name}.zip.part{i}"))
            i += 1
        if not parts:
            continue
        newest = max(os.path.getmtime(p) for p in parts)
        binary = os.path.join(folder, name + ".bin")
        if not os.path.exists(binary) or os.path.getsize(binary) == 0 or os.path.getmtime(binary) <= newest:
            data = b"".join(open(p, "rb").read() for p in parts)
            try:
                out = zlib.decompress(data, 47)  # zlib or gzip header, detected
            except zlib.error as e:
                print(f"runlua: cannot expand {name}: {e}", file=sys.stderr)
                continue
            with open(binary, "wb") as f:
                f.write(out)
        mtimes[name + ".bin"] = int(os.path.getmtime(binary))
        mtimes[name + ".zip"] = int(newest)
    return mtimes


def lua_string(value):
    return "[==[" + value + "]==]"


os.chdir(os.path.join(root, "src"))
L = lua.luaL_newstate()
lua.luaL_openlibs(L)
timeless = expand_timeless_data(os.path.join(root, "src", "Data", "TimelessJewelData"))
boot = "\n".join([
    # _SimpleGraphic.def.lua (loaded by HeadlessWrapper) defines the stubs: right after it, let NewFileSearch
    # report the timeless jewel files so the loader reads the expanded .bin
    "local timeless = { " + ", ".join(f"[ {lua_string(k)} ] = {v}" for k, v in timeless.items()) + " }",
    "local l_dofile = dofile",
    "function dofile(path, ...) local r = { l_dofile(path, ...) } "
    "if tostring(path):find('_SimpleGraphic.def.lua', 1, true) then local stub = NewFileSearch "
    "NewFileSearch = function(spec, ...) local name = tostring(spec):match('TimelessJewelData/([^/]+)$') "
    "if name then name = name:gsub('%.part%*$', '') local t = timeless[name] "
    "if t then return { GetFileName = function() return name end, GetFileModifiedTime = function() return t end } end return nil end "
    "return stub(spec, ...) end end return unpack(r) end",
    "package.path = '../runtime/lua/?.lua;../runtime/lua/?/init.lua;' .. package.path",
    "package.cpath = " + lua_string(runtime.replace("\\", "/") + "/?.dll;") + " .. package.cpath",
    "SCRIPT_DIR = " + lua_string(os.path.dirname(script).replace("\\", "/")),
    "SCRIPT_ARGS = { " + ", ".join(lua_string(a.replace("\\", "/")) for a in args) + " }",
    "arg = { }",
    "io.stdout:setvbuf('no')",
    "dofile(" + lua_string(script.replace("\\", "/")) + ")",
])
if lua.luaL_loadstring(L, boot.encode("utf-8")) != 0 or lua.lua_pcall(L, 0, 0, 0) != 0:
    print("LUA ERROR:", lua.lua_tolstring(L, -1, None).decode(errors="replace"))
    sys.exit(1)
