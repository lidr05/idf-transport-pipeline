import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

df_verif = pd.read_sql("SELECT * FROM prochains_departs", engine)
print(df_verif)