try:
    import pandas as pd
    print("pandas version:", pd.__version__)
except ImportError:
    print("pandas is not installed")
