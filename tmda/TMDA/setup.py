from distutils.core import setup, Extension

module1 = Extension("CheckPassword", sources = ["CheckPassword.c"])

setup (name = "PackageName", version = "1.0",
       description = "Module for calling checkpassword.", ext_modules = [module1])
