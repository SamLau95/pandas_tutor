1. clone repo, cd into it
2. mamba create --name pandas_tutor python=3.9
3. mamba activate pandas_tutor
4. pip install -r requirements-dev.txt
5. make test
   1. Sara ran into a failing test: test_memory_cap_data, possibly because
      memory usage on Windows is different than macOS.
   2. also, lots of warnings from numpy, probbaly have to downgrade and pin
      numpy version
6. bin/main pandas_tutor/tests/e2e_golden/head_01.py
   1. This errored out because windows can't run scripts...so we started all
      over using WSL.
7. after doing everything in WSL, things work perfectly!

hello world
