import os
import pandas as pd

def read_tsv(tsv_filename):
    return pd.read_csv(tsv_filename, sep='\t')

def escape_quotes(s):
    if isinstance(s, str):
        return s.replace('"', '\\"')
    return s

def write_arff(df, arff_filename):
    if os.path.exists(arff_filename):
        print(f"ARFF файл '{arff_filename}' уже существует.")
        return

    with open(arff_filename, 'w') as f:
        f.write('@relation allrecipes_recipes\n\n')

        f.write('@attribute URL string\n')
        f.write('@attribute Title string\n')
        f.write('@attribute Category string\n')
        f.write('@attribute Rating numeric\n')
        f.write('@attribute "Prep_Time_(min)" numeric\n')
        f.write('@attribute "Cook_Time_(min)" numeric\n')
        f.write('@attribute "Total_Time_(min)" numeric\n')
        f.write('@attribute Servings numeric\n')
        f.write('@attribute Ingredients string\n')
        f.write('@attribute "Image_Paths" string\n\n')

        f.write('@data\n')
        for index, row in df.iterrows():
            f.write(f'"{escape_quotes(row["URL"])}", "{escape_quotes(row["Title"])}", '
                    f'"{escape_quotes(row["Category"])}", '
                    f'{row["Rating"] if pd.notnull(row["Rating"]) else "?"}, '
                    f'{row["Prep_Time_(min)"] if pd.notnull(row["Prep_Time_(min)"]) else "?"}, '
                    f'{row["Cook_Time_(min)"] if pd.notnull(row["Cook_Time_(min)"]) else "?"}, '
                    f'{row["Total_Time_(min)"] if pd.notnull(row["Total_Time_(min)"]) else "?"}, '
                    f'{row["Servings"] if pd.notnull(row["Servings"]) else "?"}, '
                    f'"{escape_quotes(row["Ingredients"])}", "{escape_quotes(row["Image_Paths"])}"\n')

    print(f"ARFF файл '{arff_filename}' успешно создан.")
