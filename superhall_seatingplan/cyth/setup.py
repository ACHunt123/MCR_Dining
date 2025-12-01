from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        "sa_core",
        sources=["sa_core.pyx"],
        include_dirs=[np.get_include()],
        extra_compile_args=["-O3"],
    )
]

setup(
    name="sa_core",
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": 3},
        annotate=True  # optional, for HTML annotation
    ),
)
