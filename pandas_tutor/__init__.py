# in Jupyter, load the %%pandas_tutor magic.
# users have to initialize the magic first using %load_ext pandas_tutor.
def load_ipython_extension(ipython):
    from importlib import reload
    import pandas_tutor.ipython_magics

    reload(pandas_tutor.ipython_magics)
    ipython.register_magics(pandas_tutor.ipython_magics.PandasTutorMagics)
