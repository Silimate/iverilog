/*
 *    Copyright (C) 2026 Silimate Inc.
 *
 *    This source code is free software; you can redistribute it
 *    and/or modify it in source code form under the terms of the GNU
 *    General Public License as published by the Free Software
 *    Foundation; either version 2 of the License, or (at your option)
 *    any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *    You should have received a copy of the GNU General Public License
 *    along with this program; if not, write to the Free Software
 *    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */
// SILIMATE: This file can find the appropriate prefix for a relocated driver,
//           which is needed for wheels.
//
//           C++17 with std::filesystem required.
#include <filesystem>
#include <unistd.h>
#include <cstdio>
#include <cstring>

#ifdef __APPLE__
#include <mach-o/dyld.h>
#endif

namespace fs = std::filesystem;

extern "C" void print_runtime_paths_portable(const char *ivl_root) {
    auto prefix = fs::canonical(fs::path(ivl_root)).parent_path().parent_path();
    auto include_dir = prefix / "include";
    if (fs::exists(include_dir)) {
        printf("includedir: %s\n", include_dir.c_str());
    } else {
        printf("includedir: %s\n", IVL_INCLUDE_INSTALL_DIR);
    }

    // SILIMATE: unlike upstream function, we also print the libdir
    auto lib_dir = prefix / "lib";
    if (fs::exists(lib_dir)) {
        printf("libdir: %s\n", lib_dir.c_str());
    } else {
        printf("libdir: %s\n", IVL_LIB);
    }
    
}
