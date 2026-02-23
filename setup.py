from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\\n")

# get version from __version__ variable in addsol_vendor_onboarding/__init__.py
from addsol_vendor_onboarding import __version__ as version

setup(
    name="addsol_vendor_onboarding",
    version=version,
    description="Custom vendor onboarding with automated validation via Cashfree APIs",
    author="Addition Solutions",
    author_email="conatct@aitspl.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)