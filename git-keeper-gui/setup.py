# setup.py for git-keeper-core

from setuptools import setup

setup(
    name='git-keeper-gui',
    version='0.1.0',
    description='Graphical interface for git-keeper',
    url='https://github.com/git-keeper/git-keeper',
    license='GPL 3',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Education',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Natural Language :: English',
        'Topic :: Education :: Testing',
        'Topic :: Education'
    ],
    packages=['gkeepgui'],
    entry_points={
        'console_scripts': ['gkeepgui=gkeepgui.gui_main_entry:main'],
    },
    install_requires=['git-keeper-client'],

    # setup_requires=['pytest-runner'],
    # tests_require=['pytest'],
)
