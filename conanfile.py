import os
from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
from conans.tools import Version


class CAFConan(ConanFile):
    name = "caf"
    version = "0.17.6"
    description = "An open source implementation of the Actor Model in C++"
    url = "https://github.com/bincrafters/conan-caf"
    homepage = "https://github.com/actor-framework/actor-framework"
    topics = ("conan", "caf", "actor-framework", "actor-model", "pattern-matching", "actors")
    license = ("BSD-3-Clause, BSL-1.0")
    exports_sources = ["CMakeLists.txt", "caf.patch"]
    generators = ["cmake"]
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "log_level": ["ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "NONE"],
        "openssl": [True, False]
    }
    default_options = {"shared": False, "fPIC": True, "log_level": "NONE", "openssl": True}
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    _cmake = None

    @property
    def _is_static(self):
        return 'shared' not in self.options.values.keys() or not self.options.shared

    @property
    def _has_openssl(self):
        return 'openssl' in self.options.values.keys() and self.options.openssl

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
            del self.options.shared
            if self.settings.arch == "x86":
                del self.options.openssl

    def source(self):
        sha256 = "e2bf5bd243f08bb7d8adde197cfe3e6d71314ed3378fe0692f8932f4c3b3928c"
        tools.get("{}/archive/{}.tar.gz".format(self.homepage, self.version), sha256=sha256)
        os.rename("actor-framework-" + self.version, self._source_subfolder)

    def requirements(self):
        if self._has_openssl:
            self.requires("openssl/1.0.2u")

    def configure(self):
        if self.settings.compiler == "gcc":
            if Version(self.settings.compiler.version.value) < "4.8":
                raise ConanInvalidConfiguration("g++ >= 4.8 is required, yours is %s" % self.settings.compiler.version)
        elif self.settings.compiler == "clang" and Version(self.settings.compiler.version.value) < "4.0":
            raise ConanInvalidConfiguration("clang >= 4.0 is required, yours is %s" % self.settings.compiler.version)
        elif self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version.value) < "9.0":
            raise ConanInvalidConfiguration("clang >= 9.0 is required, yours is %s" % self.settings.compiler.version)
        elif self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version.value) > "10.0" and \
                self.settings.arch == 'x86':
            raise ConanInvalidConfiguration("clang >= 11.0 does not support x86")
        elif self.settings.compiler == "Visual Studio" and Version(self.settings.compiler.version.value) < "15":
            raise ConanInvalidConfiguration("Visual Studio >= 15 is required, yours is %s" % self.settings.compiler.version)

    def _cmake_configure(self):
        if not self._cmake:
            self._cmake = CMake(self)
            self._cmake.definitions["CMAKE_CXX_STANDARD"] = "11"
            self._cmake.definitions["CAF_NO_AUTO_LIBCPP"] = True
            self._cmake.definitions["CAF_NO_OPENSSL"] = not self._has_openssl
            for define in ["CAF_NO_EXAMPLES", "CAF_NO_TOOLS", "CAF_NO_UNIT_TESTS", "CAF_NO_PYTHON"]:
                self._cmake.definitions[define] = "ON"
            if tools.os_info.is_macos and self.settings.arch == "x86":
                self._cmake.definitions["CMAKE_OSX_ARCHITECTURES"] = "i386"
            self._cmake.definitions["CAF_BUILD_STATIC"] = self._is_static
            self._cmake.definitions["CAF_BUILD_STATIC_ONLY"] = self._is_static
            if self.options.log_level != "NONE":
                self._cmake.definitions["CAF_LOG_LEVEL"] = self.options.log_level
            if self.settings.os == 'Windows':
                self._cmake.definitions["OPENSSL_USE_STATIC_LIBS"] = True
                self._cmake.definitions["OPENSSL_MSVC_STATIC_RT"] = True
            elif self.settings.compiler == 'clang':
                self._cmake.definitions["PTHREAD_LIBRARIES"] = "-pthread -ldl"
            else:
                self._cmake.definitions["PTHREAD_LIBRARIES"] = "-pthread"
                if self.settings.compiler == "gcc" and Version(self.settings.compiler.version.value) < "5.0":
                    self._cmake.definitions["CMAKE_SHARED_LINKER_FLAGS"] = "-pthread"
            self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def build(self):
        if self.settings.os == "Windows":  # Needed for MSVC and Mingw
            tools.patch(base_path=self._source_subfolder, patch_file="caf.patch")
        cmake = self._cmake_configure()
        cmake.build()

    def package(self):
        self.copy("LICENSE*", dst="licenses", src=self._source_subfolder)
        cmake = self._cmake_configure()
        cmake.install()

    def package_info(self):
        suffix = "_static" if self._is_static else ""
        self.cpp_info.libs = ["caf_io%s" % suffix, "caf_core%s" % suffix]
        if self._has_openssl:
            self.cpp_info.libs.append("caf_openssl%s" % suffix)
        if self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["ws2_32", "iphlpapi", "psapi"])
        elif self.settings.os == "Linux":
            self.cpp_info.system_libs.extend(['-pthread', 'm'])
