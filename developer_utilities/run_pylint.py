#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

if __name__ == "__main__":
    from pylint import epylint as lint

    lint.lint(filename="autozlap",
              options=["--disable=logging-format-interpolation",
                       "--disable=fixme",
                       "--disable=locally-disabled",
                       "--ignore=_external"])
