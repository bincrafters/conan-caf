#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
from conans.model.version import Version


class CAFConan(ConanFile):
    name = "caf"
    version = "0.16.1"
    description = "An open source implementation of the Actor Model in C++"
    url = "https://github.com/bincrafters/conan-caf"
    homepage = "https://github.com/actor-framework/actor-framework"
    topics = ("conan", "caf", "acto-framework", "actor-model", "pattern-matching", "actors")
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "BSD-3-Clause, BSL-1.0"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = ["cmake"]
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "log_level": ["ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "NONE"],
        "openssl": [True, False]
    }
    default_options = {"shared": False, "log_level": "NONE", "openssl": True}
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    @property
    def _is_static(self):
        return 'shared' in self.options.values.keys() and not self.options.shared

    @property
    def _has_openssl(self):
        return 'openssl' in self.options.values.keys() and self.options.openssl

    def config_options(self):
        if self.settings.os == "Windows" or self.settings.arch == "x86":
            del self.options.shared
            del self.options.openssl

    def source(self):
        tools.get("{}/archive/{}.tar.gz".format(self.homepage, self.version))
        os.rename("actor-framework-" + self.version, self._source_subfolder)

    def requirements(self):
        if self._has_openssl:
            self.requires("OpenSSL/1.0.2o@conan/stable")

    def configure(self):
        if self.settings.compiler == "gcc":
            if Version(self.settings.compiler.version.value) < "4.8":
                raise ConanInvalidConfiguration("g++ >= 4.8 is required, yours is %s" % self.settings.compiler.version)
        if self.settings.compiler == "clang" and Version(self.settings.compiler.version.value) < "3.4":
            raise ConanInvalidConfiguration("clang >= 3.4 is required, yours is %s" % self.settings.compiler.version)
        if self.settings.compiler == "Visual Studio" and Version(self.settings.compiler.version.value) < "14":
            raise ConanInvalidConfiguration("Visual Studio >= 14 is required, yours is %s" % self.settings.compiler.version)

    def _cmake_configure(self):
        cmake = CMake(self)
        cmake.parallel = True
        cmake.definitions["CMAKE_CXX_STANDARD"] = "11"
        cmake.definitions["CAF_NO_OPENSSL"] = not self._has_openssl
        for define in ["CAF_NO_EXAMPLES", "CAF_NO_TOOLS", "CAF_NO_UNIT_TESTS", "CAF_NO_PYTHON"]:
            cmake.definitions[define] = "ON"
        if tools.os_info.is_macos and self.settings.arch == "x86":
            cmake.definitions["CMAKE_OSX_ARCHITECTURES"] = "i386"
        cmake.definitions["CAF_BUILD_STATIC"] = self._is_static
        cmake.definitions["CAF_BUILD_STATIC_ONLY"] = self._is_static
        cmake.definitions["CAF_LOG_LEVEL"] = self.default_options['log_level'].index(self.options.log_level.value)
        cmake.configure(build_dir=self._build_subfolder)
        return cmake

    def build(self):
        cmake = self._cmake_configure()
        cmake.build()

    def package(self):
        self.copy("LICENSE*", dst="licenses", src=self._source_subfolder)
        cmake = self._cmake_configure()
        cmake.install()

    def package_info(self):
        suffix = "_static" if self._is_static else ""
        self.cpp_info.libs = ["caf_core%s" % suffix, "caf_io%s" % suffix]
        if self._has_openssl:
            self.cpp_info.libs.append("caf_openssl%s" % suffix)
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.cpp_info.libs.append('ws2_32')
            self.cpp_info.libs.append('iphlpapi')
        elif self.settings.os == "Linux":
            self.cpp_info.libs.append('pthread')
