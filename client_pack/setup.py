from setuptools import setup, find_packages

setup(  
        name="client_pack_2try_version",
        version="0.8.7",
        description="mess_client",
        author="Sergey Kuchko",
        author_email="kuchko.02@gmail.com",
        packages=find_packages(),
        install_requires=['PyQt6', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
    )