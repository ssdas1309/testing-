import streamlit as st
import pandas as pd
import numpy as np
st.title("ISERVEU RECON PROCESS")
Mware = st.file_uploader('mware a file containing m/w data')
Npci = st.file_uploader('npci a file containing npci data')
Switch=st.file_uploader('switch a file containing switch data')
mware=pd.read_excel(Mware)
npci=pd.read_excel(Npci)
switch=pd.read_excel(Switch)
# import streamlit as st
# import pandas as pd
# import numpy as np
# mware = pd.read_excel(r'NSDL AEPS MIDDLEWARE FILE - 24-10-2022.xlsx')
# # print(mware)
# npci = pd.read_excel(r'NSDL AEPS NPCI FILE - 24-10-2022.xlsx')
# # print(npci)
# switch = pd.read_excel(r'NSDL AEPS SWITCH FILE - 24-10-2022.xlsx')
# print(switch)
#MIDDILE WARE
mware.rename(columns={'referenceNo':'Card No', 'apiTid':'RRN', 'transactionMode':'Transaction Type','status':'Transaction Status', 'amountTransacted':'Transaction Amount', 'createdDate':'Transaction Date Time'}, inplace = True)
npci.rename(columns={'PAN Number':'Card No', 'Transaction Serial Number': 'RRN', 'Transaction Type': 'Transaction Type', 'Response Code':'Transaction Status', 'Actual Transaction Amount':'Transaction Amount', 'Transaction Date':'Transaction Date Time' }, inplace = True)
df_final = pd.merge(pd.merge(npci, switch, on='RRN', how='outer', suffixes=("_npci","_switch")), mware, on='RRN', how='outer')
df_final.loc[df_final['Transaction Type_npci'] == 4, 'Transaction Type_npci'] = 'cash withdrawal'
df_final.loc[df_final['Transaction Type_npci'] == 7, 'Transaction Type_npci'] = 'mini statement'
df_final.loc[df_final['Transaction Type_npci'] == 5, 'Transaction Type_npci'] = 'balance enquiry'
df_final['transaction sector'] = ''
df_final['transaction sector'] = np.where(df_final['Transaction Type_npci'] == 'cash withdrawal', 'finance', 'non-finance')

mware = mware[['RRN', 'Transaction Type', 'Transaction Status', 'Transaction Amount', 'Transaction Date Time', 'Card No']]
mware.loc[mware['Transaction Type'] == 'AEPS_CASH_WITHDRAWAL', 'Transaction Type'] = 'cash withdrawal'
mware.loc[mware['Transaction Type'] == 'AEPS_MINI_STATEMENT', 'Transaction Type'] = 'mini statement'
mware.loc[mware['Transaction Type'] == 'AEPS_BALANCE_ENQUIRY', 'Transaction Type'] = 'balance enquiry'
# print("BEFORE MERGE MWARE DATA:",mware)
#NPCI
npci = npci[['RRN', 'Transaction Type', 'Transaction Status', 'Transaction Amount', 'Transaction Date Time', 'Card No']]
npci['Transaction Status'] = np.where(npci['Transaction Status'] == '00', 'SUCCESS', 'FAILED')
npci.loc[npci['Transaction Type'] == 4, 'Transaction Type'] = 'cash withdrawal'
npci.loc[npci['Transaction Type'] == 7, 'Transaction Type'] = 'mini statement'
npci.loc[npci['Transaction Type'] == 5, 'Transaction Type'] = 'balance enquiry'
# print("BEFORE MERGE NPCI DATA:",npci)
#SWITCH
switch = switch[['RRN', 'Transaction Type', 'Transaction Status', 'Transaction Amount', 'Transaction Date Time', 'Card No']]
switch.loc[switch['Transaction Type'] == 'Offus Withdrawal txn', 'Transaction Type'] = 'cash withdrawal'
switch.loc[switch['Transaction Type'] == 'Offus Mini Statement', 'Transaction Type'] = 'mini statement'
switch.loc[switch['Transaction Type'] == 'OFFUS Balance enquiry', 'Transaction Type'] = 'balance enquiry'
# print("BEFORE MERGE SWITCH",switch)
mware['Card No New'] = mware['Card No'].str[-4:]
switch['Card No New'] = switch['Card No'].str[-4:]
npci['Card No New'] = npci['Card No'].str[-4:]
mware['Transaction Amount'] = mware['Transaction Amount'].apply(lambda x: str(x))
switch['Transaction Amount'] = switch['Transaction Amount'].apply(lambda x: str(x))
npci['Transaction Amount'] = npci['Transaction Amount'].apply(lambda x: str(x))

#MERGE
df_merge = pd.merge(pd.merge(npci, switch, on='RRN', how='outer', suffixes=("_npci","_switch")), mware, on='RRN', how='outer')
#list of column matches
column_match1 = ['Transaction Status', 'Transaction Amount','Transaction Type', 'Card No New']
#match of three excel sheet of this column
for key in column_match1:
    df_merge['{}_final_status'.format(key)] = df_merge[['{}_switch'.format(key), '{}_npci'.format(key)]].eq(df_merge['{}'.format(key)], axis=0).all(axis=1)
    df_merge['{}_final_status'.format(key)] = np.where(df_merge['{}_final_status'.format(key)] == 0, '{} '.format(key), '')
    
print("2 column merge report 3excel sheet::",df_merge)
# column_match2 = ['Transaction Type']
# #list of column matches in 2 excel sheet
# for key in column_match2:
#     df_merge['{}_final_status'.format(key)] = np.where((df_merge['{}_switch'.format(key)] == df_merge['{}_npci'.format(key)]),'{} '.format(key), '' )
#match1 AND match2 concatenate
# column_match = column_match1 + column_match2
#this will print the why column not matched
df_merge['final_status_description'] = ''
for key in column_match1:
    df_merge['final_status_description'] += df_merge['{}_final_status'.format(key)]

df_merge['final_status'] = ''
#this list for the match or mismatch
df_merge['final_status'] = np.where(df_merge['final_status_description'] == '', 'Match', 'Mismatch')

for key in column_match1:
    del df_merge['{}_final_status'.format(key)]
print("MATCH COUNT:", df_merge['final_status'].value_counts())
print("final status:::",df_merge['final_status'])
print("merge columns:",df_merge.columns)
df_final.index = df_merge.index
df_final['final_status_description'] = ''

df_final['final_status'] = ''

df_final['final_status_description'] = df_merge['final_status_description']
df_final['final_status'] = df_merge['final_status']
df_merge['transaction sector'] = df_final['transaction sector']

df_merge.to_csv('merge data.csv')
df_final.to_csv('all.csv')
st.write(df_merge)
st.write(df_final)


