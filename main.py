from parse_site import start_parse

tsv_filename = 'allrecipes_everyday_cooking.tsv'
arff_filename = 'allrecipes_everyday_cooking.arff'
output_csv = 'allrecipes_binarized_everyday_cooking.csv'
filter_keyword = '/everyday-cooking/'

start_parse(tsv_filename, arff_filename, output_csv, filter_keyword)