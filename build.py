#!/usr/bin/env python
# -*- coding: utf-8 -*-

import platform
import os
from bincrafters import build_template_default


def get_shared_option_name():
    return False if platform.system() == 'Windows' or \
                    os.getenv("CONAN_ARCHS") == "x86" else "caf:shared"

if __name__ == "__main__":
    builder = build_template_default.get_builder(pure_c=False,
                                                 shared_option_name=get_shared_option_name())
    builder.run()
