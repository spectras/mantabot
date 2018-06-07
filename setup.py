from setuptools import setup, find_packages, Extension
import os.path

root = os.path.dirname(__file__)

native = Extension(
    name='mantabot.util.native',
    sources=['mantabot/util/native.c'],
)

setup(
    name='mantabot',
    version='0.1',
    description='Asynchronous Discord bot engine',
    author='Julien Hartmann',
    author_email='juli1.hartmann@gmail.com',
    packages=find_packages(),
    scripts=['mantabot.py'],
    ext_modules=[native],
    include_package_data=True,
    zip_safe=False,
)
